import React from 'react';
import { ComparisonInsightData } from '../../types/machineComparison';
import { Lightbulb } from 'lucide-react';

interface ComparisonInsightProps {
  insight: ComparisonInsightData;
}

export const ComparisonInsight: React.FC<ComparisonInsightProps> = ({ insight }) => {
  if (!insight || (!insight.summary_text && (!insight.key_observations || insight.key_observations.length === 0))) {
    return null;
  }

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-3">
      <div className="flex items-center gap-2">
        <Lightbulb className="w-4 h-4 text-amber-500" />
        <h3 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          Factual Telemetry Summary
        </h3>
      </div>

      <p className="text-sm font-bold text-slate-900 leading-relaxed">
        {insight.summary_text}
      </p>

      {insight.key_observations && insight.key_observations.length > 0 && (
        <ul className="space-y-1.5 pt-1 border-t border-slate-100 text-xs font-medium text-slate-600">
          {insight.key_observations.map((obs, idx) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-blue-600 font-bold">•</span>
              <span>{obs}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};
