import React from 'react';
import { RefreshCw, ArrowUpRight, ArrowDownRight, Minus, Grid } from 'lucide-react';
import { PeriodComparisonMetric, ComparisonPeriod } from '../../types/overview';
import { Card } from '../ui/Card';

interface WhatChangedComparisonProps {
  comparisonMetrics: PeriodComparisonMetric[];
  selectedComparison: ComparisonPeriod;
}

export const WhatChangedComparison: React.FC<WhatChangedComparisonProps> = ({
  comparisonMetrics,
  selectedComparison,
}) => {
  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <Grid className="w-5 h-5 text-emerald-600" />
            <h3 className="font-bold text-slate-900 text-base">Period Variance Matrix</h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">Comparative shift metrics over consecutive operational periods</p>
        </div>
        <span className="text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-lg">
          N=5 Indicators
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200 text-slate-400 font-bold uppercase tracking-wider text-[10px]">
              <th className="py-2.5 px-3">Metric</th>
              <th className="py-2.5 px-3">Current</th>
              <th className="py-2.5 px-3">Previous</th>
              <th className="py-2.5 px-3">Variance</th>
              <th className="py-2.5 px-3">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-mono">
            {comparisonMetrics.map((item, idx) => {
              const isBad = item.trend === 'down_bad' || item.trend === 'up_bad';
              const isGood = item.trend === 'up_good' || item.trend === 'down_good';

              return (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-3 font-bold text-slate-900 font-sans">{item.metric}</td>
                  <td className="py-3 px-3 text-slate-900 font-bold">{item.current}</td>
                  <td className="py-3 px-3 text-slate-500">{item.previous}</td>
                  <td className="py-3 px-3 font-bold">
                    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded ${
                      isBad
                        ? 'bg-rose-50 text-rose-700 border border-rose-200'
                        : isGood
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-slate-100 text-slate-700'
                    }`}>
                      {item.change_text}
                    </span>
                  </td>
                  <td className="py-3 px-3 font-sans">
                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                      isBad ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                    }`}>
                      {isBad ? 'ATTENTION' : 'HEALTHY'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
