import React from 'react';
import { QualityStatusData } from '../../types/manpowerQuality';
import { Card } from '../ui/Card';
import { ShieldAlert, CheckCircle2, AlertTriangle } from 'lucide-react';

interface QualityStatusSectionProps {
  status: QualityStatusData;
}

export const QualityStatusSection: React.FC<QualityStatusSectionProps> = ({ status }) => {
  const isAttention = status.status === 'ATTENTION' || status.status === 'CRITICAL';

  return (
    <Card className="space-y-6 p-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-4">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            4. QUALITY STATUS
          </h2>
          <div className="flex flex-wrap items-baseline gap-3 mt-1">
            <span className="text-2xl font-extrabold text-slate-900 tracking-tight">
              QUALITY TODAY
            </span>
            {isAttention ? (
              <span className="inline-flex items-center gap-1.5 text-xs font-extrabold text-amber-800 bg-amber-50 border border-amber-200 px-3 py-1 rounded-lg">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
                <span>● Attention Required</span>
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-xs font-extrabold text-emerald-700 bg-emerald-50 border border-emerald-200 px-3 py-1 rounded-lg">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>● Within Specification Limits</span>
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-bold text-slate-600 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
          <ShieldAlert className="w-4 h-4 text-slate-500" />
          <span>Main Issue:</span>
          <span className="text-rose-600 font-extrabold">{status.main_issue}</span>
        </div>
      </div>

      {/* 4 Clean Metric Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-center space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Samples Tested</span>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            {status.samples_tested}
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-center space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Pass Rate</span>
          <div className="text-2xl font-extrabold text-emerald-600 font-mono">
            {status.pass_rate_pct}%
          </div>
        </div>

        <div className="bg-rose-50/70 border border-rose-200/80 rounded-xl p-4 text-center space-y-1">
          <span className="text-[10px] font-bold text-rose-700 uppercase tracking-wider">Defect Rate</span>
          <div className="text-2xl font-extrabold text-rose-700 font-mono">
            {status.defect_rate_pct}%
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-4 text-center space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">Primary Deviation</span>
          <div className="text-sm font-extrabold text-slate-900 truncate mt-1">
            {status.main_issue}
          </div>
        </div>
      </div>
    </Card>
  );
};
