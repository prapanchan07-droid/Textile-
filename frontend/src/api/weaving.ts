import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { getData, http, postJson } from './client';
import type { Period } from '../lib/period';
import type {
  ActionsData, CockpitData, CommandData, CompareMeta, CompareResult, FleetData, HandoverData, InsightsData, MachineDetail, MaintenanceData, OrdersData, OwnerData, ProductionData,
  QualityData, SchedulerData, StoppagesData, WorkforceData,
} from '../types/pages';

type Params = Record<string, string | number | undefined>;

/** One weaving page's data. `live` pages refresh on their own because the floor changes by the minute. */
function usePage<T>(slug: string, params: Params = {}, opts: { live?: boolean; enabled?: boolean } = {}) {
  return useQuery({
    enabled: opts.enabled ?? true,
    queryKey: ['weaving', 'page', slug, params],
    queryFn: () => getData<T>(`/weaving/pages/${slug}`, params),
    placeholderData: keepPreviousData,
    refetchInterval: opts.live ? 60_000 : false,
    staleTime: opts.live ? 20_000 : 60_000,
  });
}

export const useCommand = (period: Period) => usePage<CommandData>('command', { period }, { live: true });
export const useOwner = (period: Period) => usePage<OwnerData>('owner', { period });
export const useProduction = (period: Period) => usePage<ProductionData>('production', { period });
export const useStoppages = (period: Period) => usePage<StoppagesData>('stoppages', { period }, { live: true });
export const useFleet = (enabled = true) => usePage<FleetData>('machines', {}, { live: true, enabled });
export const useMaintenance = () => usePage<MaintenanceData>('maintenance', {}, { live: true });
export const useWorkforce = () => usePage<WorkforceData>('workforce');
export const useCockpit = () => usePage<CockpitData>('cockpit', {}, { live: true });
export const useHandover = (which: 'current' | 'previous') => usePage<HandoverData>('handover', { which });
export const useOrders = () => usePage<OrdersData>('orders');
export const useScheduler = () => usePage<SchedulerData>('scheduler');
export const useInsights = (period: Period) => usePage<InsightsData>('insights', { period });
export const useQuality = (period: Period) => usePage<QualityData>('quality', { period });
export const useActions = () => usePage<ActionsData>('actions');
export const useCompareMeta = () => usePage<CompareMeta>('compare');

export const useMachine = (loom: string | null) =>
  useQuery({ queryKey: ['weaving', 'machine', loom], queryFn: () => getData<MachineDetail>(`/weaving/pages/machines/${loom}`), enabled: !!loom, staleTime: 60_000 });

export const useCompareRun = (args: { type: string; keys: string[]; metrics: string[]; days: number; style?: string | null }, enabled: boolean) =>
  useQuery({
    queryKey: ['weaving', 'compare', args],
    enabled: enabled && args.keys.length > 0,
    placeholderData: keepPreviousData,
    queryFn: () =>
      getData<CompareResult>('/weaving/compare/run', { type: args.type, keys: args.keys, metrics: args.metrics, days: args.days, ...(args.style ? { style: args.style } : {}) }),
  });

/** After any write, every weaving page may have changed. */
function useWrite<TBody, TOut>(fn: (b: TBody) => Promise<TOut>) {
  const qc = useQueryClient();
  return useMutation({ mutationFn: fn, onSuccess: () => qc.invalidateQueries({ queryKey: ['weaving'] }) });
}

export const useCreateAction = () =>
  useWrite((b: { issue: string; action: string; owner_role?: string | null; owner_name?: string | null; due_date?: string | null; finding_key?: string | null; expected_impact_lakhs?: number }) =>
    postJson<{ ref: string; status: string; requires_approval: boolean }>('/weaving/actions', b));

export const useUpdateAction = () =>
  useWrite(async (b: { ref: string; status?: string; outcome_note?: string; verified_cause?: string }) => {
    const { ref, ...body } = b;
    const res = await http.patch(`/weaving/actions/${ref}`, body);
    return res.data;
  });

export const useApproveAction = () => useWrite((ref: string) => postJson<{ ref: string }>(`/weaving/actions/${ref}/approve`, {}));
export const useCreateNote = () => useWrite((b: { body: string; loom?: string | null; category: string; severity: string }) => postJson<{ id: number }>('/weaving/notes', b));
export const useResolveNote = () => useWrite((id: number) => postJson<{ id: number }>(`/weaving/notes/${id}/resolve`, {}));
export const useSchedulerDecision = () =>
  useWrite((b: { decision: 'APPROVE' | 'REJECT'; signature: string; note?: string }) => postJson<{ plan_ref: string; status: string; actions_created: number }>('/weaving/scheduler/decision', b));

export const useCompareOptions = (type: string, enabled: boolean) =>
  useQuery({ queryKey: ['weaving', 'compare-options', type], enabled, queryFn: () => getData<{ key: string; label: string; group: string }[]>('/weaving/compare/options', { type }), staleTime: 300_000 });
