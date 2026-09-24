import React from 'react';
import { ShiftPerformanceItem } from '../../types/production';
import { Card } from '../ui/Card';

interface ShiftPerformanceSectionProps {
  shifts?: ShiftPerformanceItem[];
}

export const ShiftPerformanceSection: React.FC<ShiftPerformanceSectionProps> = ({ shifts }) => {
  if (!shifts || shifts.length === 0) return null;

  return (
    <Card className="p-5 space-y-4">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          SHIFT PERFORMANCE
        </h2>
        <p className="text-xs text-slate-500 font-medium mt-0.5">
          Operational output and target achievement across shifts
        </p>
      </div>

      <div className="space-y-3.5 pt-1">
        {shifts.map((s) => {
          const barPct = Math.min(100, s.achievement_pct);
          const barBg = s.achievement_pct >= 95 ? 'bg-blue-600' : 'bg-amber-500';

          return (
            <div key={s.shift_name} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-bold text-slate-900">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold">{s.shift_name}</span>
                  <span className="text-xs text-slate-400 font-mono">({s.actual_kg.toLocaleString()} kg)</span>
                </div>
                <span className="font-mono text-slate-900 font-extrabold">{s.achievement_pct.toFixed(1)}%</span>
              </div>

              <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden p-0.5 border border-slate-200/80">
                <div
                  className={`${barBg} h-full rounded-full transition-all duration-500`}
                  style={{ width: `${barPct}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
