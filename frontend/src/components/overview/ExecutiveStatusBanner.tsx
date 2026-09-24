import React from 'react';
import { AlertTriangle, ArrowRight, Zap, Target, Wrench } from 'lucide-react';
import { ExecutiveSummaryData } from '../../types/overview';

interface ExecutiveStatusBannerProps {
  summary: ExecutiveSummaryData;
  onInvestigateClick?: () => void;
}

export const ExecutiveStatusBanner: React.FC<ExecutiveStatusBannerProps> = ({
  summary,
  onInvestigateClick,
}) => {
  return (
    <div className="bg-white border border-rose-200 rounded-2xl p-5 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left Status Overview */}
        <div className="flex items-start gap-3.5">
          <div className="bg-rose-50 border border-rose-200 p-2.5 rounded-xl text-rose-600 shrink-0 mt-0.5">
            <AlertTriangle className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">TELEMETRY NODE // 01 • FACTORY OVERVIEW</span>
              <span className="bg-rose-100 text-rose-800 border border-rose-200 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase">
                {summary.factory_status}
              </span>
            </div>
            <h2 className="text-2xl font-extrabold text-slate-900 tracking-tight">
              Production Deficit Gap: <span className="text-rose-600">-{summary.impact_kg.toLocaleString()} kg</span>
            </h2>
            <p className="text-xs text-slate-600 leading-relaxed max-w-3xl">
              Real-time traversal metrics: Main contributor is <strong className="text-slate-900">{summary.main_issue}</strong> on <span className="text-indigo-600 font-semibold">{summary.affected_entity}</span>.
            </p>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex items-center gap-3 shrink-0 self-start lg:self-center">
          <div className="hidden sm:block text-right text-xs">
            <div className="text-slate-400 font-bold uppercase text-[10px]">Recommended Action</div>
            <div className="text-slate-900 font-bold">{summary.recommended_action}</div>
          </div>
          <button
            onClick={onInvestigateClick}
            className="inline-flex items-center gap-2 bg-factory-navy hover:bg-slate-800 text-white font-semibold px-4 py-2.5 rounded-xl text-xs shadow-nav transition-all hover:scale-[1.02]"
          >
            <span>Investigate Node</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
