import React from 'react';
import { MachineDetailData } from '../../types/machines';
import { Card } from '../ui/Card';
import { Cpu, Wrench, Zap, Activity } from 'lucide-react';

interface MachineDetailSectionProps {
  detail?: MachineDetailData;
}

export const MachineDetailSection: React.FC<MachineDetailSectionProps> = ({ detail }) => {
  if (!detail) {
    return (
      <Card className="p-6 text-center text-slate-500 text-xs">
        Data not available
      </Card>
    );
  }

  return (
    <Card className="space-y-5 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            5. MACHINE DETAIL
          </h2>
          <div className="flex items-baseline gap-2 mt-1">
            <span className="text-xl font-extrabold text-slate-900 font-mono">
              MACHINE: {detail.machine_id}
            </span>
            <span className="text-xs font-bold text-slate-500 uppercase px-2 py-0.5 rounded bg-slate-100 border border-slate-200">
              TYPE: {detail.machine_type}
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-xs">
        {/* PERFORMANCE */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            <Cpu className="w-3.5 h-3.5 text-slate-600" />
            <span>PERFORMANCE</span>
          </div>
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Production:</span>
              <span className="font-mono font-bold text-slate-900">
                {detail.actual_kg ? `${detail.actual_kg.toLocaleString()} kg` : 'Data not available'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Target:</span>
              <span className="font-mono font-bold text-slate-600">
                {detail.target_kg ? `${detail.target_kg.toLocaleString()} kg` : 'Data not available'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Efficiency:</span>
              <span className="font-mono font-bold text-blue-600">
                {detail.efficiency_pct ? `${detail.efficiency_pct}%` : 'Data not available'}
              </span>
            </div>
            <div className="flex justify-between border-t border-slate-200/60 pt-1.5">
              <span className="text-slate-500">Production Loss:</span>
              <span className="font-mono font-extrabold text-rose-600">
                {detail.loss_kg ? `-${detail.loss_kg.toLocaleString()} kg` : 'Data not available'}
              </span>
            </div>
          </div>
        </div>

        {/* DOWNTIME */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            <Activity className="w-3.5 h-3.5 text-slate-600" />
            <span>DOWNTIME</span>
          </div>
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Total Downtime:</span>
              <span className="font-mono font-bold text-amber-700">
                {detail.total_downtime_min ? `${detail.total_downtime_min} min` : 'Data not available'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Stoppage Count:</span>
              <span className="font-mono font-bold text-slate-900">
                {detail.stoppage_count ? `${detail.stoppage_count} events` : 'Data not available'}
              </span>
            </div>
            <div className="border-t border-slate-200/60 pt-1.5 space-y-0.5">
              <span className="text-slate-500 block">Main Reason:</span>
              <span className="font-bold text-slate-900 block truncate">
                {detail.main_reason || 'Data not available'}
              </span>
            </div>
          </div>
        </div>

        {/* MAINTENANCE */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            <Wrench className="w-3.5 h-3.5 text-slate-600" />
            <span>MAINTENANCE</span>
          </div>
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Last Maintenance:</span>
              <span className="font-semibold text-slate-900">
                {detail.last_maintenance || 'Data not available'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Next Scheduled:</span>
              <span className="font-semibold text-slate-900">
                {detail.next_maintenance || 'Data not available'}
              </span>
            </div>
            <div className="border-t border-slate-200/60 pt-1.5 space-y-0.5">
              <span className="text-slate-500 block">Recent Event:</span>
              <span className="font-semibold text-slate-700 block truncate">
                {detail.recent_event || 'Data not available'}
              </span>
            </div>
          </div>
        </div>

        {/* POWER & QUALITY */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-2">
          <div className="flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
            <Zap className="w-3.5 h-3.5 text-slate-600" />
            <span>POWER & QUALITY</span>
          </div>
          <div className="space-y-1.5 pt-1">
            <div className="flex justify-between">
              <span className="text-slate-500">Power Events:</span>
              <span className="font-mono font-bold text-slate-900">
                {detail.power_events !== undefined ? detail.power_events : 'Data not available'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Power Downtime:</span>
              <span className="font-mono font-bold text-slate-900">
                {detail.power_downtime_min ? `${detail.power_downtime_min} min` : 'Data not available'}
              </span>
            </div>
            <div className="border-t border-slate-200/60 pt-1.5 space-y-0.5">
              <span className="text-slate-500 block">Quality Status:</span>
              <span className="font-bold text-emerald-700 block truncate">
                {detail.quality_status || 'Data not available'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
