import React from 'react';
import { WhyContributor } from '../../types/decisionCenter';

interface WhySectionProps {
  contributors: WhyContributor[];
}

export const WhySection: React.FC<WhySectionProps> = ({ contributors }) => {
  return (
    <section className="space-y-3">
      <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
        2. WHY?
      </h2>

      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-5">
        <p className="text-xs text-slate-500 font-medium">
          Top contributing factors driving current production gap
        </p>

        <div className="space-y-4">
          {contributors.slice(0, 3).map((item, index) => {
            const barBg =
              item.status_color === 'RED'
                ? 'bg-red-500'
                : item.status_color === 'ORANGE'
                ? 'bg-amber-500'
                : 'bg-yellow-500';

            const dotColor =
              item.status_color === 'RED'
                ? 'text-red-500'
                : item.status_color === 'ORANGE'
                ? 'text-amber-500'
                : 'text-yellow-500';

            return (
              <div key={index} className="space-y-1.5">
                <div className="flex items-center justify-between text-xs sm:text-sm font-bold text-slate-900">
                  <div className="flex items-center gap-2">
                    <span className={dotColor}>●</span>
                    <span>{item.category}</span>
                  </div>
                  <span className="font-mono text-slate-700">{item.percentage}%</span>
                </div>

                {/* Progress Bar Container */}
                <div className="w-full bg-slate-100 rounded-full h-3.5 overflow-hidden p-0.5 border border-slate-200/60">
                  <div
                    className={`${barBg} h-full rounded-full transition-all duration-500 ease-out`}
                    style={{ width: `${Math.min(item.percentage, 100)}%` }}
                  ></div>
                </div>

                {item.detail_text && (
                  <p className="text-[11px] text-slate-500 font-normal pl-4">
                    {item.detail_text}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
};
