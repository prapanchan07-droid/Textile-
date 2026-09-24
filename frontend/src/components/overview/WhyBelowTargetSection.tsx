import React from 'react';
import { HelpCircle, ArrowDownRight, Layers } from 'lucide-react';
import { LossContributor } from '../../types/overview';
import { Card } from '../ui/Card';

interface WhyBelowTargetSectionProps {
  contributors: LossContributor[];
  totalLossKg: number;
}

export const WhyBelowTargetSection: React.FC<WhyBelowTargetSectionProps> = ({
  contributors,
  totalLossKg,
}) => {
  return (
    <Card className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-600" />
            <h3 className="font-bold text-slate-900 text-base">Production Loss Pipeline & Breakdown</h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Step decay rates across full operational pipeline ({totalLossKg.toLocaleString()} kg total loss)
          </p>
        </div>
        <div className="bg-slate-100 text-slate-700 text-xs px-3 py-1 rounded-lg font-mono font-semibold self-start sm:self-auto">
          Loss Contribution: {totalLossKg.toLocaleString()} kg
        </div>
      </div>

      {/* Horizontal Pipeline Steps */}
      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 pt-2">
        {contributors.map((c, idx) => (
          <div
            key={idx}
            className={`p-3.5 rounded-xl border flex flex-col justify-between space-y-3 transition-all ${
              idx === 0
                ? 'bg-rose-50/50 border-rose-200'
                : idx === 1
                ? 'bg-amber-50/50 border-amber-200'
                : 'bg-slate-50 border-slate-200'
            }`}
          >
            <div>
              <div className="flex justify-between items-center text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                <span>0{idx + 1}. FACTOR</span>
                <span className={`font-mono ${idx === 0 ? 'text-rose-600' : 'text-slate-600'}`}>{c.percentage}%</span>
              </div>
              <h4 className="text-xs font-bold text-slate-900 truncate" title={c.category}>{c.category}</h4>
              <div className="text-lg font-extrabold text-slate-900 font-mono mt-1">
                -{c.impact_kg.toLocaleString()} <span className="text-xs font-normal text-slate-500">kg</span>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between text-[11px]">
              <span className="text-slate-500 truncate" title={c.evidence}>{c.evidence}</span>
              <span className={`inline-flex items-center gap-0.5 font-bold font-mono ${idx === 0 ? 'text-rose-600' : 'text-slate-600'}`}>
                <ArrowDownRight className="w-3 h-3" />
                {c.percentage}%
              </span>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
};
