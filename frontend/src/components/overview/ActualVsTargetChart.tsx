import React from 'react';
import { BarChart2, Info } from 'lucide-react';
import { ProductionVariance } from '../../types/overview';
import { Card } from '../ui/Card';

interface ActualVsTargetChartProps {
  variance: ProductionVariance;
}

export const ActualVsTargetChart: React.FC<ActualVsTargetChartProps> = ({ variance }) => {
  const maxVal = Math.max(variance.target_kg, variance.actual_kg) * 1.1;
  const targetWidthPct = (variance.target_kg / maxVal) * 100;
  const actualWidthPct = (variance.actual_kg / maxVal) * 100;

  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between border-b border-factory-border pb-3">
        <div className="flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-factory-accent" />
          <h3 className="font-bold text-white text-base tracking-wide">SECTION 2 — ACTUAL VS TARGET PRODUCTION</h3>
        </div>
        <span className="text-xs text-slate-400 font-mono">Scale: 0 - {Math.round(maxVal).toLocaleString()} kg</span>
      </div>

      <div className="space-y-5 py-2">
        {/* Target Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-slate-300">TARGET PRODUCTION</span>
            <span className="text-white font-mono">{variance.target_kg.toLocaleString()} kg</span>
          </div>
          <div className="w-full bg-factory-surface rounded-full h-7 border border-factory-border p-1">
            <div
              className="bg-slate-500 rounded-full h-full transition-all duration-500 flex items-center justify-end pr-3 text-[11px] font-bold text-white shadow-sm"
              style={{ width: `${targetWidthPct}%` }}
            >
              Target (100%)
            </div>
          </div>
        </div>

        {/* Actual Bar */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="text-slate-300">ACTUAL PRODUCTION</span>
            <span className="text-amber-400 font-mono">{variance.actual_kg.toLocaleString()} kg</span>
          </div>
          <div className="w-full bg-factory-surface rounded-full h-7 border border-factory-border p-1">
            <div
              className="bg-gradient-to-r from-amber-600 to-amber-500 rounded-full h-full transition-all duration-500 flex items-center justify-end pr-3 text-[11px] font-bold text-white shadow-sm"
              style={{ width: `${actualWidthPct}%` }}
            >
              Actual ({((variance.actual_kg / variance.target_kg) * 100).toFixed(1)}%)
            </div>
          </div>
        </div>

        {/* Variance Display Callout */}
        <div className="bg-factory-surface p-3.5 rounded-xl border border-rose-500/30 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2">
            <Info className="w-4 h-4 text-rose-400 shrink-0" />
            <span className="text-slate-300">Variance (Target - Actual):</span>
          </div>
          <div className="font-mono font-bold text-rose-400 text-sm">
            {variance.variance_kg.toLocaleString()} kg ({variance.variance_pct}%)
          </div>
        </div>
      </div>
    </Card>
  );
};
