import React from 'react';
import { Card } from '../ui/Card';
import { Sparkles, ArrowRight, AlertTriangle } from 'lucide-react';

interface AiRecommendationSectionProps {
  onViewDetails?: () => void;
}

export const AiRecommendationSection: React.FC<AiRecommendationSectionProps> = ({
  onViewDetails,
}) => {
  return (
    <Card className="space-y-5 p-6 border-indigo-200 bg-gradient-to-br from-indigo-50/40 via-white to-slate-50">
      {/* Header with Title & Priority Badge */}
      <div className="flex justify-between items-center border-b border-indigo-100 pb-3">
        <div className="flex items-center gap-2">
          <div className="bg-indigo-600 text-white p-1.5 rounded-lg shadow-sm">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 font-sans">
              5. AI RECOMMENDATION
            </h2>
            <p className="text-sm font-extrabold text-slate-900 mt-0.5">
              WHAT SHOULD I DO?
            </p>
          </div>
        </div>

        <span className="inline-flex items-center gap-1.5 bg-rose-100 border border-rose-200 text-rose-800 text-xs font-extrabold px-3 py-1 rounded-full uppercase tracking-wider">
          <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
          <span>HIGH PRIORITY</span>
        </span>
      </div>

      {/* 4 Clean Short Items */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs">
        {/* 1. Problem */}
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">1. PROBLEM</span>
          <p className="font-extrabold text-slate-900 leading-snug">
            Production is 6.4% below today's target.
          </p>
        </div>

        {/* 2. Main Reason */}
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">2. MAIN REASON</span>
          <p className="font-extrabold text-slate-900 leading-snug">
            Machine downtime is the largest observed contributor.
          </p>
        </div>

        {/* 3. Machine */}
        <div className="bg-white p-3.5 rounded-xl border border-slate-200 shadow-sm space-y-1">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">3. MACHINE / AREA</span>
          <p className="font-extrabold text-indigo-600 font-mono leading-snug">
            V-09 (680 kg loss, 240 min downtime)
          </p>
        </div>

        {/* 4. Action */}
        <div className="bg-white p-3.5 rounded-xl border border-indigo-200 shadow-sm space-y-1">
          <span className="text-[10px] font-bold text-indigo-600 uppercase tracking-wider block">4. RECOMMENDED ACTION</span>
          <p className="font-extrabold text-slate-900 leading-snug">
            Check V-09 downtime and maintenance history.
          </p>
        </div>
      </div>

      {/* Why & Action Button Footer */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
        <div className="space-y-0.5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider">WHY THIS RECOMMENDATION?</span>
          <p className="text-xs font-semibold text-slate-700">
            V-09 has the highest observed production loss and below-average efficiency (84.2% vs 91.6% average).
          </p>
        </div>

        <button
          onClick={onViewDetails}
          className="inline-flex items-center justify-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white font-bold px-4 py-2 rounded-xl text-xs shadow-sm transition-colors shrink-0"
        >
          <span>VIEW DETAILED ANALYSIS</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </Card>
  );
};
