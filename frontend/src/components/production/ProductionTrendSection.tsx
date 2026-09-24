import React, { useState, useRef } from 'react';
import { ProductionTrendPoint } from '../../types/production';
import { Card } from '../ui/Card';

interface ShiftData {
  id: string;
  name: string;
  actual_kg: number;
  target_kg: number;
  color: string;
  reasons: { category: string; impact_kg: number; pct: number }[];
}

interface ProductionTrendSectionProps {
  trendPoints?: ProductionTrendPoint[];
}

export const ProductionTrendSection: React.FC<ProductionTrendSectionProps> = () => {
  const [hoveredShiftGap, setHoveredShiftGap] = useState<number | null>(null);
  const [hoveredCumShift, setHoveredCumShift] = useState<number | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Dynamic Shift Data & Dynamic Loss Reasons
  const shifts: ShiftData[] = [
    {
      id: 'shift_a',
      name: 'Shift A',
      actual_kg: 12450,
      target_kg: 12940,
      color: 'bg-blue-600',
      reasons: [
        { category: 'Machine Downtime', impact_kg: 280, pct: 57.1 },
        { category: 'Efficiency Loss', impact_kg: 140, pct: 28.6 },
        { category: 'Power Events', impact_kg: 70, pct: 14.3 },
      ],
    },
    {
      id: 'shift_b',
      name: 'Shift B',
      actual_kg: 10890,
      target_kg: 11910,
      color: 'bg-indigo-600',
      reasons: [
        { category: 'Machine Downtime', impact_kg: 520, pct: 51.0 },
        { category: 'Efficiency Loss', impact_kg: 280, pct: 27.5 },
        { category: 'Power Events', impact_kg: 140, pct: 13.7 },
        { category: 'Other Factors', impact_kg: 80, pct: 7.8 },
      ],
    },
    {
      id: 'shift_c',
      name: 'Shift C',
      actual_kg: 11280,
      target_kg: 11610,
      color: 'bg-teal-600',
      reasons: [
        { category: 'Machine Downtime', impact_kg: 220, pct: 66.7 },
        { category: 'Efficiency Loss', impact_kg: 110, pct: 33.3 },
      ],
    },
  ];

  const totalActual = shifts.reduce((sum, s) => sum + s.actual_kg, 0);
  const totalTarget = shifts.reduce((sum, s) => sum + s.target_kg, 0);
  const totalGap = Math.max(0, totalTarget - totalActual);

  const handleGapMouseEnter = (idx: number) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setHoveredShiftGap(idx);
    }, 100); // 100ms fast tooltip response
  };

  const handleGapMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setHoveredShiftGap(null);
  };

  const handleCumMouseEnter = (idx: number) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setHoveredCumShift(idx);
    }, 100);
  };

  const handleCumMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setHoveredCumShift(null);
  };

  return (
    <Card className="p-5 space-y-6 overflow-visible relative">
      {/* Header & Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            2. PRODUCTION TREND
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            Today&apos;s Shift Performance &amp; Cumulative Progress
          </p>
        </div>

        {/* Minimal Legend */}
        <div className="flex items-center gap-4 text-xs font-bold text-slate-700">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600"></span>
            <span>Shift A</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-indigo-600"></span>
            <span>Shift B</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-teal-600"></span>
            <span>Shift C</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-red-400"></span>
            <span className="text-red-600">Gap</span>
          </div>
        </div>
      </div>

      {/* 1. SHIFT-BY-SHIFT CONTINUOUS BAR (TOP VISUALIZATION) */}
      <div className="space-y-3">
        <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
          Shift-by-Shift Continuous Bar
        </span>

        {/* Inline Shift Labels above the Bar (No Cards) */}
        <div className="w-full flex items-center justify-between text-xs font-bold text-slate-800 px-1 font-mono">
          {shifts.map((shift) => {
            const achPct = ((shift.actual_kg / shift.target_kg) * 100).toFixed(1);
            return (
              <div key={shift.id} className="flex flex-col items-center">
                <span className="font-extrabold text-slate-900 font-sans">{shift.name}</span>
                <span className="text-[11px] text-slate-600 font-mono">
                  {shift.actual_kg.toLocaleString()} / {shift.target_kg.toLocaleString()} kg
                </span>
                <span className="text-[10px] text-blue-600 font-bold">{achPct}%</span>
              </div>
            );
          })}
        </div>

        {/* ONE SINGLE CONTINUOUS HORIZONTAL PRODUCTION BAR */}
        <div className="relative w-full">
          <div className="w-full bg-slate-100 rounded-xl h-8 sm:h-9 border border-slate-300/80 flex items-center overflow-visible relative p-0.5 shadow-xs">
            {shifts.map((shift, idx) => {
              const shiftSectionWidthPct = (shift.target_kg / totalTarget) * 100;
              const shiftGap = Math.max(0, shift.target_kg - shift.actual_kg);
              const actualSubPct = Math.min(100, (shift.actual_kg / shift.target_kg) * 100);
              const gapSubPct = 100 - actualSubPct;
              const isGapHovered = hoveredShiftGap === idx;

              return (
                <div
                  key={shift.id}
                  className="relative h-full flex items-center"
                  style={{ width: `${shiftSectionWidthPct}%` }}
                >
                  {/* Actual Production Fill (Strong Shift Color) */}
                  <div
                    className={`${shift.color} h-full ${
                      idx === 0 ? 'rounded-l-lg' : ''
                    } flex items-center justify-center transition-all duration-500`}
                    style={{ width: `${actualSubPct}%` }}
                  >
                    <span className="text-[10px] font-extrabold text-white font-mono truncate px-1 select-none">
                      {shift.actual_kg.toLocaleString()} kg
                    </span>
                  </div>

                  {/* Dim Red Gap Segment (Low-opacity red when Actual < Target) */}
                  {shiftGap > 0 && (
                    <div
                      className="bg-red-400/30 hover:bg-red-400/60 h-full cursor-pointer transition-colors duration-100 flex items-center justify-center"
                      style={{ width: `${gapSubPct}%` }}
                      onMouseEnter={() => handleGapMouseEnter(idx)}
                      onMouseLeave={handleGapMouseLeave}
                    >
                      <span className="text-[9px] font-bold text-red-700 font-mono truncate px-0.5 select-none">
                        -{shiftGap}
                      </span>
                    </div>
                  )}

                  {/* Target Breakpoint Tick Line */}
                  <div className="absolute right-0 top-0 bottom-0 w-0.5 bg-slate-900 z-10" />

                  {/* Independent Fast Tooltip for Hovered Shift Gap (~100ms response) */}
                  {isGapHovered && (
                    <div
                      className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 z-50 w-64 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left font-sans animate-in fade-in zoom-in-95 duration-75"
                      onMouseEnter={() => setHoveredShiftGap(idx)}
                      onMouseLeave={handleGapMouseLeave}
                    >
                      {/* Header */}
                      <div className="text-xs font-bold text-slate-900 border-b border-slate-100 pb-2 mb-2 flex items-center justify-between">
                        <span>{shift.name.toUpperCase()} — PRODUCTION GAP</span>
                        <span className="text-red-600 font-mono font-bold">-{shiftGap.toLocaleString()} kg</span>
                      </div>

                      {/* Summary Metrics */}
                      <div className="grid grid-cols-3 gap-1 text-[11px] font-mono text-center bg-slate-50 p-2 rounded-lg mb-2">
                        <div>
                          <span className="text-[9px] text-slate-400 block font-sans">Target</span>
                          <span className="font-bold text-slate-900">{shift.target_kg.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-[9px] text-slate-400 block font-sans">Actual</span>
                          <span className="font-bold text-blue-600">{shift.actual_kg.toLocaleString()}</span>
                        </div>
                        <div>
                          <span className="text-[9px] text-red-500 block font-sans">Gap</span>
                          <span className="font-bold text-red-600">{shiftGap.toLocaleString()}</span>
                        </div>
                      </div>

                      {/* Internal Scrolling Contributors List */}
                      <div className="max-h-36 overflow-y-auto space-y-1.5 pr-1">
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
                          Main Contributors:
                        </span>
                        {shift.reasons.map((r, rIdx) => (
                          <div key={rIdx} className="flex items-center justify-between text-xs">
                            <span className="text-slate-700 font-medium">{r.category}</span>
                            <div className="font-mono font-bold text-red-600 flex items-center gap-1">
                              <span>-{r.impact_kg} kg</span>
                              <span className="text-[10px] text-slate-400">({r.pct}%)</span>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Tooltip Pointer */}
                      <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rotate-45 border-r border-b border-slate-200" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Subtitle Target Markers below the Bar */}
          <div className="w-full flex items-center justify-between text-[10px] font-extrabold text-slate-500 font-mono pt-1.5 px-1">
            {shifts.map((shift) => (
              <div key={`target-${shift.id}`} className="text-center">
                <span>↑ Target {shift.name}: {shift.target_kg.toLocaleString()} kg</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 2. SECOND CONTINUOUS BAR — CUMULATIVE TODAY */}
      <div className="space-y-3 pt-2 border-t border-slate-100">
        <div className="flex items-center justify-between">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Cumulative Today Progress
          </span>
          <div className="text-xs font-mono space-x-3">
            <span className="text-slate-700 font-semibold">
              Actual: <strong className="text-slate-900 font-extrabold">{totalActual.toLocaleString()} kg</strong>
            </span>
            <span className="text-slate-700 font-semibold">
              Target: <strong className="text-slate-900 font-extrabold">{totalTarget.toLocaleString()} kg</strong>
            </span>
            <span className="text-red-600 font-bold">
              Gap: -{totalGap.toLocaleString()} kg
            </span>
          </div>
        </div>

        {/* Single Continuous Cumulative Bar */}
        <div className="relative w-full">
          <div className="w-full bg-slate-100 rounded-xl h-8 sm:h-9 p-0.5 border border-slate-200 flex items-center overflow-visible relative shadow-xs">
            {shifts.map((shift, idx) => {
              const cumPct = (shift.actual_kg / totalTarget) * 100;
              const isCumHovered = hoveredCumShift === idx;

              // Calculate cumulative totals up to current shift
              let cumActual = 0;
              let cumTarget = 0;
              for (let i = 0; i <= idx; i++) {
                cumActual += shifts[i].actual_kg;
                cumTarget += shifts[i].target_kg;
              }
              const cumGap = Math.max(0, cumTarget - cumActual);

              return (
                <div
                  key={`cum-${shift.id}`}
                  className={`relative ${shift.color} h-full transition-all duration-300 cursor-pointer flex items-center justify-center ${
                    idx === 0 ? 'rounded-l-lg' : ''
                  } border-r border-white/20 hover:brightness-110`}
                  style={{ width: `${cumPct}%` }}
                  onMouseEnter={() => handleCumMouseEnter(idx)}
                  onMouseLeave={handleCumMouseLeave}
                >
                  <span className="text-[10px] font-bold text-white font-mono truncate px-1 select-none">
                    {shift.name}
                  </span>

                  {/* Fast Cumulative Hover Tooltip */}
                  {isCumHovered && (
                    <div
                      className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 z-50 pointer-events-none w-56 bg-white border border-slate-200 rounded-xl p-3 shadow-xl text-left text-slate-900 font-sans animate-in fade-in zoom-in-95 duration-75"
                    >
                      <div className="text-xs font-bold border-b border-slate-100 pb-1.5 mb-2 flex justify-between items-center">
                        <span>{shift.name.toUpperCase()} CUMULATIVE</span>
                        <span className="text-blue-600 font-mono">{shift.actual_kg.toLocaleString()} kg</span>
                      </div>
                      <div className="space-y-1 text-[11px] font-mono">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Shift Output:</span>
                          <span className="font-bold">{shift.actual_kg.toLocaleString()} kg</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Cumulative Production:</span>
                          <span className="font-bold text-slate-900">{cumActual.toLocaleString()} kg</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Cumulative Target:</span>
                          <span className="font-bold text-slate-900">{cumTarget.toLocaleString()} kg</span>
                        </div>
                        <div className="flex justify-between pt-1 border-t border-slate-100 text-red-600 font-bold">
                          <span>Cumulative Gap:</span>
                          <span>-{cumGap.toLocaleString()} kg</span>
                        </div>
                      </div>
                      <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rotate-45 border-r border-b border-slate-200" />
                    </div>
                  )}
                </div>
              );
            })}

            {/* Dim Red Cumulative Gap Segment */}
            {totalGap > 0 && (
              <div
                className="flex-1 bg-red-400/30 h-full flex items-center justify-center rounded-r-lg border-l border-red-300 cursor-pointer"
                title={`Cumulative Gap: -${totalGap.toLocaleString()} kg`}
              >
                <span className="text-[10px] font-bold text-red-700 font-mono truncate px-1 select-none">
                  Gap: -{totalGap.toLocaleString()} kg
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
};
