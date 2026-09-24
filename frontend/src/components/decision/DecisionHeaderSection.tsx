import React from 'react';
import { TimePeriod } from '../../types/overview';

interface DecisionHeaderSectionProps {
  selectedPeriod: TimePeriod;
  onPeriodChange: (period: TimePeriod) => void;
}

export const DecisionHeaderSection: React.FC<DecisionHeaderSectionProps> = ({
  selectedPeriod,
  onPeriodChange,
}) => {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
      <div>
        <div className="flex items-center gap-2">
          <span className="text-xl">🎯</span>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight uppercase">
            Decision Center
          </h1>
        </div>
        <p className="text-sm font-medium text-slate-500 mt-1">
          &ldquo;Important issues that need management attention&rdquo;
        </p>
      </div>

      <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 self-start sm:self-auto">
        <button
          onClick={() => onPeriodChange('TODAY')}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
            selectedPeriod === 'TODAY'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
          }`}
        >
          Today
        </button>
        <button
          onClick={() => onPeriodChange('THIS_WEEK')}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
            selectedPeriod === 'THIS_WEEK'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
          }`}
        >
          This Week
        </button>
        <button
          onClick={() => onPeriodChange('THIS_MONTH')}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-all ${
            selectedPeriod === 'THIS_MONTH'
              ? 'bg-slate-900 text-white shadow-xs'
              : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
          }`}
        >
          This Month
        </button>
      </div>
    </div>
  );
};
