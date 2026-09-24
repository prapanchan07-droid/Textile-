import React from 'react';
import { Cpu, AlertCircle, ArrowRight, Gauge, MapPin } from 'lucide-react';
import { MachineAttentionItem, LowEfficiencyMachine } from '../../types/overview';
import { Card } from '../ui/Card';

interface MachineAttentionCardProps {
  machines: MachineAttentionItem[];
  spotlight: LowEfficiencyMachine;
  onViewMachineAnalysis?: () => void;
}

export const MachineAttentionCard: React.FC<MachineAttentionCardProps> = ({
  machines,
  spotlight,
  onViewMachineAnalysis,
}) => {
  const topMachine = machines.length > 0 ? machines[0] : null;

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Left 2 Cols: Machines Telemetry Node Matrix */}
      <Card className="lg:col-span-2 space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-600" />
              <h3 className="font-bold text-slate-900 text-base">Machine Telemetry Nodes Requiring Attention</h3>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">Real-time machine telemetry, stoppage logs, and efficiency drop</p>
          </div>
          <button
            onClick={onViewMachineAnalysis}
            className="flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-800 transition-colors"
          >
            <span>Telemetry Map</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Top Machine Spotlight Bar */}
        {topMachine && (
          <div className="bg-rose-50/80 border border-rose-200 p-4 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="bg-rose-600 text-white font-bold text-[10px] px-2 py-0.5 rounded uppercase">CRITICAL NODE</span>
                <span className="text-xs text-rose-800 font-semibold">{topMachine.section_id}</span>
              </div>
              <h4 className="text-lg font-extrabold text-slate-900 font-mono">
                {topMachine.machine_id} <span className="text-xs text-slate-500 font-normal font-sans">({topMachine.machine_type})</span>
              </h4>
              <p className="text-xs text-slate-700 mt-0.5">
                Issue: <strong className="text-slate-900">{topMachine.primary_issue}</strong>
              </p>
            </div>

            <div className="flex items-center gap-3 text-xs font-mono">
              <div className="bg-white px-3 py-1.5 rounded-lg border border-rose-200 shadow-sm text-center">
                <span className="text-slate-400 block text-[10px] uppercase font-sans">Loss</span>
                <span className="text-rose-600 font-extrabold">{topMachine.loss_kg} kg</span>
              </div>
              <div className="bg-white px-3 py-1.5 rounded-lg border border-rose-200 shadow-sm text-center">
                <span className="text-slate-400 block text-[10px] uppercase font-sans">Efficiency</span>
                <span className="text-amber-600 font-extrabold">{topMachine.efficiency_pct}%</span>
              </div>
              <div className="bg-white px-3 py-1.5 rounded-lg border border-rose-200 shadow-sm text-center">
                <span className="text-slate-400 block text-[10px] uppercase font-sans">Downtime</span>
                <span className="text-slate-900 font-extrabold">{topMachine.downtime_minutes} m</span>
              </div>
            </div>
          </div>
        )}

        {/* Machine Telemetry List */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
                <th className="py-2.5 px-3">Node ID</th>
                <th className="py-2.5 px-3">Type</th>
                <th className="py-2.5 px-3">Production Loss</th>
                <th className="py-2.5 px-3">Efficiency</th>
                <th className="py-2.5 px-3">Downtime</th>
                <th className="py-2.5 px-3">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-mono">
              {machines.map((m) => (
                <tr key={m.machine_id} className="hover:bg-slate-50 transition-colors">
                  <td className="py-3 px-3 font-bold text-slate-900 font-mono">{m.machine_id}</td>
                  <td className="py-3 px-3 text-slate-600 font-sans text-xs">{m.machine_type}</td>
                  <td className="py-3 px-3 text-rose-600 font-bold">-{m.loss_kg} kg</td>
                  <td className="py-3 px-3 text-amber-600 font-bold">{m.efficiency_pct}%</td>
                  <td className="py-3 px-3 text-slate-700">{m.downtime_minutes} min</td>
                  <td className="py-3 px-3 font-sans">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      m.status === 'CRITICAL'
                        ? 'bg-rose-100 text-rose-800'
                        : m.status === 'ATTENTION'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {m.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Right Col: Efficiency Ingestion Node */}
      <Card className="space-y-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center gap-2">
              <Gauge className="w-5 h-5 text-amber-600" />
              <h3 className="font-bold text-slate-900 text-base">Node Efficiency Gap</h3>
            </div>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 mt-3 space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-xs text-slate-500 uppercase font-bold tracking-wider">Node Spotlight</span>
              <span className="bg-amber-100 text-amber-800 font-bold px-2 py-0.5 rounded font-mono text-xs">
                {spotlight.machine_id}
              </span>
            </div>

            <div className="flex items-baseline justify-between">
              <span className="text-xs text-slate-600">Current Efficiency:</span>
              <span className="text-2xl font-extrabold text-amber-600 font-mono">{spotlight.efficiency_pct}%</span>
            </div>

            <div className="flex items-baseline justify-between text-xs border-t border-slate-200 pt-2 text-slate-500">
              <span>Factory Average:</span>
              <span className="text-slate-900 font-mono font-bold">{spotlight.factory_avg_pct}%</span>
            </div>

            <div className="flex items-baseline justify-between text-xs text-rose-600 font-bold border-t border-slate-200 pt-2">
              <span>Efficiency Deficit:</span>
              <span className="font-mono">{spotlight.gap_points} % pts</span>
            </div>
          </div>
        </div>

        <p className="text-[11px] text-slate-400 italic pt-2">
          {spotlight.historical_status}
        </p>
      </Card>
    </div>
  );
};
