import React from 'react';
import { Card } from '../ui/Card';

interface WhatIsHappeningSectionProps {
  onViewDetails?: () => void;
}

export const WhatIsHappeningSection: React.FC<WhatIsHappeningSectionProps> = ({
  onViewDetails,
}) => {
  return (
    <Card className="space-y-5 p-6 border-slate-200">
      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            5. WHAT IS HAPPENING?
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            Quick Executive Summary
          </p>
        </div>
        <span className="text-xs font-semibold bg-slate-100 text-slate-700 px-2.5 py-1 rounded-lg">
          3 Key Facts
        </span>
      </div>

      {/* 3 Short Plain Business Statements */}
      <div className="space-y-2 text-xs">
        <div className="flex items-start gap-2.5 bg-slate-50 p-3 rounded-xl border border-slate-200 text-slate-800">
          <span className="w-2 h-2 rounded-full bg-rose-600 shrink-0 mt-1.5" />
          <span>Production is <strong>6.4% below today's target</strong> (2,380 kg gap).</span>
        </div>

        <div className="flex items-start gap-2.5 bg-slate-50 p-3 rounded-xl border border-slate-200 text-slate-800">
          <span className="w-2 h-2 rounded-full bg-amber-500 shrink-0 mt-1.5" />
          <span><strong>Machine downtime</strong> is the largest reason for the loss (1,120 kg loss).</span>
        </div>

        <div className="flex items-start gap-2.5 bg-slate-50 p-3 rounded-xl border border-slate-200 text-slate-800">
          <span className="w-2 h-2 rounded-full bg-rose-600 shrink-0 mt-1.5" />
          <span>Machine <strong>V-09</strong> needs attention because of 4 hours of downtime and low efficiency (84.2%).</span>
        </div>
      </div>

      {/* What to Check Box */}
      <div className="bg-slate-900 text-white p-4 rounded-xl flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">WHAT TO CHECK NEXT</div>
          <div className="text-xs font-bold text-white mt-0.5">
            Check V-09 downtime and maintenance history.
          </div>
        </div>
        <button
          onClick={onViewDetails}
          className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-3.5 py-2 rounded-lg text-xs shadow-sm transition-colors shrink-0"
        >
          View Details
        </button>
      </div>
    </Card>
  );
};
