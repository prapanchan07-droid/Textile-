import React from 'react';
import { MoneyPositionData } from '../../types/revenueLoss';
import { Card } from '../ui/Card';
import { IndianRupee, AlertCircle, CheckCircle2 } from 'lucide-react';

interface MoneyPositionSectionProps {
  data: MoneyPositionData;
}

export const MoneyPositionSection: React.FC<MoneyPositionSectionProps> = ({ data }) => {
  return (
    <Card className="space-y-6 p-6">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          4. MONEY POSITION
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          Outstanding receivables & payment collections
        </p>
      </div>

      {/* 3 Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Outstanding (Highlight Warning) */}
        <div className="bg-rose-50/70 border border-rose-200/80 rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-extrabold text-rose-700 uppercase tracking-wider">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
            <span>OUTSTANDING</span>
          </div>
          <div className="text-2xl font-extrabold text-rose-700 font-mono">
            {data.currency_symbol}{data.outstanding_lakhs.toFixed(1)} L
          </div>
        </div>

        {/* Collected */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>COLLECTED</span>
          </div>
          <div className="text-2xl font-extrabold text-emerald-600 font-mono">
            {data.currency_symbol}{data.collected_lakhs.toFixed(1)} L
          </div>
        </div>

        {/* Collection Rate */}
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 space-y-1">
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">
            COLLECTION RATE
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            {data.collection_rate_pct.toFixed(1)}%
          </div>
        </div>
      </div>
    </Card>
  );
};
