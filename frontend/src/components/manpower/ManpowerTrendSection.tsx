import React, { useState } from 'react';
import { ManpowerTrendPoint } from '../../types/manpowerQuality';
import { Card } from '../ui/Card';

interface ManpowerTrendSectionProps {
  trend: ManpowerTrendPoint[];
}

export const ManpowerTrendSection: React.FC<ManpowerTrendSectionProps> = ({ trend }) => {
  const [selectedRange, setSelectedRange] = useState<'TODAY' | 'SEVEN_DAYS' | 'THIS_MONTH'>('THIS_MONTH');
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const sampleToday: ManpowerTrendPoint[] = [
    { date_label: 'Today (Sep 22)', required: 1250, available: 1180, shortage: 70, attendance_pct: 94.4 },
  ];

  const activePoints = selectedRange === 'TODAY' ? sampleToday : trend;
  const maxVal = 1400;

  return (
    <Card className="space-y-6 p-6 overflow-visible">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            3. MANPOWER TREND
          </h2>
          <p className="text-base font-bold text-slate-900 mt-0.5">
            Required vs Available workforce over time
          </p>
        </div>

        {/* Range Selector Pill */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 self-start sm:self-auto text-xs">
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
              className={`px-3 py-1 rounded-md font-bold transition-all ${
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

      {/* Vertical Grouped Chart Viewport */}
      <div className="relative pt-2 pb-1">
        <div className="flex items-end justify-around h-48 border-b border-slate-200 px-4">
          {activePoints.map((point, idx) => {
            const reqPct = (point.required / maxVal) * 100;
            const availPct = (point.available / maxVal) * 100;
            const isHovered = hoveredIdx === idx;

            return (
              <div
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className="relative flex flex-col items-center h-full justify-end cursor-pointer group flex-1 max-w-[70px]"
              >
                {/* Grouped Bars */}
                <div className="flex items-end gap-1.5 h-full w-full justify-center">
                  {/* Required Bar (Neutral Slate) */}
                  <div
                    className="w-3.5 sm:w-4 bg-slate-300 rounded-t-sm group-hover:bg-slate-400 transition-colors"
                    style={{ height: `${reqPct}%` }}
                  />
                  {/* Available Bar (Primary Blue) */}
                  <div
                    className="w-3.5 sm:w-4 bg-blue-600 rounded-t-sm group-hover:bg-blue-700 transition-colors"
                    style={{ height: `${availPct}%` }}
                  />
                </div>

                {/* Instant Custom Tooltip Overlay */}
                {isHovered && (
                  <div className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 z-50 pointer-events-none w-56 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left animate-in fade-in zoom-in-95 duration-75 font-sans">
                    <div className="border-b border-slate-100 pb-1.5 mb-2 flex justify-between items-center text-xs font-bold text-slate-900">
                      <span>{point.date_label}</span>
                      <span className="font-mono text-blue-700">{point.attendance_pct}%</span>
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500 flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-slate-400 inline-block" />
                          Required:
                        </span>
                        <span className="font-mono font-bold text-slate-900">{point.required}</span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-slate-500 flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full bg-blue-600 inline-block" />
                          Available:
                        </span>
                        <span className="font-mono font-bold text-blue-600">{point.available}</span>
                      </div>

                      <div className="border-t border-slate-100 pt-1.5 flex justify-between items-center">
                        <span className="text-slate-500">Shortage:</span>
                        <span className="font-mono font-bold text-rose-600">
                          {point.shortage > 0 ? `-${point.shortage} workers` : 'Sufficient'}
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
            <div key={idx} className="text-center flex-1 max-w-[70px]">
              {point.date_label}
            </div>
          ))}
        </div>
      </div>

      {/* Minimal Legend */}
      <div className="flex items-center justify-center gap-6 border-t border-slate-100 pt-4 text-xs font-semibold text-slate-600">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-sm bg-slate-300 inline-block" />
          <span>Required Workforce</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-sm bg-blue-600 inline-block shadow-sm" />
          <span>Available Workforce</span>
        </div>
      </div>
    </Card>
  );
};
