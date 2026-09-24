import React from 'react';
import { IfContinuesData } from '../../types/decisionCenter';
import { ArrowDown, AlertCircle } from 'lucide-react';

interface IfContinuesSectionProps {
  data: IfContinuesData;
}

export const IfContinuesSection: React.FC<IfContinuesSectionProps> = ({ data }) => {
  return (
    <section className="space-y-3">
      <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
        5. IF THIS CONTINUES
      </h2>

      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-700 uppercase tracking-wide">
            {data.label}
          </span>
          <span className="text-[11px] font-semibold text-slate-400">
            Unmitigated Loss Progression
          </span>
        </div>

        {/* Projection Cards Sequence */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
          {/* Current Gap */}
          <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-center space-y-1">
            <span className="text-xs font-bold text-slate-500 block uppercase">
              Current Daily Gap
            </span>
            <span className="text-2xl font-black text-red-600 font-mono block">
              {data.current_daily_gap_kg.toLocaleString()} kg/day
            </span>
          </div>

          {/* 7 Days Projection */}
          <div className="bg-amber-50/70 border border-amber-200 rounded-xl p-4 text-center space-y-1 relative">
            <div className="hidden md:block absolute -left-3 top-1/2 -translate-y-1/2 z-10 bg-white border border-slate-200 rounded-full p-1 text-slate-400">
              <ArrowDown className="w-3.5 h-3.5 -rotate-90" />
            </div>
            <span className="text-xs font-bold text-amber-800 block uppercase">
              7 Days Projection
            </span>
            <span className="text-2xl font-black text-amber-700 font-mono block">
              {data.projected_7d_gap_kg.toLocaleString()} kg
            </span>
          </div>

          {/* 30 Days Projection */}
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-center space-y-1 relative">
            <div className="hidden md:block absolute -left-3 top-1/2 -translate-y-1/2 z-10 bg-white border border-slate-200 rounded-full p-1 text-slate-400">
              <ArrowDown className="w-3.5 h-3.5 -rotate-90" />
            </div>
            <span className="text-xs font-bold text-red-800 block uppercase">
              30 Days Projection
            </span>
            <span className="text-2xl font-black text-red-700 font-mono block">
              {data.projected_30d_gap_kg.toLocaleString()} kg
            </span>
          </div>
        </div>

        {/* Small Disclaimer */}
        <div className="flex items-center gap-2 text-slate-500 text-xs font-normal pt-1">
          <AlertCircle className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <p>{data.disclaimer_note}</p>
        </div>
      </div>
    </section>
  );
};
