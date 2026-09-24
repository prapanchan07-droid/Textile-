import React from 'react';
import { RecommendedAction } from '../../types/decisionCenter';
import { ArrowUpRight, CheckCircle2 } from 'lucide-react';

interface RecommendedActionsSectionProps {
  actions: RecommendedAction[];
  onNavigateTab: (tabId: string) => void;
}

export const RecommendedActionsSection: React.FC<RecommendedActionsSectionProps> = ({
  actions,
  onNavigateTab,
}) => {
  return (
    <section className="space-y-3">
      <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
        4. RECOMMENDED ACTION
      </h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {actions.slice(0, 3).map((item, index) => (
          <div
            key={item.id || index}
            className="bg-white border border-slate-200 hover:border-slate-300 rounded-2xl p-5 shadow-xs flex flex-col justify-between gap-4 transition-all hover:shadow-md"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="h-7 w-7 rounded-full bg-slate-900 text-white font-bold text-xs flex items-center justify-center">
                  {index + 1}
                </span>
                <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              </div>
              <p className="text-sm font-bold text-slate-900 leading-snug">
                {item.action_text}
              </p>
            </div>

            <button
              onClick={() => onNavigateTab(item.target_tab || 'overview')}
              className="inline-flex items-center justify-between w-full bg-slate-100 hover:bg-slate-200 text-slate-900 font-bold text-xs px-3.5 py-2.5 rounded-xl border border-slate-200/80 transition-colors cursor-pointer"
            >
              <span>{item.button_label}</span>
              <ArrowUpRight className="w-4 h-4 text-slate-500" />
            </button>
          </div>
        ))}
      </div>
    </section>
  );
};
