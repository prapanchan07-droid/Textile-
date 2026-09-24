import React from 'react';
import { MachinePerformanceItem, SpotlightMachine } from '../../types/machines';
import { Card } from '../ui/Card';
import { AlertTriangle, Filter } from 'lucide-react';

interface MachinePerformanceSectionProps {
  spotlight: SpotlightMachine;
  machines: MachinePerformanceItem[];
  machineTypes: string[];
  selectedPeriod: string;
  onPeriodChange: (p: string) => void;
  selectedType: string;
  onTypeChange: (type: string) => void;
  selectedMachineId: string;
  onMachineIdChange: (id: string) => void;
}

export const MachinePerformanceSection: React.FC<MachinePerformanceSectionProps> = ({
  spotlight,
  machines,
  machineTypes,
  selectedPeriod,
  onPeriodChange,
  selectedType,
  onTypeChange,
  selectedMachineId,
  onMachineIdChange,
}) => {
  // Master list to ensure dropdown options are never lost upon selection
  const masterList = ['V-09', 'V-05', 'SMX-03', 'V-12', 'RF-04', 'A-02'];
  const availableMachineIds = ['ALL', ...Array.from(new Set([...machines.map((m) => m.machine_id), ...masterList]))];

  return (
    <Card className="space-y-6 p-6">
      {/* Title & Filter Toolbar */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            1. MACHINE PERFORMANCE
          </h2>
          <p className="text-base font-bold text-slate-900 mt-0.5">
            Find machines with low efficiency and high production loss
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Period Selector Pill */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs">
            {(
              [
                { id: 'TODAY', label: 'Today' },
                { id: 'SEVEN_DAYS', label: '7 Days' },
                { id: 'THIS_MONTH', label: 'This Month' },
              ] as const
            ).map((r) => (
              <button
                key={r.id}
                onClick={() => onPeriodChange(r.id)}
                className={`px-3 py-1 rounded-md font-bold transition-all ${
                  selectedPeriod === r.id
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-white'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>

          {/* Machine Type Filter */}
          <div className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <span>Type:</span>
            <select
              value={selectedType}
              onChange={(e) => onTypeChange(e.target.value)}
              className="bg-transparent font-bold text-slate-900 focus:outline-none cursor-pointer"
            >
              {machineTypes.map((t) => (
                <option key={t} value={t === 'All' ? 'ALL' : t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Machine ID Filter */}
          <div className="flex items-center gap-1.5 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700">
            <span>Machine:</span>
            <select
              value={selectedMachineId}
              onChange={(e) => onMachineIdChange(e.target.value)}
              className="bg-transparent font-bold text-slate-900 focus:outline-none cursor-pointer font-mono"
            >
              {availableMachineIds.map((id) => (
                <option key={id} value={id}>
                  {id === 'ALL' ? 'All Machines' : id}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Spotlight Card: Machine Requiring Attention */}
      <div className="bg-amber-50/60 border border-amber-200/80 rounded-2xl p-4.5 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-sm">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2 text-amber-800 font-extrabold text-xs tracking-wide uppercase">
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>MACHINE REQUIRING ATTENTION</span>
          </div>

          <div className="flex items-baseline gap-3">
            <span className="text-2xl font-extrabold text-slate-900 font-mono tracking-tight">
              {spotlight.machine_id}
            </span>
            <span className="text-xs font-bold text-slate-500 uppercase px-2 py-0.5 rounded bg-white/80 border border-amber-200/60 font-sans">
              {spotlight.machine_type}
            </span>
          </div>

          <p className="text-xs text-slate-700 font-medium">
            Main issue: <span className="font-bold text-slate-900">{spotlight.main_issue}</span>
          </p>
        </div>

        <div className="grid grid-cols-3 gap-3 md:gap-4 bg-white/90 border border-amber-200/60 rounded-xl p-3 text-center shrink-0">
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase">Loss</div>
            <div className="text-sm font-extrabold text-rose-600 font-mono">
              {spotlight.loss_kg.toLocaleString()} <span className="text-[10px] font-normal text-slate-500">kg</span>
            </div>
          </div>
          <div className="border-x border-slate-100 px-2">
            <div className="text-[10px] font-bold text-slate-400 uppercase">Efficiency</div>
            <div className="text-sm font-extrabold text-slate-900 font-mono">
              {spotlight.efficiency_pct}%
            </div>
          </div>
          <div>
            <div className="text-[10px] font-bold text-slate-400 uppercase">Downtime</div>
            <div className="text-sm font-extrabold text-amber-700 font-mono">
              {spotlight.downtime_min} <span className="text-[10px] font-normal text-slate-500">min</span>
            </div>
          </div>
        </div>
      </div>

      {/* Machine Performance Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4">Machine</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4 text-right">Production</th>
              <th className="py-3 px-4 text-right">Target</th>
              <th className="py-3 px-4 text-right">Efficiency</th>
              <th className="py-3 px-4 text-right">Loss</th>
              <th className="py-3 px-4 text-right">Downtime</th>
              <th className="py-3 px-4 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono text-slate-900 font-semibold">
            {machines.map((m) => {
              const statusColors =
                m.status === 'CRITICAL'
                  ? 'bg-rose-50 text-rose-700 border-rose-200'
                  : m.status === 'ATTENTION'
                  ? 'bg-amber-50 text-amber-800 border-amber-200'
                  : 'bg-emerald-50 text-emerald-700 border-emerald-200';

              return (
                <tr key={m.machine_id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-bold text-slate-900">{m.machine_id}</td>
                  <td className="py-3 px-4 font-sans font-medium text-slate-600">{m.machine_type}</td>
                  <td className="py-3 px-4 text-right">{m.actual_kg.toLocaleString()} kg</td>
                  <td className="py-3 px-4 text-right text-slate-500">{m.target_kg.toLocaleString()} kg</td>
                  <td className="py-3 px-4 text-right font-bold">{m.efficiency_pct}%</td>
                  <td className="py-3 px-4 text-right text-rose-600 font-bold">-{m.loss_kg.toLocaleString()} kg</td>
                  <td className="py-3 px-4 text-right text-slate-700">{m.downtime_min} min</td>
                  <td className="py-3 px-4 text-center font-sans">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${statusColors}`}>
                      {m.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
