import React from 'react';
import { BusinessPerformanceSummary } from '../../types/revenueLoss';
import { Card } from '../ui/Card';

interface BusinessPerformanceSectionProps {
  summary: BusinessPerformanceSummary;
}

export const BusinessPerformanceSection: React.FC<BusinessPerformanceSectionProps> = ({ summary }) => {
  return (
    <Card className="space-y-4 p-6">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          6. BUSINESS PERFORMANCE
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          At-a-glance financial & operational business position
        </p>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
        <div className="bg-slate-50 border border-slate-200/80 p-3 rounded-xl space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase">Revenue</span>
          <div className="text-base font-extrabold text-slate-900 font-mono">
            ₹{summary.revenue_lakhs.toFixed(1)} L
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 p-3 rounded-xl space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase">Orders</span>
          <div className="text-base font-extrabold text-slate-900 font-mono">
            {summary.orders_meters.toLocaleString()} m
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 p-3 rounded-xl space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase">Dispatched</span>
          <div className="text-base font-extrabold text-blue-600 font-mono">
            {summary.dispatched_meters.toLocaleString()} m
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 p-3 rounded-xl space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase">Collected</span>
          <div className="text-base font-extrabold text-emerald-600 font-mono">
            ₹{summary.collected_lakhs.toFixed(1)} L
          </div>
        </div>

        <div className="bg-rose-50/70 border border-rose-200/80 p-3 rounded-xl space-y-1">
          <span className="text-[10px] text-rose-700 font-bold uppercase">Outstanding</span>
          <div className="text-base font-extrabold text-rose-700 font-mono">
            ₹{summary.outstanding_lakhs.toFixed(1)} L
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 p-3 rounded-xl space-y-1">
          <span className="text-[10px] text-slate-400 font-bold uppercase">Total Stock</span>
          <div className="text-base font-extrabold text-amber-900 font-mono">
            ₹{summary.total_stock_lakhs.toFixed(2)} L
          </div>
        </div>
      </div>
    </Card>
  );
};
