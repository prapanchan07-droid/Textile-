import React from 'react';
import { RevenueCurrentSummary } from '../../types/revenueLoss';
import { Card } from '../ui/Card';
import { IndianRupee, TrendingDown, TrendingUp } from 'lucide-react';

interface RevenueCurrentSectionProps {
  summary: RevenueCurrentSummary;
  selectedPeriod: string;
  onPeriodChange: (p: string) => void;
}

export const RevenueCurrentSection: React.FC<RevenueCurrentSectionProps> = ({
  summary,
  selectedPeriod,
  onPeriodChange,
}) => {
  const isNegative = summary.change_lakhs < 0;

  return (
    <Card className="space-y-6 p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            1. REVENUE CURRENT PERIOD
          </h2>
          <p className="text-base font-bold text-slate-900 mt-0.5">
            Total sales revenue and period comparison
          </p>
        </div>

        {/* Period Selector Pill */}
        <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-bold">
          {(
            [
              { id: 'TODAY', label: 'Today' },
              { id: 'SEVEN_DAYS', label: '7 Days' },
              { id: 'THIS_MONTH', label: 'This Month' },
            ] as const
          ).map((r) => (
            <button
              key={r.id}
              onClick={() => onPeriodChange(r.id)}
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

      {/* Primary Dominant Revenue Display */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-50 border border-slate-200/80 rounded-2xl p-6">
        <div className="space-y-1">
          <div className="text-xs font-extrabold text-slate-400 uppercase tracking-wider">
            REVENUE THIS MONTH
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-slate-900 font-mono tracking-tight">
              {summary.currency_symbol}{summary.revenue_amount_lakhs.toFixed(1)} L
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {isNegative ? (
            <div className="flex items-center gap-2 bg-rose-50 border border-rose-200 text-rose-700 px-4 py-2 rounded-xl text-xs font-extrabold shadow-sm">
              <TrendingDown className="w-4 h-4 text-rose-600 shrink-0" />
              <span>
                ↓ {summary.currency_symbol}{Math.abs(summary.change_lakhs).toFixed(1)} L vs last month ({summary.change_pct.toFixed(1)}%)
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-2 bg-emerald-50 border border-emerald-200 text-emerald-700 px-4 py-2 rounded-xl text-xs font-extrabold shadow-sm">
              <TrendingUp className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>
                ↑ {summary.currency_symbol}{summary.change_lakhs.toFixed(1)} L vs last month (+{summary.change_pct.toFixed(1)}%)
              </span>
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
