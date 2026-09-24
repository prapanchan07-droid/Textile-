import React from 'react';
import { LossContributor } from '../../types/overview';
import { Card } from '../ui/Card';

interface WhyIsProductionLowSectionProps {
  contributors: LossContributor[];
  totalLossKg: number;
}

export const WhyIsProductionLowSection: React.FC<WhyIsProductionLowSectionProps> = ({
  contributors,
  totalLossKg,
}) => {
  // Take ONLY top 3 factors
  const top3 = contributors.slice(0, 3);
  const topReason = top3.length > 0 ? top3[0].category : 'Machine downtime';

  return (
    <Card className="space-y-5 p-6">
      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            2. WHY IS PRODUCTION LOW?
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            Main Reason: <span className="text-rose-600">{topReason}</span>
          </p>
        </div>
        <span className="text-xs font-mono font-bold text-rose-600 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-lg">
          -{totalLossKg.toLocaleString()} kg Total Loss
        </span>
      </div>

      {/* Top 3 Factors Ranked List */}
      <div className="space-y-4">
        {top3.map((factor, idx) => {
          const dotColor = idx === 0 ? 'bg-rose-600' : idx === 1 ? 'bg-amber-500' : 'bg-yellow-500';
          const barColor = idx === 0 ? 'bg-rose-600' : idx === 1 ? 'bg-amber-500' : 'bg-slate-500';

          return (
            <div key={idx} className="space-y-1.5 bg-slate-50 p-3.5 rounded-xl border border-slate-200/70">
              <div className="flex items-center justify-between text-xs font-bold">
                <div className="flex items-center gap-2 text-slate-900">
                  <span className={`w-2.5 h-2.5 rounded-full ${dotColor}`} />
                  <span>{factor.category}</span>
                </div>
                <div className="font-mono text-slate-900 font-extrabold">
                  -{factor.impact_kg.toLocaleString()} kg <span className="text-slate-400 font-medium text-[11px]">({factor.percentage}%)</span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${barColor}`}
                  style={{ width: `${factor.percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
