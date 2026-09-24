import React from 'react';
import { Card } from '../ui/Card';

interface LowEfficiencySectionProps {
  machineType: string;
  efficiencyPct: number;
  factoryAvgGap: number;
  lossKg: number;
}

export const LowEfficiencySection: React.FC<LowEfficiencySectionProps> = ({
  machineType,
  efficiencyPct,
  factoryAvgGap,
  lossKg,
}) => {
  return (
    <Card className="space-y-4 p-6 border-rose-200 bg-rose-50/20">
      <div className="flex justify-between items-center border-b border-rose-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            4. MACHINE TYPE REQUIRING ATTENTION
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            Spotlight: <span className="text-rose-700 font-mono font-extrabold uppercase">{machineType}</span>
          </p>
        </div>
        <span className="text-xs font-extrabold text-rose-800 bg-rose-100 border border-rose-200 px-2.5 py-1 rounded-lg">
          -{lossKg.toLocaleString()} kg Loss
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 font-mono">
        <div className="bg-white p-3.5 rounded-xl border border-rose-200 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase font-sans">Efficiency</span>
          <div className="text-2xl font-extrabold text-amber-700 mt-0.5">
            {efficiencyPct}%
          </div>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-rose-200 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase font-sans">Vs Factory Avg</span>
          <div className="text-2xl font-extrabold text-rose-700 mt-0.5">
            {factoryAvgGap} % pts
          </div>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-rose-200 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase font-sans">Total Loss</span>
          <div className="text-2xl font-extrabold text-rose-700 mt-0.5">
            -{lossKg.toLocaleString()} kg
          </div>
        </div>
      </div>

      {/* Why Breakdown Horizontal Bars */}
      <div className="space-y-2 pt-2">
        <div className="text-xs font-bold text-slate-600 uppercase">Top Loss Factors for {machineType}:</div>
        <div className="space-y-2 text-xs">
          <div className="space-y-1">
            <div className="flex justify-between font-semibold text-slate-900">
              <span>Machine Downtime</span>
              <span className="font-mono text-rose-600 font-bold">47%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div className="bg-rose-600 h-full rounded-full" style={{ width: '47%' }} />
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex justify-between font-semibold text-slate-900">
              <span>Efficiency Loss</span>
              <span className="font-mono text-amber-600 font-bold">30%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div className="bg-amber-500 h-full rounded-full" style={{ width: '30%' }} />
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex justify-between font-semibold text-slate-900">
              <span>Power Events</span>
              <span className="font-mono text-slate-700 font-bold">12%</span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2">
              <div className="bg-slate-600 h-full rounded-full" style={{ width: '12%' }} />
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
