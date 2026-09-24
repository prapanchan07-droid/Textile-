import React from 'react';
import { AttentionItem } from '../../types/manpowerQuality';
import { Card } from '../ui/Card';
import { AlertTriangle, AlertCircle, Info } from 'lucide-react';

interface NeedsAttentionSectionProps {
  items: AttentionItem[];
}

export const NeedsAttentionSection: React.FC<NeedsAttentionSectionProps> = ({ items }) => {
  return (
    <Card className="space-y-4 p-6">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          8. NEEDS ATTENTION
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          Priority workforce and quality action items
        </p>
      </div>

      <div className="space-y-2.5">
        {items.map((item, idx) => {
          const isHigh = item.severity === 'HIGH';
          const isMedium = item.severity === 'MEDIUM';

          const icon = isHigh ? (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          ) : isMedium ? (
            <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
          ) : (
            <Info className="w-4 h-4 text-blue-600 shrink-0" />
          );

          const style = isHigh
            ? 'bg-rose-50/70 border-rose-200 text-rose-950'
            : isMedium
            ? 'bg-amber-50/60 border-amber-200 text-amber-950'
            : 'bg-blue-50/60 border-blue-200 text-blue-950';

          return (
            <div
              key={idx}
              className={`p-3 rounded-xl border flex items-center gap-3 text-xs ${style}`}
            >
              {icon}
              <div className="flex-1">
                <span className="font-extrabold text-slate-900">{item.title}: </span>
                <span className="font-medium text-slate-700">{item.detail}</span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
