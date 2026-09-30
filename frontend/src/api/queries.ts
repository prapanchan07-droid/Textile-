import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getData, http, postForm } from './client';
import { toComparison, toOverviewPeriod, type Period } from '../lib/period';
import type { HealthResponseData } from '../types/api';
import type { FactoryOverviewData } from '../types/overview';
import type { ProductionModuleData } from '../types/production';
import type { MachinesModuleData } from '../types/machines';
import type { MachineComparisonResponse } from '../types/machineComparison';
import type { ManpowerQualityModuleData } from '../types/manpowerQuality';
import type { RevenueLossModuleData } from '../types/revenueLoss';
import type { DecisionCenterData } from '../types/decisionCenter';

/**
 * Every server read goes through a hook here. React Query gives caching across
 * page switches, background refresh, and one place to invalidate after an import.
 * The backend "unit" and "role" parameters are intentionally not sent: roles must
 * come from an authenticated session, not from a value the browser chooses.
 */

export const qk = {
  all: ['api'] as const,
  health: ['api', 'health'] as const,
  overview: (p: Period) => ['api', 'overview', p] as const,
  decision: (p: Period) => ['api', 'decision', p] as const,
  production: (date?: string) => ['api', 'production', date ?? 'latest'] as const,
  machines: (p: Period, type: string, id: string) => ['api', 'machines', p, type, id] as const,
  comparison: (args: ComparisonArgs) => ['api', 'comparison', args] as const,
  manpowerQuality: (p: Period) => ['api', 'manpower-quality', p] as const,
  revenue: (p: Period) => ['api', 'revenue', p] as const,
  history: ['api', 'ingestion', 'history'] as const,
};

export const useHealth = () =>
  useQuery({
    queryKey: qk.health,
    queryFn: () => getData<HealthResponseData>('/health'),
    refetchInterval: 60_000,
    retry: false,
  });

export const useOverview = (period: Period) =>
  useQuery({
    queryKey: qk.overview(period),
    queryFn: () =>
      getData<FactoryOverviewData>('/overview', {
        period: toOverviewPeriod(period),
        comparison: toComparison(period),
      }),
    placeholderData: keepPreviousData,
  });

export const useDecisionCenter = (period: Period) =>
  useQuery({
    queryKey: qk.decision(period),
    queryFn: () =>
      getData<DecisionCenterData>('/decision-center', {
        period: toOverviewPeriod(period),
        comparison: toComparison(period),
      }),
    placeholderData: keepPreviousData,
  });

/** /production ignores `period`; it reports one report date (latest when omitted). */
export const useProduction = (date?: string) =>
  useQuery({
    queryKey: qk.production(date),
    queryFn: () =>
      getData<ProductionModuleData & { is_reconciled?: boolean; data_quality_warning?: string | null }>(
        '/production',
        date ? { date } : undefined,
      ),
    placeholderData: keepPreviousData,
  });

export const useMachines = (period: Period, machineType = 'ALL', machineId = 'ALL') =>
  useQuery({
    queryKey: qk.machines(period, machineType, machineId),
    queryFn: () => getData<MachinesModuleData>('/machines', { period, machine_type: machineType, machine_id: machineId }),
    placeholderData: keepPreviousData,
  });

export interface ComparisonArgs {
  machines: string[];
  metric: string;
  period: Period;
  machineType: string;
  reference: string;
}

export const useMachineComparison = (args: ComparisonArgs) =>
  useQuery({
    queryKey: qk.comparison(args),
    queryFn: () =>
      getData<MachineComparisonResponse>('/machine-comparison', {
        machines: args.machines.length ? args.machines : undefined,
        metric: args.metric,
        period: args.period,
        machine_type: args.machineType,
        reference: args.reference,
      }),
    placeholderData: keepPreviousData,
  });

export const useManpowerQuality = (period: Period) =>
  useQuery({
    queryKey: qk.manpowerQuality(period),
    queryFn: () => getData<ManpowerQualityModuleData>('/manpower-quality', { period }),
    placeholderData: keepPreviousData,
  });

export const useRevenue = (period: Period) =>
  useQuery({
    queryKey: qk.revenue(period),
    queryFn: () => getData<RevenueLossModuleData>('/revenue-loss', { period }),
    placeholderData: keepPreviousData,
  });

// ---------- Data imports ----------

export interface ImportHistoryItem {
  id: string;
  filename: string;
  report_type: string;
  confidence_score: number;
  status: string;
  report_date?: string;
  upload_timestamp: string;
}

export interface ImportFileStatus {
  filename: string;
  status: 'PROCESSING' | 'SUCCESS' | 'DUPLICATE' | 'FAILED';
  message: string;
  report_type?: string;
  report_date?: string;
}

export interface ImportJob {
  job_id: string;
  status: 'PROCESSING' | 'COMPLETED' | 'FAILED';
  total_files: number;
  processed_count: number;
  success_count: number;
  failed_count: number;
  duplicate_count: number;
  progress_pct: number;
  created_at: string;
  file_statuses: ImportFileStatus[];
}

export const useImportHistory = () => useQuery({ queryKey: qk.history, queryFn: () => getData<ImportHistoryItem[]>('/ingestion/history') });

export const useImportJob = (jobId: string | null) => {
  const qc = useQueryClient();
  return useQuery({
    queryKey: ['api', 'ingestion', 'job', jobId],
    enabled: !!jobId,
    queryFn: async () => {
      const job = await getData<ImportJob>(`/ingestion/job/${jobId}`);
      if (job.status !== 'PROCESSING') {
        // New data landed: every dashboard is stale now.
        qc.invalidateQueries({ queryKey: qk.all });
      }
      return job;
    },
    refetchInterval: (q) => (q.state.data && q.state.data.status !== 'PROCESSING' ? false : 1000),
  });
};

export interface StartImportArgs {
  files: File[];
  reportType?: string;
  reportDate?: string;
  forceReplace?: boolean;
}

export const useStartImport = () =>
  useMutation({
    mutationFn: ({ files, reportType, reportDate, forceReplace }: StartImportArgs) => {
      const form = new FormData();
      files.forEach((f) => form.append('files', f));
      if (reportType) form.append('report_type_override', reportType);
      if (reportDate) form.append('date_override', reportDate);
      if (forceReplace) form.append('force_replace', 'true');
      return postForm<{ job_id: string; total_files: number }>('/ingestion/upload-job', form);
    },
  });

export async function downloadTemplate(sample: boolean) {
  const res = await http.get('/ingestion/template', { params: { sample }, responseType: 'blob' });
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = sample ? 'factory_data_sample.xlsx' : 'factory_data_template.xlsx';
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}
