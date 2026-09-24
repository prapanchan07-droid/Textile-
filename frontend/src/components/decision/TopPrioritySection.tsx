import React from 'react';
import { TopPriorityData } from '../../types/decisionCenter';
import { ArrowRight } from 'lucide-react';

interface TopPrioritySectionProps {
  data: TopPriorityData;
  onNavigateTab: (tabId: string) => void;
}

export const TopPrioritySection: React.FC<TopPrioritySectionProps> = ({
  data,
  onNavigateTab,
}) => {
  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          1. TOP PRIORITY
        </h2>
        <div className="inline-flex items-center gap-1.5 bg-red-50 text-red-700 border border-red-200 px-2.5 py-0.5 rounded-full text-xs font-bold">
          <span className="w-1.5 h-1.5 rounded-full bg-red-600 animate-pulse"></span>
          <span>{data.badge_label}</span>
        </div>
      </div>

      {/* Clean Premium Management Card */}
      <div className="bg-white border border-slate-200 border-l-4 border-l-red-500 rounded-2xl p-6 shadow-xs transition-all space-y-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-4 max-w-3xl flex-1">
            {/* Title & Short Gap Highlight */}
            <div>
              <h3 className="text-2xl font-extrabold text-slate-900 tracking-tight">
                {data.title}
              </h3>
              <p className="text-base font-bold text-red-600 mt-1">
                {data.sub_highlight}
              </p>
            </div>

            {/* Main Contributor & Affected Entity */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
              <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
                <span className="text-[11px] font-bold text-slate-400 block uppercase tracking-wider">
                  Main Contributor
                </span>
                <span className="text-sm font-bold text-slate-900 mt-0.5 block">
                  {data.main_contributor}
                </span>
              </div>
              <div className="bg-slate-50 border border-slate-200/80 rounded-xl p-3">
                <span className="text-[11px] font-bold text-slate-400 block uppercase tracking-wider">
                  Most Affected
                </span>
                <span className="text-sm font-bold text-slate-900 mt-0.5 block">
                  {data.most_affected_machine_type} — <span className="text-slate-900 font-extrabold">{data.most_affected_machine_id}</span>
                </span>
              </div>
            </div>

            {/* Compact Production Summary */}
            <div className="flex flex-wrap items-center gap-6 text-xs sm:text-sm font-medium pt-1 text-slate-600">
              <div>
                <span className="text-slate-400 text-[11px] block uppercase font-bold">Production</span>
                <span className="font-bold text-slate-900 font-mono">
                  {data.actual_kg.toLocaleString()} kg
                </span>
              </div>
              <div className="text-slate-300">|</div>
              <div>
                <span className="text-slate-400 text-[11px] block uppercase font-bold">Target</span>
                <span className="font-bold text-slate-900 font-mono">
                  {data.target_kg.toLocaleString()} kg
                </span>
              </div>
              <div className="text-slate-300">|</div>
              <div>
                <span className="text-slate-400 text-[11px] block uppercase font-bold">Gap</span>
                <span className="font-bold text-red-600 font-mono">
                  {data.gap_kg > 0 ? `+${data.gap_kg.toLocaleString()}` : data.gap_kg.toLocaleString()} kg
                </span>
              </div>
            </div>
          </div>

          {/* Action Button */}
          <div className="flex items-center md:self-center">
            <button
              onClick={() => onNavigateTab(data.target_tab || 'production')}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 bg-slate-900 hover:bg-slate-800 text-white font-bold text-xs px-5 py-3.5 rounded-xl shadow-xs transition-all hover:translate-x-0.5 cursor-pointer"
            >
              <span>View Problem</span>
              <ArrowRight className="w-4 h-4 text-slate-300" />
            </button>
          </div>
        </div>
      </div>
    </section>
  );
};
