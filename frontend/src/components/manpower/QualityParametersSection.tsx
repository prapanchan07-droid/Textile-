import React from 'react';
import { QualityParameterItem } from '../../types/manpowerQuality';
import { Card } from '../ui/Card';

interface QualityParametersSectionProps {
  parameters: QualityParameterItem[];
}

export const QualityParametersSection: React.FC<QualityParametersSectionProps> = ({
  parameters,
}) => {
  return (
    <Card className="space-y-5 p-6">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          5. QUALITY PARAMETERS
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          Yarn quality parameters vs factory specifications
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
        {parameters.map((p) => {
          const isOutOfLimit = p.status === 'OUT OF LIMIT';
          const isAttention = p.status === 'ATTENTION';

          const cardStyle = isOutOfLimit
            ? 'bg-rose-50/70 border-rose-200'
            : isAttention
            ? 'bg-amber-50/60 border-amber-200'
            : 'bg-slate-50 border-slate-200/80';

          const badgeStyle = isOutOfLimit
            ? 'bg-rose-100 text-rose-800 border-rose-300'
            : isAttention
            ? 'bg-amber-100 text-amber-800 border-amber-300'
            : 'bg-emerald-100 text-emerald-800 border-emerald-300';

          return (
            <div
              key={p.parameter}
              className={`p-3.5 rounded-xl border space-y-2 flex flex-col justify-between ${cardStyle}`}
            >
              <div className="flex items-center justify-between">
                <span className="text-xs font-extrabold text-slate-900 font-sans">{p.label}</span>
                <span className={`text-[10px] font-extrabold px-2 py-0.5 rounded-full border ${badgeStyle}`}>
                  {p.status}
                </span>
              </div>

              <div className="flex items-baseline justify-between pt-1 font-mono">
                <span className={`text-xl font-extrabold ${isOutOfLimit ? 'text-rose-700' : 'text-slate-900'}`}>
                  {p.value} <span className="text-[11px] font-normal text-slate-500">{p.unit}</span>
                </span>
                <span className="text-[11px] font-semibold text-slate-400">
                  Limit: {p.limit} {p.unit}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
