import React from 'react';
import { OtherIssueItem } from '../../types/decisionCenter';

interface OtherIssuesSectionProps {
  issues: OtherIssueItem[];
  onNavigateTab: (tabId?: string) => void;
}

export const OtherIssuesSection: React.FC<OtherIssuesSectionProps> = ({
  issues,
  onNavigateTab,
}) => {
  return (
    <section className="space-y-3">
      <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
        6. OTHER ISSUES TO WATCH
      </h2>

      <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs divide-y divide-slate-100">
        {issues.slice(0, 5).map((item, index) => (
          <div
            key={item.id || index}
            onClick={() => onNavigateTab(item.target_tab)}
            className="flex flex-col sm:flex-row sm:items-center justify-between p-3 hover:bg-slate-50 rounded-xl transition-colors cursor-pointer gap-2"
          >
            <div className="flex items-center gap-3">
              <span className="text-base">{item.status_icon}</span>
              <div>
                <span className="text-xs font-bold text-slate-900 block">
                  {item.category}
                </span>
                <span className="text-[11px] text-slate-500 font-medium">
                  {item.location_or_area}
                </span>
              </div>
            </div>

            <div className="flex items-center gap-3 self-end sm:self-auto">
              <span className="text-xs font-bold text-slate-700 bg-slate-100 border border-slate-200/80 px-2.5 py-1 rounded-lg">
                {item.impact_detail}
              </span>
              <span className="text-slate-400 text-xs">→</span>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
};
