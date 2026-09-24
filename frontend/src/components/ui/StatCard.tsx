import React from 'react';
import { Card } from './Card';
import { Badge } from './Badge';
import { ArrowUpRight, ArrowDownRight, Minus } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  targetSubtext?: string;
  badgeText?: string;
  badgeVariant?: 'emerald' | 'amber' | 'rose' | 'accent' | 'indigo' | 'slate';
  trendText?: string;
  trendType?: 'positive' | 'negative' | 'neutral';
  comparisonSubtext?: string;
  icon?: React.ReactNode;
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  subtitle,
  targetSubtext,
  badgeText,
  badgeVariant = 'slate',
  trendText,
  trendType = 'neutral',
  comparisonSubtext,
  icon,
}) => {
  return (
    <Card className="flex flex-col justify-between">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 font-sans">{title}</span>
        <div className="flex items-center gap-1.5">
          {badgeText && <Badge variant={badgeVariant}>{badgeText}</Badge>}
          {icon && (
            <div className="p-1.5 rounded-lg bg-slate-100 text-slate-600 border border-slate-200/60">
              {icon}
            </div>
          )}
        </div>
      </div>

      <div className="my-1 flex items-baseline gap-2">
        <span className="text-3xl font-extrabold tracking-tight text-slate-900 font-sans">{value}</span>
        {targetSubtext && (
          <span className="text-xs font-medium text-slate-400">{targetSubtext}</span>
        )}
      </div>

      {(trendText || comparisonSubtext || subtitle) && (
        <div className="flex items-center justify-between text-xs pt-2 mt-1 border-t border-slate-100">
          {trendText ? (
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md font-bold text-[11px] ${
              trendType === 'positive'
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : trendType === 'negative'
                ? 'bg-rose-50 text-rose-700 border border-rose-200'
                : 'bg-slate-100 text-slate-600 border border-slate-200'
            }`}>
              {trendType === 'positive' ? (
                <ArrowUpRight className="w-3 h-3" />
              ) : trendType === 'negative' ? (
                <ArrowDownRight className="w-3 h-3" />
              ) : (
                <Minus className="w-3 h-3" />
              )}
              <span>{trendText}</span>
            </span>
          ) : (
            <span className="text-[11px] font-medium text-slate-500">{subtitle}</span>
          )}

          {comparisonSubtext && (
            <span className="text-[11px] font-medium text-slate-400">{comparisonSubtext}</span>
          )}
        </div>
      )}
    </Card>
  );
};
