import React from 'react';
import { DispatchOrdersData } from '../../types/revenueLoss';
import { Card } from '../ui/Card';
import { Package, Truck, Clock } from 'lucide-react';

interface DispatchOrdersSectionProps {
  data: DispatchOrdersData;
}

export const DispatchOrdersSection: React.FC<DispatchOrdersSectionProps> = ({ data }) => {
  return (
    <Card className="space-y-6 p-6">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          3. DISPATCH & ORDERS
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          Order volume vs actual dispatch execution
        </p>
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            <Package className="w-3.5 h-3.5 text-slate-500" />
            <span>ORDERS</span>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            {data.orders_meters.toLocaleString()} <span className="text-xs font-normal text-slate-500">m</span>
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            <Truck className="w-3.5 h-3.5 text-blue-600" />
            <span>DISPATCHED</span>
          </div>
          <div className="text-2xl font-extrabold text-blue-600 font-mono">
            {data.dispatched_meters.toLocaleString()} <span className="text-xs font-normal text-slate-500">m</span>
          </div>
        </div>

        <div className="bg-amber-50/70 border border-amber-200/80 rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-amber-800 uppercase tracking-wider">
            <Clock className="w-3.5 h-3.5 text-amber-600" />
            <span>PENDING DISPATCH</span>
          </div>
          <div className="text-2xl font-extrabold text-amber-800 font-mono">
            {data.pending_meters.toLocaleString()} <span className="text-xs font-normal text-amber-600">m</span>
          </div>
        </div>
      </div>

      {/* Visual Fulfillment Bar */}
      <div className="space-y-2 pt-1">
        <div className="flex justify-between text-xs font-bold">
          <span className="text-slate-600">Fulfillment Rate</span>
          <span className="font-mono text-slate-900">{data.fulfillment_pct}% Dispatched</span>
        </div>
        <div className="w-full bg-amber-100 rounded-full h-4 p-0.5 border border-slate-200 flex overflow-hidden">
          <div
            className="bg-blue-600 h-full rounded-full transition-all duration-500"
            style={{ width: `${data.fulfillment_pct}%` }}
          />
        </div>
        <div className="flex justify-between text-[11px] font-mono text-slate-400 font-semibold pt-0.5">
          <span>0 m</span>
          <span>Target: {data.orders_meters.toLocaleString()} m</span>
        </div>
      </div>
    </Card>
  );
};
