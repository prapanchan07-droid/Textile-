import React from 'react';
import { HeadToHeadMetric } from '../../types/machineComparison';
import { GitCompare, Trophy } from 'lucide-react';

interface HeadToHeadComparisonProps {
  machine1Id: string;
  machine2Id: string;
  metrics: HeadToHeadMetric[];
}

export const HeadToHeadComparison: React.FC<HeadToHeadComparisonProps> = ({
  machine1Id,
  machine2Id,
  metrics,
}) => {
  if (!metrics || metrics.length === 0) return null;

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2">
          <GitCompare className="w-5 h-5 text-indigo-600" />
          <h3 className="text-base font-bold text-slate-900 uppercase tracking-tight">
            Head-to-Head Comparison: <span className="text-blue-600">{machine1Id}</span> vs <span className="text-indigo-600">{machine2Id}</span>
          </h3>
        </div>
        <span className="text-xs font-semibold text-slate-500 bg-slate-100 border border-slate-200 px-3 py-1 rounded-full">
          Direct 2-Machine Comparison
        </span>
      </div>

      {/* Head to Head Table / Cards */}
      <div className="space-y-4">
        {metrics.map((row) => {
          const isM1Leader = row.leader_machine_id === machine1Id;
          const isM2Leader = row.leader_machine_id === machine2Id;

          return (
            <div
              key={row.metric_key}
              className="bg-slate-50/70 border border-slate-200/80 rounded-xl p-4 space-y-2"
            >
              <div className="flex items-center justify-between text-xs font-bold text-slate-500 uppercase tracking-wider">
                <span>{row.metric_name}</span>
                <span className="text-indigo-600 font-mono text-[11px]">{row.delta_text}</span>
              </div>

              <div className="grid grid-cols-2 gap-4">
                {/* Machine 1 Box */}
                <div
                  className={`p-3 rounded-xl border flex items-center justify-between ${
                    isM1Leader
                      ? 'bg-blue-50 border-blue-200 text-blue-950 font-bold'
                      : 'bg-white border-slate-200 text-slate-700'
                  }`}
                >
                  <div>
                    <span className="text-xs font-bold block">{machine1Id}</span>
                    <span className="text-lg font-black font-mono">{row.machine1_formatted}</span>
                  </div>
                  {isM1Leader && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-blue-700 bg-blue-100/80 px-2 py-0.5 rounded-md">
                      <Trophy className="w-3 h-3 text-blue-600" /> Leader
                    </span>
                  )}
                </div>

                {/* Machine 2 Box */}
                <div
                  className={`p-3 rounded-xl border flex items-center justify-between ${
                    isM2Leader
                      ? 'bg-indigo-50 border-indigo-200 text-indigo-950 font-bold'
                      : 'bg-white border-slate-200 text-slate-700'
                  }`}
                >
                  <div>
                    <span className="text-xs font-bold block">{machine2Id}</span>
                    <span className="text-lg font-black font-mono">{row.machine2_formatted}</span>
                  </div>
                  {isM2Leader && (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-indigo-700 bg-indigo-100/80 px-2 py-0.5 rounded-md">
                      <Trophy className="w-3 h-3 text-indigo-600" /> Leader
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
