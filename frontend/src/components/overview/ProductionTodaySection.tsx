import React, { useState, useRef } from 'react';
import { ProductionSummary, ProductionVariance } from '../../types/overview';
import { Card } from '../ui/Card';

interface ProductionTodaySectionProps {
  summary: ProductionSummary;
  variance: ProductionVariance;
}

export const ProductionTodaySection: React.FC<ProductionTodaySectionProps> = ({
  summary,
  variance,
}) => {
  const [showGapTooltip, setShowGapTooltip] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const isOverTarget = summary.actual_kg >= summary.target_kg;
  const gapKg = Math.max(0, summary.target_kg - summary.actual_kg);

  // Scaled percentage calculations for bullet track
  // Target is anchored near 92% of the bar width so the target label never overflows on the right
  const targetPct = 90;
  const maxScaleVal = summary.target_kg > 0 ? summary.target_kg / (targetPct / 100) : 1;
  const actualPct = Math.min(100, (summary.actual_kg / maxScaleVal) * 100);

  const handleMouseEnter = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setShowGapTooltip(true);
    }, 100); // 100ms fast tooltip response
  };

  const handleMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setShowGapTooltip(false);
  };

  return (
    <Card className="p-5 space-y-4">
      {/* 1. Header Row */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <span className="text-[11px] font-extrabold uppercase tracking-wider text-slate-400 font-sans">
          1. PRODUCTION TODAY
        </span>

        {/* Priority 4: 93.6% Achieved */}
        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 border border-slate-200/80 rounded-lg text-xs font-bold text-slate-900 font-mono">
          <span>{summary.achievement_pct.toFixed(1)}% ACHIEVED</span>
        </div>
      </div>

      {/* Main Bullet Visualization Area */}
      <div className="space-y-4 pt-1">
        {/* Priority 1: Actual Production (Most Prominent KPI) */}
        <div>
          <div className="text-3xl sm:text-4xl font-black text-slate-900 tracking-tight">
            {summary.actual_kg.toLocaleString()}{' '}
            <span className="text-base font-bold text-slate-500 font-mono">kg</span>
          </div>
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mt-0.5">
            ACTUAL PRODUCTION
          </div>
        </div>

        {/* Bullet-Style Target Track with Hover Tooltip */}
        <div className="relative w-full pt-1 pb-6">
          {/* Fast Custom Tooltip on Hovering Target Marker or Gap Track */}
          {showGapTooltip && !isOverTarget && gapKg > 0 && (
            <div
              className="absolute -top-10 z-50 pointer-events-none whitespace-nowrap bg-white text-red-600 text-xs font-bold font-mono px-3.5 py-1.5 rounded-lg shadow-lg border border-red-200 transition-opacity duration-100"
              style={{
                left: `${(actualPct + targetPct) / 2}%`,
                transform: 'translateX(-50%)',
              }}
            >
              Gap: {gapKg.toLocaleString()} kg needed to reach target
              <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-white rotate-45 border-r border-b border-red-200" />
            </div>
          )}

          {/* Bullet Track Base */}
          <div
            className="w-full bg-slate-100 rounded-full h-3 sm:h-3.5 border border-slate-200/90 relative flex items-center cursor-pointer overflow-visible"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            {/* Primary Blue Actual Production Fill Bar */}
            <div
              className="bg-blue-600 h-full rounded-l-full transition-all duration-500"
              style={{ width: `${actualPct}%` }}
            />

            {/* Subtle Red Gap Fill Segment between Actual and Target */}
            {!isOverTarget && targetPct > actualPct && (
              <div
                className="bg-red-100/90 h-full border-y border-red-200 transition-all duration-500"
                style={{
                  width: `${targetPct - actualPct}%`,
                }}
              />
            )}

            {/* Target Bullet Pin Marker (Priority 3: Target Indicator) */}
            <div
              className="absolute top-1/2 -translate-y-1/2 z-20 flex flex-col items-center"
              style={{ left: `${targetPct}%`, transform: 'translate(-50%, -50%)' }}
            >
              <div className="w-4 h-4 bg-slate-900 border-2 border-white rounded-full shadow-md shrink-0" />
            </div>
          </div>

          {/* Target Value Label below Bullet Pin */}
          <div
            className="absolute top-6 z-10 text-right whitespace-nowrap"
            style={{ left: `${targetPct}%`, transform: 'translateX(-85%)' }}
          >
            <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              TARGET
            </div>
            <div className="text-xs sm:text-sm font-extrabold text-slate-900 font-mono">
              {summary.target_kg.toLocaleString()} kg
            </div>
          </div>
        </div>

        {/* Priority 2: 2,380 kg SHORT Callout (Centered Management Issue) */}
        <div className="flex items-center justify-center pt-2">
          {!isOverTarget ? (
            <div className="inline-flex items-center gap-1.5 bg-red-50 text-red-700 border border-red-200/90 px-4 py-1.5 rounded-full text-xs font-extrabold font-mono shadow-xs">
              <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></span>
              <span>{gapKg.toLocaleString()} kg SHORT</span>
              <span className="text-[11px] font-normal text-red-500 font-sans">
                (-{Math.abs(variance.variance_pct).toFixed(1)}%)
              </span>
            </div>
          ) : (
            <div className="inline-flex items-center gap-1.5 bg-emerald-50 text-emerald-700 border border-emerald-200 px-4 py-1.5 rounded-full text-xs font-bold font-mono">
              <span>↑ {(summary.actual_kg - summary.target_kg).toLocaleString()} kg ABOVE TARGET</span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
