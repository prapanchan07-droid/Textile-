import React, { useState } from 'react';
import { ProductionComparisonData } from '../../types/production';
import { Card } from '../ui/Card';

interface ProductionComparisonSectionProps {
  comparison: ProductionComparisonData;
}

export const ProductionComparisonSection: React.FC<ProductionComparisonSectionProps> = ({
  comparison,
}) => {
  const [refPeriod, setRefPeriod] = useState<string>('Yesterday');

  return (
    <Card className="space-y-4 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            6. COMPARISON
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            Production Comparison vs Reference Period
          </p>
        </div>

        {/* Comparison Selector */}
        <div className="flex items-center gap-1.5 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs">
          <span className="text-slate-500 font-bold px-1">Compare:</span>
          {(['Yesterday', 'Previous Shift', 'Previous Week', 'Previous Month'] as const).map((p) => (
            <button
              key={p}
              onClick={() => setRefPeriod(p)}
              className={`px-2.5 py-1 rounded font-bold transition-all ${
                refPeriod === p
                  ? 'bg-slate-900 text-white shadow-sm'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white'
              }`}
            >
              {p}
            </button>
          ))}
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase">{refPeriod} Produced</span>
          <div className="text-xl font-extrabold text-slate-900 font-mono mt-1">
            {comparison.reference_kg.toLocaleString()} kg
          </div>
        </div>

        <div className="bg-rose-50/60 p-3.5 rounded-xl border border-rose-200 text-center">
          <span className="text-[10px] text-rose-700 font-bold uppercase">Today Produced</span>
          <div className="text-xl font-extrabold text-rose-700 font-mono mt-1">
            {comparison.current_kg.toLocaleString()} kg
          </div>
        </div>

        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200 text-center">
          <span className="text-[10px] text-slate-400 font-bold uppercase">Difference</span>
          <div className="text-xl font-extrabold text-rose-600 font-mono mt-1">
            ↓ {Math.abs(comparison.difference_kg).toLocaleString()} kg ({comparison.difference_pct}%)
          </div>
        </div>
      </div>

      <div className="bg-slate-900 text-white p-3.5 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs border border-slate-800 shadow-sm">
        <span className="text-slate-400 font-semibold">
          Main reason for change vs {refPeriod}:
        </span>
        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-rose-500/20 border border-rose-500/40 text-rose-300 font-extrabold text-xs uppercase tracking-wider shadow-sm self-start sm:self-auto">
          <span className="w-2 h-2 rounded-full bg-rose-400 shrink-0" />
          {comparison.main_reason}
        </span>
      </div>
    </Card>
  );
};
