import React from 'react';
import { TrendingDown, AlertOctagon, Info } from 'lucide-react';
import { ImpactProjectionData } from '../../types/overview';
import { Card } from '../ui/Card';

interface IfThisContinuesImpactProps {
  projection: ImpactProjectionData;
}

export const IfThisContinuesImpact: React.FC<IfThisContinuesImpactProps> = ({ projection }) => {
  return (
    <Card className="border-rose-200 bg-gradient-to-br from-rose-50/30 to-white space-y-4">
      <div className="flex items-center justify-between border-b border-rose-100 pb-3">
        <div className="flex items-center gap-2">
          <TrendingDown className="w-5 h-5 text-rose-600" />
          <h3 className="font-bold text-slate-900 text-base">Estimated Cumulative Operational Impact</h3>
        </div>
        <span className="bg-rose-100 text-rose-800 border border-rose-200 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
          PROJECTED HORIZON
        </span>
      </div>

      <p className="text-xs text-slate-500">
        Cumulative production volume deficit if current daily performance gap persists unmitigated.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
          <span className="text-[11px] text-slate-400 font-bold uppercase tracking-wider">Current Daily Gap</span>
          <div className="text-xl font-extrabold text-rose-600 font-mono mt-1">
            -{projection.daily_gap_kg.toLocaleString()} kg/day
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Observed today</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-rose-200 shadow-sm">
          <span className="text-[11px] text-rose-700 font-bold uppercase tracking-wider">7-Day Projected Gap</span>
          <div className="text-xl font-extrabold text-rose-600 font-mono mt-1">
            -{projection.projected_7d_gap_kg.toLocaleString()} kg
          </div>
          <p className="text-[11px] text-slate-500 mt-1">1-week horizon impact</p>
        </div>

        <div className="bg-white p-4 rounded-xl border border-rose-300 shadow-sm">
          <span className="text-[11px] text-rose-700 font-bold uppercase tracking-wider">30-Day Projected Gap</span>
          <div className="text-xl font-extrabold text-rose-700 font-mono mt-1">
            -{projection.projected_30d_gap_kg.toLocaleString()} kg
          </div>
          <p className="text-[11px] text-slate-500 mt-1">1-month horizon impact</p>
        </div>
      </div>

      <div className="flex items-center gap-2 text-[11px] text-slate-500 bg-white p-2.5 rounded-lg border border-slate-200 shadow-sm">
        <Info className="w-3.5 h-3.5 text-slate-400 shrink-0" />
        <span>{projection.assumptions_note}</span>
      </div>
    </Card>
  );
};
