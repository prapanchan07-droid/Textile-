import React from 'react';
import { StockCategoryItem } from '../../types/revenueLoss';
import { Card } from '../ui/Card';

interface StockPositionSectionProps {
  stockItems: StockCategoryItem[];
}

export const StockPositionSection: React.FC<StockPositionSectionProps> = ({ stockItems }) => {
  return (
    <Card className="space-y-5 p-6">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          5. STOCK POSITION
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          Finished goods fabric & raw yarn inventory valuation
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {stockItems.map((item) => {
          const isAttention = item.status === 'ATTENTION' || item.status === 'CRITICAL';

          const cardStyle = isAttention
            ? 'bg-amber-50/60 border-amber-200'
            : 'bg-slate-50 border-slate-200/80';

          const badgeStyle = isAttention
            ? 'bg-amber-100 text-amber-800 border-amber-300'
            : 'bg-emerald-100 text-emerald-800 border-emerald-300';

          return (
            <div
              key={item.category}
              className={`p-4 rounded-xl border space-y-2 flex flex-col justify-between ${cardStyle}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold text-slate-900 uppercase font-sans">
                  {item.category}
                </span>
                <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${badgeStyle}`}>
                  {item.status}
                </span>
              </div>

              <div className="space-y-1 pt-1 font-mono">
                <div className={`text-xl font-extrabold ${isAttention ? 'text-amber-900' : 'text-slate-900'}`}>
                  {item.unit}{item.current_value_lakhs.toFixed(2)} L
                </div>
                <div className="text-[11px] font-semibold text-slate-500">
                  Limit: {item.unit}{item.limit_value_lakhs.toFixed(2)} L
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
