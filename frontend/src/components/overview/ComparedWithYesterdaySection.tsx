import React from 'react';
import { Card } from '../ui/Card';
import { ComparisonPeriod, PeriodComparisonMetric } from '../../types/overview';

interface ComparedWithYesterdaySectionProps {
  metrics: PeriodComparisonMetric[];
  todayKg: number;
  comparison?: ComparisonPeriod;
}

const COMPARISON_LABELS: Record<ComparisonPeriod, { heading: string; previous: string; current: string }> = {
  PREVIOUS_SHIFT: { heading: 'PREVIOUS SHIFT', previous: 'Previous Shift', current: 'This Shift' },
  PREVIOUS_DAY: { heading: 'YESTERDAY', previous: 'Yesterday', current: 'Today' },
  PREVIOUS_WEEK: { heading: 'PREVIOUS WEEK', previous: 'Previous Week', current: 'This Week' },
  PREVIOUS_MONTH: { heading: 'PREVIOUS MONTH', previous: 'Previous Month', current: 'This Month' },
  THREE_MONTH_AVG: { heading: '3-MONTH AVERAGE', previous: '3-Month Average', current: 'Selected Period' },
};

const parseKg = (text?: string): number | null => {
  const n = parseFloat((text || '').replace(/[^0-9.]/g, ''));
  return Number.isFinite(n) ? n : null;
};

const TONES = {
  rose: { text: 'text-rose-600', badge: 'text-rose-600 bg-rose-50 border-rose-200', card: 'bg-rose-50/60 border-rose-200', label: 'text-rose-700', value: 'text-rose-700' },
  emerald: { text: 'text-emerald-600', badge: 'text-emerald-600 bg-emerald-50 border-emerald-200', card: 'bg-emerald-50/60 border-emerald-200', label: 'text-emerald-700', value: 'text-emerald-700' },
  slate: { text: 'text-slate-600', badge: 'text-slate-600 bg-slate-50 border-slate-200', card: 'bg-slate-50 border-slate-200', label: 'text-slate-600', value: 'text-slate-800' },
} as const;

const arrowFor = (trend: PeriodComparisonMetric['trend']) =>
  trend.startsWith('up') ? '↑' : trend.startsWith('down') ? '↓' : '→';

const toneFor = (trend: PeriodComparisonMetric['trend']) =>
  trend.endsWith('_bad') ? 'text-rose-600' : trend.endsWith('_good') ? 'text-emerald-600' : 'text-slate-600';

export const ComparedWithYesterdaySection: React.FC<ComparedWithYesterdaySectionProps> = ({
  metrics,
  todayKg,
  comparison = 'PREVIOUS_DAY',
}) => {
  const labels = COMPARISON_LABELS[comparison] ?? COMPARISON_LABELS.PREVIOUS_DAY;
  const volume = metrics.find((m) => m.metric === 'Production Volume');
  const previousKg = parseKg(volume?.previous);
  const hasPrevious = previousKg !== null && previousKg > 0;

  const diffKg = hasPrevious ? todayKg - (previousKg as number) : 0;
  const diffPct = hasPrevious ? (diffKg / (previousKg as number)) * 100 : 0;
  const isWorse = diffKg < 0;
  const tone = TONES[!hasPrevious ? 'slate' : isWorse ? 'rose' : 'emerald'];

  const drivers = ['Total Downtime', 'Factory Efficiency', 'Energy Consumption / kg', 'Quality Rating']
    .map((name) => metrics.find((m) => m.metric === name))
    .filter((m): m is PeriodComparisonMetric => !!m && m.change_text !== 'N/A')
    .slice(0, 3);

  return (
    <Card className="space-y-5 p-6">
      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            3. COMPARED WITH {labels.heading}
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            {hasPrevious ? (
              <>
                {labels.current} is{' '}
                <span className={tone.text}>
                  {Math.abs(diffPct).toFixed(1)}% {isWorse ? 'worse' : 'better'}
                </span>{' '}
                than {labels.previous.toLowerCase()}.
              </>
            ) : (
              <>No {labels.previous.toLowerCase()} data available for comparison.</>
            )}
          </p>
        </div>
        {hasPrevious && (
          <span className={`text-xs font-mono font-bold ${tone.badge} border px-2.5 py-1 rounded-lg`}>
            {isWorse ? '↓' : '↑'} {Math.abs(Math.round(diffKg)).toLocaleString()} kg ({diffPct.toFixed(1)}%)
          </span>
        )}
      </div>

      {/* 1-to-1 Comparison Cards */}
      <div className="grid grid-cols-2 gap-3 text-center">
        <div className="bg-slate-50 p-3.5 rounded-xl border border-slate-200">
          <div className="text-xs text-slate-500 font-medium">{labels.previous} Produced</div>
          <div className="text-xl font-extrabold text-slate-900 font-mono mt-1">
            {hasPrevious ? `${Math.round(previousKg as number).toLocaleString()} kg` : 'N/A'}
          </div>
        </div>

        <div className={`${tone.card} p-3.5 rounded-xl border`}>
          <div className={`text-xs ${tone.label} font-medium`}>{labels.current} Produced</div>
          <div className={`text-xl font-extrabold ${tone.value} font-mono mt-1`}>
            {Math.round(todayKg).toLocaleString()} kg
          </div>
        </div>
      </div>

      {/* Key Drivers for the change */}
      {drivers.length > 0 && (
        <div className="space-y-2 pt-1">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Main changes:</div>
          <div className="grid grid-cols-3 gap-2 text-xs font-medium">
            {drivers.map((d) => (
              <div key={d.metric} className="bg-slate-50 p-2.5 rounded-lg border border-slate-200 text-center">
                <span className="text-slate-500 block text-[11px]">{d.metric}</span>
                <span className={`${toneFor(d.trend)} font-bold font-mono`}>
                  {arrowFor(d.trend)} {d.change_text.replace(/^[+-]/, '')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};
