import React from 'react';
import { AIInsightData } from '../../types/decisionCenter';
import { Sparkles } from 'lucide-react';

interface AIInsightSectionProps {
  data: AIInsightData;
}

export const AIInsightSection: React.FC<AIInsightSectionProps> = ({ data }) => {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          8. AI INSIGHT
        </h2>
        <span className="text-xs text-slate-400 font-medium">
          Evidence confidence: <strong className="text-slate-700 font-semibold">{data.evidence_confidence || 'High'}</strong>
        </span>
      </div>

      {/* Clean Light AI Insight Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-5">
        <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
          <Sparkles className="w-4 h-4 text-indigo-600" />
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              AI INSIGHT
            </h3>
            <p className="text-xs text-slate-500 font-medium">
              &ldquo;Evidence-based explanation&rdquo;
            </p>
          </div>
        </div>

        {/* Concise WHY THIS HAPPENED Structure */}
        <div className="space-y-3">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Why This Happened
          </span>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="bg-slate-50 border border-slate-200/70 rounded-xl p-3">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">
                Production Gap
              </span>
              <span className="text-sm font-bold text-red-600 font-mono mt-0.5 block">
                -2,380 kg
              </span>
            </div>

            <div className="bg-slate-50 border border-slate-200/70 rounded-xl p-3">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">
                Main Contributor
              </span>
              <span className="text-sm font-bold text-slate-900 mt-0.5 block">
                Machine downtime
              </span>
            </div>

            <div className="bg-slate-50 border border-slate-200/70 rounded-xl p-3">
              <span className="text-[10px] font-bold text-slate-400 block uppercase">
                Most Affected
              </span>
              <span className="text-sm font-bold text-slate-900 mt-0.5 block">
                V-09 — Vortex
              </span>
            </div>
          </div>

          <div className="bg-slate-50/80 border border-slate-200/70 rounded-xl p-3 text-xs text-slate-700">
            <span className="font-bold text-slate-900 block text-[10px] uppercase text-slate-400 mb-0.5">
              Related Observation
            </span>
            <p className="font-medium">
              Repeated power events occurred during the affected period.
            </p>
          </div>
        </div>

        {/* Subtle Highlighted Recommendation Box */}
        <div className="space-y-1.5 pt-1">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
            Recommended Action
          </span>
          <div className="bg-indigo-50/70 border border-indigo-100 rounded-xl p-4 text-xs font-bold text-indigo-950">
            {data.recommended_focus || "Investigate V-09 downtime and related power events."}
          </div>
        </div>
      </div>
    </section>
  );
};
