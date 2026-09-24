import React, { useState } from 'react';
import { RevenueTrendPoint } from '../../types/revenueLoss';
import { Card } from '../ui/Card';

interface RevenueTrendSectionProps {
  trend: RevenueTrendPoint[];
}

export const RevenueTrendSection: React.FC<RevenueTrendSectionProps> = ({ trend }) => {
  const [selectedRange, setSelectedRange] = useState<'TODAY' | 'SEVEN_DAYS' | 'THIS_MONTH'>('THIS_MONTH');
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const sampleToday: RevenueTrendPoint[] = [
    { date_label: 'Today (Sep 22)', revenue_lakhs: 4.2, previous_lakhs: 4.8, change_pct: -12.5 },
  ];

  const activePoints = selectedRange === 'TODAY' ? sampleToday : trend;
  const maxVal = Math.max(...activePoints.map((p) => Math.max(p.revenue_lakhs, p.previous_lakhs)), 5.0) * 1.15;

  return (
    <Card className="space-y-6 p-6 overflow-visible">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            2. REVENUE TREND
          </h2>
          <p className="text-base font-bold text-slate-900 mt-0.5">
            Sales revenue over time
          </p>
        </div>

        {/* Range Selector Pill */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 self-start sm:self-auto text-xs font-bold">
          {(
            [
              { id: 'TODAY', label: 'Today' },
              { id: 'SEVEN_DAYS', label: '7 Days' },
              { id: 'THIS_MONTH', label: 'This Month' },
            ] as const
          ).map((r) => (
            <button
              key={r.id}
              onClick={() => {
                setSelectedRange(r.id);
                setHoveredIdx(null);
              }}
              className={`px-3 py-1 rounded-md transition-all ${
                selectedRange === r.id
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white'
              }`}
            >
              {r.label}
            </button>
          ))}
        </div>
      </div>

      {/* Vertical Bar Chart Viewport */}
      <div className="relative pt-2 pb-1">
        <div className="flex items-end justify-around h-48 border-b border-slate-200 px-4">
          {activePoints.map((point, idx) => {
            const heightPct = (point.revenue_lakhs / maxVal) * 100;
            const isHovered = hoveredIdx === idx;

            return (
              <div
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className="relative flex flex-col items-center h-full justify-end cursor-pointer group flex-1 max-w-[60px]"
              >
                {/* Vertical Bar */}
                <div
                  className="w-4 sm:w-6 bg-blue-600 rounded-t-sm group-hover:bg-blue-700 transition-colors shadow-sm"
                  style={{ height: `${heightPct}%` }}
                />

                {/* Instant Custom Tooltip Overlay */}
                {isHovered && (
                  <div className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 z-50 pointer-events-none w-56 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left animate-in fade-in zoom-in-95 duration-75 font-sans">
                    <div className="border-b border-slate-100 pb-1.5 mb-2 font-bold text-xs text-slate-900">
                      {point.date_label}
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Revenue:</span>
                        <span className="font-mono font-bold text-blue-600">
                          ₹{point.revenue_lakhs.toFixed(1)} L
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Previous Period:</span>
                        <span className="font-mono font-semibold text-slate-600">
                          ₹{point.previous_lakhs.toFixed(1)} L
                        </span>
                      </div>

                      <div className="border-t border-slate-100 pt-1.5 flex justify-between items-center">
                        <span className="text-slate-500">Period Change:</span>
                        <span
                          className={`font-mono font-bold ${
                            point.change_pct < 0 ? 'text-rose-600' : 'text-emerald-600'
                          }`}
                        >
                          {point.change_pct < 0 ? '' : '+'}{point.change_pct.toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* Tooltip pointer arrow */}
                    <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rotate-45 border-r border-b border-slate-200" />
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* Date Labels */}
        <div className="flex justify-around pt-2 text-[11px] font-bold text-slate-500 font-mono">
          {activePoints.map((point, idx) => (
            <div key={idx} className="text-center flex-1 max-w-[60px]">
              {point.date_label}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
