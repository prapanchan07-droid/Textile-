import React from 'react';
import { LossReasonItem } from '../../types/production';
import { Card } from '../ui/Card';

interface ProductionLossReasonsSectionProps {
  reasons: LossReasonItem[];
}

export const ProductionLossReasonsSection: React.FC<ProductionLossReasonsSectionProps> = ({
  reasons,
}) => {
  return (
    <Card className="p-5 space-y-4">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          WHERE IS PRODUCTION LOSS?
        </h2>
        <p className="text-xs text-slate-500 font-medium mt-0.5">
          Major contributors driving production deficit
        </p>
      </div>

      <div className="space-y-3.5 pt-1">
        {reasons.map((r, idx) => {
          const barColor =
            idx === 0 ? 'bg-red-500' : idx === 1 ? 'bg-amber-500' : 'bg-slate-700';

          return (
            <div key={r.rank || idx} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-bold text-slate-900">
                <span>{r.category}</span>
                <div className="flex items-center gap-3 font-mono">
                  <span className="text-slate-500 font-normal">{r.impact_kg.toLocaleString()} kg</span>
                  <span className="text-slate-900 font-bold">{r.percentage}%</span>
                </div>
              </div>

              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden p-0.5 border border-slate-200/80">
                <div
                  className={`${barColor} h-full rounded-full transition-all duration-500`}
                  style={{ width: `${Math.min(100, r.percentage)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
