import React from 'react';
import { AiProductionAnalysisData } from '../../types/production';
import { Card } from '../ui/Card';
import { Sparkles, ArrowRight } from 'lucide-react';

interface AiProductionAnalysisSectionProps {
  analysis: AiProductionAnalysisData;
  onViewDetailedAnalysis?: () => void;
}

export const AiProductionAnalysisSection: React.FC<AiProductionAnalysisSectionProps> = ({
  analysis,
  onViewDetailedAnalysis,
}) => {
  return (
    <Card className="space-y-4 p-6 border-indigo-200 bg-gradient-to-br from-indigo-50/40 via-white to-slate-50">
      <div className="flex justify-between items-center border-b border-indigo-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="bg-indigo-600 text-white p-1.5 rounded-lg shadow-sm">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 font-sans">
              7. AI PRODUCTION ANALYSIS
            </h2>
            <p className="text-sm font-extrabold text-slate-900 mt-0.5">
              Decision Support & Action Item
            </p>
          </div>
        </div>

        <span className="bg-indigo-100 text-indigo-800 border border-indigo-200 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase">
          EVIDENCE-BASED
        </span>
      </div>

      <div className="bg-white p-4 rounded-xl border border-indigo-100 shadow-sm space-y-3 text-xs">
        <p className="font-extrabold text-slate-900 text-sm">
          {analysis.summary}
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 pt-1">
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase block">MAIN AFFECTED MACHINE TYPE</span>
            <span className="text-sm font-extrabold text-indigo-600 font-mono">{analysis.affected_machine_type}</span>
          </div>

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 space-y-1">
            <span className="text-[10px] font-bold text-slate-400 uppercase block">MAIN OBSERVED FACTOR</span>
            <span className="text-sm font-extrabold text-rose-700">{analysis.main_observed_factor}</span>
          </div>
        </div>

        <div className="bg-slate-900 text-white p-3.5 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3 mt-2">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase block">RECOMMENDED ACTION</span>
            <span className="text-xs font-bold text-white mt-0.5 block">{analysis.recommended_action}</span>
          </div>

          <button
            onClick={onViewDetailedAnalysis}
            className="bg-indigo-600 hover:bg-indigo-700 text-white font-bold px-3.5 py-2 rounded-lg text-xs shadow-sm transition-colors flex items-center gap-1.5 shrink-0"
          >
            <span>View Detailed Analysis</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </Card>
  );
};
