import React from 'react';
import { Card } from '../ui/Card';

interface IfThisContinuesSectionProps {
  dailyGapKg: number;
  projected7dKg: number;
  projected30dKg: number;
}

export const IfThisContinuesSection: React.FC<IfThisContinuesSectionProps> = ({
  dailyGapKg = 2380,
  projected7dKg = 16660,
  projected30dKg = 71400,
}) => {
  return (
    <Card className="space-y-4 p-6 border-rose-200 bg-rose-50/20">
      <div className="flex justify-between items-center border-b border-rose-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            6. IF THIS CONTINUES
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            Estimated Impact If Problems Continue Unfixed
          </p>
        </div>
        <span className="text-xs font-bold text-rose-700 bg-rose-100 px-2.5 py-1 rounded-lg">
          Projection
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 font-mono">
        <div className="bg-white p-3.5 rounded-xl border border-rose-200 text-center">
          <span className="text-[10px] text-slate-500 font-bold uppercase font-sans">Daily Gap</span>
          <div className="text-lg font-extrabold text-rose-600 mt-0.5">
            -{dailyGapKg.toLocaleString()} kg
          </div>
          <span className="text-[10px] text-slate-400 font-sans">per day</span>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-rose-200 text-center">
          <span className="text-[10px] text-slate-500 font-bold uppercase font-sans">7-Day Gap</span>
          <div className="text-lg font-extrabold text-rose-600 mt-0.5">
            -{projected7dKg.toLocaleString()} kg
          </div>
          <span className="text-[10px] text-slate-400 font-sans">in 1 week</span>
        </div>

        <div className="bg-white p-3.5 rounded-xl border border-rose-300 text-center shadow-sm">
          <span className="text-[10px] text-rose-700 font-bold uppercase font-sans">30-Day Gap</span>
          <div className="text-lg font-extrabold text-rose-700 mt-0.5">
            -{projected30dKg.toLocaleString()} kg
          </div>
          <span className="text-[10px] text-slate-400 font-sans">in 1 month</span>
        </div>
      </div>

      <p className="text-[11px] text-slate-500 italic text-center pt-1">
        Based on current daily performance gap continuing without intervention.
      </p>
    </Card>
  );
};
