import React from 'react';
import { ShieldAlert, ArrowRight } from 'lucide-react';
import { RecommendedInvestigationData } from '../../types/overview';
import { Card } from '../ui/Card';

interface RecommendedInvestigationCardProps {
  investigation: RecommendedInvestigationData;
  onInvestigateClick?: () => void;
}

export const RecommendedInvestigationCard: React.FC<RecommendedInvestigationCardProps> = ({
  investigation,
  onInvestigateClick,
}) => {
  return (
    <Card className="border-rose-200 bg-white space-y-3">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-rose-600" />
          <h3 className="font-bold text-slate-900 text-base">Recommended Investigation Action</h3>
        </div>
        <span className="bg-rose-600 text-white font-bold text-[10px] px-2.5 py-0.5 rounded-full uppercase tracking-wider">
          PRIORITY: {investigation.priority}
        </span>
      </div>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-slate-50 p-4 rounded-xl border border-slate-200">
        <div className="space-y-1 text-xs">
          <div className="text-slate-500">
            Target Area: <strong className="text-slate-900">{investigation.area}</strong> • Node ID: <strong className="text-indigo-600 font-mono">{investigation.machine_id}</strong>
          </div>
          <p className="text-slate-700">
            Observed Issue: <span className="text-rose-700 font-semibold">{investigation.observed_issue}</span>
          </p>
          <p className="text-slate-900 font-bold pt-1">
            Action Item: {investigation.recommended_next_step}
          </p>
        </div>

        <button
          onClick={onInvestigateClick}
          className="inline-flex items-center gap-2 bg-rose-600 hover:bg-rose-700 text-white px-4 py-2 rounded-xl text-xs font-bold shadow-sm transition-colors shrink-0"
        >
          <span>View Telemetry</span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </Card>
  );
};
