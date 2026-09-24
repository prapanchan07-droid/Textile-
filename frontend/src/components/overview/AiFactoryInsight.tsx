import React from 'react';
import { Sparkles, CheckCircle2, AlertCircle } from 'lucide-react';
import { AIInsightData } from '../../types/overview';
import { Card } from '../ui/Card';

interface AiFactoryInsightProps {
  insight: AIInsightData;
}

export const AiFactoryInsight: React.FC<AiFactoryInsightProps> = ({ insight }) => {
  return (
    <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50/40 via-white to-slate-50 space-y-4">
      <div className="flex items-center justify-between border-b border-indigo-100 pb-3">
        <div className="flex items-center gap-2.5">
          <div className="bg-indigo-600 text-white p-1.5 rounded-lg shadow-sm">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-base">AI Factory Analytics & Reasoning Engine</h3>
            <p className="text-[11px] text-slate-500 font-medium">Deterministic evidence-based synthesis</p>
          </div>
        </div>
        <span className="bg-indigo-100 text-indigo-800 border border-indigo-200 px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider">
          {insight.confidence}
        </span>
      </div>

      <div className="space-y-3 text-xs leading-relaxed">
        {/* Core Summary */}
        <div className="bg-white p-3.5 rounded-xl border border-indigo-100 shadow-sm text-slate-800 font-medium">
          {insight.summary}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
          {/* Key Observations */}
          <div className="space-y-2">
            <h4 className="font-bold text-slate-700 uppercase tracking-wider text-[11px]">Observed Telemetry Evidence</h4>
            <ul className="space-y-1.5 text-slate-600">
              {insight.observations.map((obs, idx) => (
                <li key={idx} className="flex items-start gap-2 bg-white p-2.5 rounded-lg border border-slate-200/80 shadow-sm">
                  <span className="text-indigo-600 font-bold">•</span>
                  <span>{obs}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Recommended Investigation */}
          <div className="space-y-2">
            <h4 className="font-bold text-emerald-800 uppercase tracking-wider text-[11px]">Recommended Investigation Protocol</h4>
            <ul className="space-y-1.5 text-slate-700">
              {insight.recommended_investigation.map((rec, idx) => (
                <li key={idx} className="flex items-start gap-2 bg-white p-2.5 rounded-lg border border-emerald-200/80 shadow-sm">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                  <span>{rec}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </Card>
  );
};
