import React from 'react';
import { Card } from '../ui/Card';

interface ComparedWithYesterdaySectionProps {
  yesterdayKg: number;
  todayKg: number;
}

export const ComparedWithYesterdaySection: React.FC<ComparedWithYesterdaySectionProps> = ({
  yesterdayKg = 36100,
  todayKg = 34620,
}) => {
  const diffKg = todayKg - yesterdayKg;
  const diffPct = ((diffKg / yesterdayKg) * 100).toFixed(1);

  return (
    <Card className="space-y-5 p-6">
      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            3. COMPARED WITH YESTERDAY
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            Today is <span className="text-rose-600">4.1% worse</span> than yesterday.
          </p>
        </div>
        <span className="text-xs font-mono font-bold text-rose-600 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-lg">
          ↓ {Math.abs(diffKg).toLocaleString()} kg ({diffPct}%)
        </span>
      </div>

      {/* 1-to-1 Comparison Cards */}
      <div className="grid grid-cols-2 gap-3 text-center">
        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
          <div className="text-xs text-slate-500 font-medium">Yesterday Produced</div>
          <div className="text-xl font-extrabold text-slate-900 font-mono mt-1">
            {yesterdayKg.toLocaleString()} kg
          </div>
        </div>

        <div className="bg-rose-50/60 p-3.5 rounded-xl border border-rose-200">
          <div className="text-xs text-rose-700 font-medium">Today Produced</div>
          <div className="text-xl font-extrabold text-rose-700 font-mono mt-1">
            {todayKg.toLocaleString()} kg
          </div>
        </div>
      </div>

      {/* Key Drivers for the Drop */}
      <div className="space-y-2 pt-1">
        <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Main reasons for drop:</div>
        <div className="grid grid-cols-3 gap-2 text-xs font-medium">
          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-center">
            <span className="text-slate-500 block text-[11px]">Downtime</span>
            <span className="text-rose-600 font-bold font-mono">↑ 112 min</span>
          </div>

          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-center">
            <span className="text-slate-500 block text-[11px]">Efficiency</span>
            <span className="text-rose-600 font-bold font-mono">↓ 3.2 pts</span>
          </div>

          <div className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-center">
            <span className="text-slate-500 block text-[11px]">Power Events</span>
            <span className="text-rose-600 font-bold font-mono">↑ 2 events</span>
          </div>
        </div>
      </div>
    </Card>
  );
};
