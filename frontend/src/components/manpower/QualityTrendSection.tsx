import React, { useState } from 'react';
import { QualityTrendPoint } from '../../types/manpowerQuality';
import { Card } from '../ui/Card';

interface QualityTrendSectionProps {
  trendsByParam: Record<string, QualityTrendPoint[]>;
}

const PARAM_OPTIONS = [
  { id: 'Thick/Km', label: 'Thick Places (Thick/Km)' },
  { id: 'U%', label: 'Unevenness (U%)' },
  { id: 'Neps/Km', label: 'Neps (Neps/Km)' },
  { id: 'Count CV', label: 'Count CV %' },
  { id: 'Strength CV', label: 'Strength CV %' },
];

export const QualityTrendSection: React.FC<QualityTrendSectionProps> = ({ trendsByParam }) => {
  const [selectedParam, setSelectedParam] = useState<string>('Thick/Km');
  const [selectedPeriod, setSelectedPeriod] = useState<'SEVEN_DAYS' | 'THIS_MONTH'>('THIS_MONTH');
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  const activePoints = trendsByParam[selectedParam] || trendsByParam['Thick/Km'] || [];
  const limitValue = activePoints[0]?.limit || 40;
  const maxVal = Math.max(...activePoints.map((p) => Math.max(p.value, p.limit)), limitValue) * 1.15;

  return (
    <Card className="space-y-6 p-6 overflow-visible">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            6. QUALITY TREND
          </h2>
          <p className="text-base font-bold text-slate-900 mt-0.5">
            Track selected quality parameter over time vs specification limit
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Parameter Dropdown */}
          <div className="flex items-center gap-2 bg-slate-100 p-1.5 px-3 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700">
            <span>Parameter:</span>
            <select
              value={selectedParam}
              onChange={(e) => setSelectedParam(e.target.value)}
              className="bg-transparent font-bold text-slate-900 font-sans focus:outline-none cursor-pointer"
            >
              {PARAM_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          {/* Period Selector */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-bold">
            {(
              [
                { id: 'SEVEN_DAYS', label: '7 Days' },
                { id: 'THIS_MONTH', label: 'This Month' },
              ] as const
            ).map((r) => (
              <button
                key={r.id}
                onClick={() => setSelectedPeriod(r.id)}
                className={`px-3 py-1 rounded-md transition-all ${
                  selectedPeriod === r.id
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-white'
                }`}
              >
                {r.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Chart Viewport */}
      <div className="relative pt-3 pb-1">
        {/* Specification Limit Line */}
        <div
          className="absolute left-0 right-0 border-b-2 border-rose-500 border-dashed z-10 pointer-events-none flex justify-end pr-2"
          style={{
            bottom: `${(limitValue / maxVal) * 100}%`,
          }}
        >
          <span className="text-[10px] font-bold text-rose-600 bg-white/90 px-1 rounded -translate-y-3 font-mono">
            Limit: {limitValue}
          </span>
        </div>

        {/* Bars Container */}
        <div className="flex items-end justify-around h-48 border-b border-slate-200 px-4">
          {activePoints.map((point, idx) => {
            const heightPct = (point.value / maxVal) * 100;
            const isExceeded = point.value > point.limit;
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
                  className={`w-4 sm:w-6 rounded-t-sm transition-all duration-150 ${
                    isExceeded
                      ? 'bg-rose-600 group-hover:bg-rose-700 shadow-sm shadow-rose-500/20'
                      : 'bg-blue-600 group-hover:bg-blue-700'
                  }`}
                  style={{ height: `${heightPct}%` }}
                />

                {/* Instant Custom Tooltip Overlay */}
                {isHovered && (
                  <div className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 z-50 pointer-events-none w-56 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left animate-in fade-in zoom-in-95 duration-75 font-sans">
                    <div className="border-b border-slate-100 pb-1.5 mb-2 flex justify-between items-center text-xs font-bold text-slate-900">
                      <span>{point.date_label}</span>
                      <span className="font-mono text-slate-500">{selectedParam}</span>
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Observed Value:</span>
                        <span className={`font-mono font-bold ${isExceeded ? 'text-rose-600' : 'text-slate-900'}`}>
                          {point.value}
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Spec Limit:</span>
                        <span className="font-mono font-semibold text-slate-600">{point.limit}</span>
                      </div>

                      <div className="border-t border-slate-100 pt-1.5 flex justify-between items-center">
                        <span className="text-slate-500">Status:</span>
                        <span className={`font-mono font-bold ${isExceeded ? 'text-rose-600' : 'text-emerald-600'}`}>
                          {isExceeded ? 'EXCEEDED' : 'WITHIN LIMIT'}
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
