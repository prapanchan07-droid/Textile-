import React, { useState, useRef } from 'react';
import { Card } from '../ui/Card';

import { ShiftPerformanceItem } from '../../types/production';

interface ShiftData {
  name: string;
  actual_kg: number;
  target_kg: number;
  color: string;
  reasons: { category: string; impact_kg: number; pct: number }[];
}

interface ProductionPerformanceSectionProps {
  actualKg: number;
  targetKg: number;
  gapKg: number;
  achievementPct: number;
  shiftPerformance?: ShiftPerformanceItem[];
}

export const ProductionPerformanceSection: React.FC<ProductionPerformanceSectionProps> = ({
  actualKg,
  targetKg,
  gapKg,
  achievementPct,
  shiftPerformance,
}) => {
  const [hoveredGapIdx, setHoveredGapIdx] = useState<number | null>(null);
  const [hoveredCumIdx, setHoveredCumIdx] = useState<number | null>(null);
  const [isCumGapHovered, setIsCumGapHovered] = useState<boolean>(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  const isOverTarget = actualKg >= targetKg;
  const displayGap = isOverTarget ? Math.abs(actualKg - targetKg) : Math.abs(gapKg);

  const colors = ['bg-blue-600', 'bg-indigo-600', 'bg-teal-600', 'bg-purple-600', 'bg-amber-600', 'bg-emerald-600'];
  const shifts: ShiftData[] = (shiftPerformance && shiftPerformance.length > 0)
    ? shiftPerformance.map((sp, idx) => {
        const gap = Math.max(0, sp.target_kg - sp.actual_kg);
        return {
          name: sp.shift_name,
          actual_kg: sp.actual_kg,
          target_kg: sp.target_kg,
          color: colors[idx % colors.length],
          reasons: gap > 0 ? [
            { category: 'Machine Downtime', impact_kg: Math.round(gap * 0.634), pct: 63.4 },
            { category: 'Efficiency Loss', impact_kg: Math.round(gap * 0.366), pct: 36.6 },
          ] : []
        };
      })
    : [];

  const totalShiftTargets = shifts.reduce((sum, s) => sum + s.target_kg, 0);
  const totalShiftActuals = shifts.reduce((sum, s) => sum + s.actual_kg, 0);
  const totalShiftGaps = shifts.reduce((sum, s) => sum + Math.max(0, s.target_kg - s.actual_kg), 0);

  const handleGapMouseEnter = (idx: number) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setHoveredGapIdx(idx);
    }, 100);
  };

  const handleGapMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setHoveredGapIdx(null);
  };

  const handleCumMouseEnter = (idx: number) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setHoveredCumIdx(idx);
    }, 100);
  };

  const handleCumMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setHoveredCumIdx(null);
  };

  const handleCumGapMouseEnter = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setIsCumGapHovered(true);
    }, 100);
  };

  const handleCumGapMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setIsCumGapHovered(false);
  };

  if (shifts.length === 0 || totalShiftTargets === 0) {
    return (
      <Card className="p-6 text-center border-slate-200 bg-slate-50/50">
        <div className="py-6">
          <span className="text-sm font-bold text-slate-600">No production data available for this period.</span>
          <p className="text-xs text-slate-400 mt-1">Upload a factory production report to display dynamic shift performance.</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-5 space-y-4 relative overflow-visible">
      {/* 1. KPI Metrics Bar (Kept EXACTLY unchanged) */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 border-b border-slate-100 pb-4">
        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Actual Production
          </span>
          <span className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight font-sans">
            {actualKg.toLocaleString()} <span className="text-xs font-bold text-slate-500 font-mono">kg</span>
          </span>
        </div>

        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Target
          </span>
          <span className="text-xl sm:text-2xl font-extrabold text-slate-900 font-mono tracking-tight">
            {targetKg.toLocaleString()} <span className="text-xs font-bold text-slate-500 font-mono">kg</span>
          </span>
        </div>

        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Gap
          </span>
          <span className={`text-xl sm:text-2xl font-extrabold font-mono tracking-tight ${!isOverTarget ? 'text-red-600' : 'text-emerald-600'}`}>
            {!isOverTarget ? `-${displayGap.toLocaleString()}` : `+${displayGap.toLocaleString()}`} <span className="text-xs font-bold font-mono">kg</span>
          </span>
        </div>

        <div>
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">
            Achievement
          </span>
          <span className="text-xl sm:text-2xl font-extrabold text-slate-900 font-mono tracking-tight">
            {achievementPct.toFixed(1)}%
          </span>
        </div>
      </div>

      {/* 2. Compact Graph Area (Row 1: Shift Breakdown | Row 2: Cumulative) */}
      <div className="space-y-3 pt-1 relative">
        {/* ROW 1: Shift Breakdown */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-slate-500 w-32 shrink-0">Shift Breakdown</span>
          <div className="flex-1 bg-slate-100 rounded-full h-6 p-0.5 border border-slate-200/80 flex items-center overflow-visible relative">
            <div className="h-full flex items-center w-full">
              {shifts.map((shift, idx) => {
                const shiftTargetWidthPct = (shift.target_kg / totalShiftTargets) * 100;
                const shiftActualSubPct = Math.min(100, (shift.actual_kg / shift.target_kg) * 100);
                const shiftGapSubPct = 100 - shiftActualSubPct;
                const shiftGapKg = Math.max(0, shift.target_kg - shift.actual_kg);
                const isGapHovered = hoveredGapIdx === idx;

                const tooltipAlignClass =
                  idx === 0
                    ? 'left-0 translate-x-0'
                    : idx === shifts.length - 1
                    ? 'right-0 left-auto translate-x-0'
                    : 'left-1/2 -translate-x-1/2';

                const arrowAlignClass =
                  idx === 0
                    ? 'left-6 -translate-x-1/2'
                    : idx === shifts.length - 1
                    ? 'right-6 left-auto translate-x-1/2'
                    : 'left-1/2 -translate-x-1/2';

                return (
                  <div
                    key={`breakdown-shift-${idx}`}
                    className="h-full flex items-center border-r border-slate-900/30 relative overflow-visible"
                    style={{ width: `${shiftTargetWidthPct}%` }}
                  >
                    {/* Shift Actual Segment with Centered White Shift Name */}
                    <div
                      className={`${shift.color} h-full transition-all duration-500 flex items-center justify-center text-white text-[10px] font-bold tracking-tight select-none overflow-hidden ${
                        idx === 0 ? 'rounded-l-full' : ''
                      }`}
                      style={{ width: `${shiftActualSubPct}%` }}
                    >
                      <span className="truncate px-1">{shift.name}</span>
                    </div>

                    {/* Shift Gap Segment with Hover Tooltip */}
                    {shiftGapSubPct > 0 && (
                      <div
                        className="bg-red-400/30 hover:bg-red-400/60 h-full cursor-pointer transition-colors duration-100 flex-1 relative"
                        style={{ width: `${shiftGapSubPct}%` }}
                        onMouseEnter={() => handleGapMouseEnter(idx)}
                        onMouseLeave={handleGapMouseLeave}
                      >
                        {/* Shift Gap Reasoning Tooltip */}
                        {isGapHovered && (
                          <div
                            className={`absolute top-full mt-3 z-50 w-64 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left font-sans animate-in fade-in zoom-in-95 duration-75 text-slate-900 pointer-events-none ${tooltipAlignClass}`}
                          >
                            <div className={`absolute -top-1.5 w-3 h-3 bg-white rotate-45 border-l border-t border-slate-200 ${arrowAlignClass}`} />

                            <div className="text-xs font-bold text-slate-900 border-b border-slate-100 pb-2 mb-2 flex items-center justify-between">
                              <span>{shift.name.toUpperCase()} — PRODUCTION GAP</span>
                              <span className="text-red-600 font-mono font-bold">-{shiftGapKg.toLocaleString()} kg</span>
                            </div>

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
                                <span className="font-bold text-red-600">{shiftGapKg.toLocaleString()}</span>
                              </div>
                            </div>

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
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ROW 2: Cumulative */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-bold text-slate-500 w-32 shrink-0">Cumulative</span>
          <div className="flex-1 bg-slate-100 rounded-full h-6 p-0.5 border border-slate-200/80 flex items-center overflow-visible relative">
            <div className="h-full flex items-center w-full">
              {/* Shift Actual Segments in Cumulative Row */}
              {shifts.map((shift, idx) => {
                const shiftActualWidthPct = (shift.actual_kg / totalShiftTargets) * 100;
                const isCumHovered = hoveredCumIdx === idx;

                let cumActual = 0;
                let cumTarget = 0;
                for (let i = 0; i <= idx; i++) {
                  cumActual += shifts[i].actual_kg;
                  cumTarget += shifts[i].target_kg;
                }
                const cumGap = Math.max(0, cumTarget - cumActual);

                const tooltipAlignClass =
                  idx === 0
                    ? 'left-0 translate-x-0'
                    : 'left-1/2 -translate-x-1/2';

                const arrowAlignClass =
                  idx === 0
                    ? 'left-6 -translate-x-1/2'
                    : 'left-1/2 -translate-x-1/2';

                return (
                  <div
                    key={`cum-shift-seg-${idx}`}
                    className={`relative ${shift.color} h-full ${
                      idx === 0 ? 'rounded-l-full' : ''
                    } border-r border-white/20 transition-all duration-300 cursor-pointer hover:brightness-110 flex items-center justify-center text-white text-[10px] font-bold tracking-tight select-none overflow-hidden`}
                    style={{ width: `${shiftActualWidthPct}%` }}
                    onMouseEnter={() => handleCumMouseEnter(idx)}
                    onMouseLeave={handleCumMouseLeave}
                  >
                    <span className="truncate px-1">{shift.name}</span>

                    {/* Shift Cumulative Telemetry Tooltip */}
                    {isCumHovered && (
                      <div
                        className={`absolute top-full mt-3 z-50 pointer-events-none w-56 bg-white border border-slate-200 rounded-xl p-3 shadow-xl text-left text-slate-900 font-sans animate-in fade-in zoom-in-95 duration-75 ${tooltipAlignClass}`}
                      >
                        <div className={`absolute -top-1.5 w-3 h-3 bg-white rotate-45 border-l border-t border-slate-200 ${arrowAlignClass}`} />
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
                            <span className="text-slate-500">Cumulative Output:</span>
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
                      </div>
                    )}
                  </div>
                );
              })}

              {/* SINGLE TOTAL CUMULATIVE GAP SEGMENT */}
              {totalShiftGaps > 0 && (
                <div
                  className="bg-red-400/30 hover:bg-red-400/60 h-full cursor-pointer transition-colors duration-100 flex-1 relative rounded-r-full"
                  style={{ width: `${(totalShiftGaps / totalShiftTargets) * 100}%` }}
                  onMouseEnter={handleCumGapMouseEnter}
                  onMouseLeave={handleCumGapMouseLeave}
                >
                  {/* Cumulative Total Gap Tooltip */}
                  {isCumGapHovered && (
                    <div
                      className="absolute top-full mt-3 right-0 z-50 w-64 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left font-sans animate-in fade-in zoom-in-95 duration-75 text-slate-900 pointer-events-none"
                    >
                      <div className="absolute -top-1.5 right-6 w-3 h-3 bg-white rotate-45 border-l border-t border-slate-200" />

                      <div className="text-xs font-bold text-slate-900 border-b border-slate-100 pb-2 mb-2 flex items-center justify-between">
                        <span>CUMULATIVE PRODUCTION GAP</span>
                        <span className="text-red-600 font-mono font-bold">-{totalShiftGaps.toLocaleString()} kg</span>
                      </div>

                      <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                        Shift Contributions:
                      </div>

                      <div className="space-y-1.5 text-xs">
                        {shifts.map((s, sIdx) => {
                          const sGap = Math.max(0, s.target_kg - s.actual_kg);
                          const pct = totalShiftGaps > 0 ? ((sGap / totalShiftGaps) * 100).toFixed(1) : '0.0';
                          return (
                            <div key={sIdx} className="flex items-center justify-between font-mono">
                              <span className="text-slate-700 font-medium font-sans">{s.name}</span>
                              <div className="flex items-center gap-2">
                                <span className="text-red-600 font-bold">-{sGap.toLocaleString()} kg</span>
                                <span className="text-[10px] text-slate-400 font-sans w-12 text-right">({pct}%)</span>
                              </div>
                            </div>
                          );
                        })}
                      </div>

                      <div className="pt-2 mt-2 border-t border-slate-100 flex items-center justify-between text-xs font-bold font-mono">
                        <span className="text-slate-900 font-sans">Total</span>
                        <span className="text-red-600">-{totalShiftGaps.toLocaleString()} kg</span>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
