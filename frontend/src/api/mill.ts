import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { deleteJson, getData, patchJson, postForm, postJson, putJson } from './client';
import type {
  Alert, AlertRule, Connection, Dashboard, Group, ImportBatch, ImportIssue, LoomDetail, LoomGrid, Meta, MetricDef, Notification, OwnerReport, Page,
  Person, Task, WorkOrder,
} from '../types/mill';

/** Query keys start with 'mill' so one invalidation refreshes every weaving view after an import or change. */
export const mk = {
  all: ['mill'] as const,
  meta: ['mill', 'meta'] as const,
  view: (name: string, params?: unknown) => ['mill', name, params] as const,
};

export type FilterQuery = Record<string, string | number | undefined>;

const useView = <T,>(name: string, url: string, params?: FilterQuery, opts: { enabled?: boolean; refetchInterval?: number } = {}) =>
  useQuery({ queryKey: mk.view(name, params), queryFn: () => getData<T>(url, params), placeholderData: keepPreviousData, ...opts });

export const useMeta = () => useQuery({ queryKey: mk.meta, queryFn: () => getData<Meta>('/mill/meta'), staleTime: 30_000 });
export const useDashboard = (p: FilterQuery) => useView<Dashboard>('dashboard', '/mill/dashboard', p);
export const useLoomGrid = (p: FilterQuery) => useView<LoomGrid>('looms', '/mill/looms', p, { refetchInterval: 30_000 });
export const useLoom = (id: number, p: FilterQuery) => useView<LoomDetail>(`loom-${id}`, `/mill/looms/${id}`, p);
export const useProduction = (p: FilterQuery) => useView<any>('production', '/mill/production', p);
export const useCompare = (p: FilterQuery) => useView<any>('compare', '/mill/compare', p);
export const useFindings = (p: FilterQuery) => useView<{ findings: Dashboard['findings'] }>('findings', '/mill/findings', p);
export const useEnergy = (p: FilterQuery) => useView<any>('energy', '/mill/energy', p);
export const useDefinitions = () => useQuery({ queryKey: mk.view('definitions'), queryFn: () => getData<MetricDef[]>('/mill/definitions'), staleTime: Infinity });

export const useImports = (page = 1) => useView<Page<ImportBatch>>('imports', '/mill/imports', { page, page_size: 25 }, { refetchInterval: 5000 });
export const useImport = (id: number | null) =>
  useQuery({ enabled: id != null, queryKey: mk.view('import', id), queryFn: () => getData<ImportBatch>(`/mill/imports/${id}`),
             refetchInterval: (q) => (q.state.data?.status === 'PROCESSING' ? 1500 : false) });
export const useImportIssues = (id: number | null, severity: string, page: number) =>
  useQuery({ enabled: id != null, queryKey: mk.view('import-issues', [id, severity, page]),
             queryFn: () => getData<Page<ImportIssue>>(`/mill/imports/${id}/issues`, { severity: severity || undefined, page, page_size: 50 }),
             placeholderData: keepPreviousData });

export const useAlerts = (p: FilterQuery) => useView<Page<Alert>>('alerts', '/mill/alerts', p, { refetchInterval: 30_000 });
export const useAlert = (id: number | null) =>
  useQuery({ enabled: id != null, queryKey: mk.view('alert', id), queryFn: () => getData<Alert>(`/mill/alerts/${id}`) });
export const useRules = () => useView<AlertRule[]>('rules', '/mill/alert-rules');
export const useNotifications = () =>
  useQuery({ queryKey: mk.view('notifications'), queryFn: () => getData<Page<Notification> & { unread: number }>('/mill/notifications', { page_size: 20 }),
             refetchInterval: 30_000 });
export const useChannels = () => useView<{ channel: string; configured: boolean; note: string | null }[]>('channels', '/mill/notification-channels');

export const useGroups = () => useView<Group[]>('groups', '/mill/groups');
export const useGroup = (id: number | null) =>
  useQuery({ enabled: id != null, queryKey: mk.view('group', id), queryFn: () => getData<Group>(`/mill/groups/${id}`) });
export const usePeople = () => useView<Person[]>('people', '/mill/people');
export const useTasks = (p: FilterQuery) => useView<Page<Task>>('tasks', '/mill/tasks', p);
export const useTask = (id: number | null) =>
  useQuery({ enabled: id != null, queryKey: mk.view('task', id), queryFn: () => getData<Task>(`/mill/tasks/${id}`) });
export const useDailyBoard = () => useView<any[]>('daily-board', '/mill/daily-board');
export const useWorkOrders = (p: FilterQuery) => useView<Page<WorkOrder>>('work-orders', '/mill/work-orders', p);

export const useReports = () => useView<Page<OwnerReport>>('reports', '/mill/reports', { page_size: 100 });
export const useReport = (id: number) => useView<OwnerReport>(`report-${id}`, `/mill/reports/${id}`);
export const useConnectivity = () => useView<{ connections: Connection[]; adapters: Record<string, string>; policy: string[] }>('connectivity', '/mill/connectivity');
export const useTargets = () => useView<any[]>('targets', '/mill/targets');
export const useAudit = (page: number, entity?: string) => useView<Page<any>>('audit', '/mill/audit', { page, page_size: 50, entity });

/** A mutation that refreshes all weaving data when it succeeds. */
export function useMillMutation<V, R = unknown>(fn: (v: V) => Promise<R>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: fn, onSuccess: () => qc.invalidateQueries({ queryKey: mk.all }) });
}

export const api = {
  post: postJson,
  patch: patchJson,
  put: putJson,
  del: deleteJson,
  upload: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return postForm<ImportBatch>('/mill/imports/preview', form);
  },
};
