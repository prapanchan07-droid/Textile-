import React from 'react';
import { ManpowerSummary } from '../../types/manpowerQuality';
import { Card } from '../ui/Card';
import { Users, AlertCircle, CheckCircle2 } from 'lucide-react';

interface ManpowerStatusSectionProps {
  summary: ManpowerSummary;
}

export const ManpowerStatusSection: React.FC<ManpowerStatusSectionProps> = ({ summary }) => {
  const hasShortage = summary.shortage > 0;

  return (
    <Card className="space-y-6 p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            1. MANPOWER STATUS
          </h2>
          <div className="flex flex-wrap items-baseline gap-3 mt-1">
            <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
              MANPOWER TODAY
            </span>
            {hasShortage ? (
              <span className="inline-flex items-center gap-1.5 text-xs font-extrabold text-rose-700 bg-rose-50 border border-rose-200 px-3 py-1 rounded-lg">
                <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                <span>SHORTAGE: {summary.shortage} workers</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-xs font-extrabold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-lg">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>MANPOWER SUFFICIENT</span>
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200/80">
          <Users className="w-4 h-4 text-slate-600" />
          <span>Attendance Rate:</span>
          <span className="font-mono font-bold text-slate-900 text-sm">{summary.attendance_pct}%</span>
        </div>
      </div>

      {/* 4 Clean Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-center space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Required</span>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            {summary.required.toLocaleString()}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-center space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Available</span>
          <div className="text-2xl font-extrabold text-blue-600 font-mono">
            {summary.available.toLocaleString()}
          </div>
        </div>

        <div className={`border rounded-xl p-4 text-center space-y-1 ${hasShortage ? 'bg-rose-50/70 border-rose-200/80' : 'bg-slate-50 border-slate-200'}`}>
          <span className={`text-[10px] font-bold uppercase tracking-wider ${hasShortage ? 'text-rose-700' : 'text-slate-400'}`}>
            Shortage
          </span>
          <div className={`text-2xl font-extrabold font-mono ${hasShortage ? 'text-rose-700' : 'text-slate-900'}`}>
            {hasShortage ? `-${summary.shortage}` : '0'}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-center space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Attendance %</span>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            {summary.attendance_pct}%
          </div>
        </div>
      </div>
    </Card>
  );
};
