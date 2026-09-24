import React, { useState, useRef } from 'react';
import { MachineMetricValue } from '../../types/machineComparison';
import { BarChart3 } from 'lucide-react';

interface PrimaryComparisonChartProps {
  metrics: MachineMetricValue[];
  metricName: string;
  referenceFormatted: string;
  referenceValue: number;
}

export const PrimaryComparisonChart: React.FC<PrimaryComparisonChartProps> = ({
  metrics,
  metricName,
  referenceFormatted,
  referenceValue,
}) => {
  const [activeHoverId, setActiveHoverId] = useState<string | null>(null);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  if (!metrics || metrics.length === 0) return null;

  // Find max value for bar scaling
  const maxVal = Math.max(...metrics.map((m) => m.value), referenceValue, 1.0) * 1.1;

  const handleMouseEnter = (id: string) => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = setTimeout(() => {
      setActiveHoverId(id);
    }, 100);
  };

  const handleMouseLeave = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setActiveHoverId(null);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <BarChart3 className="w-4 h-4 text-blue-600" />
            <h3 className="text-base font-bold text-slate-900 uppercase tracking-tight">
              {metricName} Comparison
            </h3>
          </div>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Comparing {metrics.length} selected machine{metrics.length > 1 ? 's' : ''}
          </p>
        </div>

        {referenceValue > 0 && (
          <div className="inline-flex items-center gap-2 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-xl text-xs font-semibold text-slate-700">
            <span className="w-2.5 h-0.5 bg-slate-800 rounded-full"></span>
            <span>Ref Line: <strong className="font-mono text-slate-900">{referenceFormatted}</strong></span>
          </div>
        )}
      </div>

      {/* Horizontal Bar Chart Items */}
      <div className="space-y-4 relative">
        {metrics.map((item) => {
          const barPct = Math.min(100, (item.value / maxVal) * 100);
          const isHovered = activeHoverId === item.machine_id;

          const barBg =
            item.status === 'CRITICAL'
              ? 'bg-red-500'
              : item.status === 'ATTENTION'
              ? 'bg-amber-500'
              : 'bg-blue-600';

          return (
            <div
              key={item.machine_id}
              className="space-y-1.5 relative group"
              onMouseEnter={() => handleMouseEnter(item.machine_id)}
              onMouseLeave={handleMouseLeave}
            >
              {/* Tooltip Overlay */}
              {isHovered && (
                <div className="absolute -top-12 left-1/3 z-50 pointer-events-none bg-white text-slate-900 text-xs font-semibold p-2.5 rounded-xl shadow-xl border border-slate-200 whitespace-nowrap space-y-0.5">
                  <div className="font-bold text-slate-900">{item.machine_id} ({item.machine_type})</div>
                  <div className="text-blue-600 font-mono font-bold">{metricName}: {item.formatted_value}</div>
                  <div className="text-[11px] text-slate-500 font-mono">{item.variance_label}</div>
                  <div className="absolute -bottom-1 left-4 w-2 h-2 bg-white rotate-45 border-r border-b border-slate-200" />
                </div>
              )}

              <div className="flex items-center justify-between text-xs sm:text-sm font-bold text-slate-900">
                <div className="flex items-center gap-2">
                  <span className="font-extrabold">{item.machine_id}</span>
                  <span className="text-xs font-semibold text-slate-400 font-mono">({item.machine_type})</span>
                </div>
                <div className="flex items-center gap-3">
                  {item.variance_vs_reference !== undefined && (
                    <span
                      className={`text-xs font-mono font-semibold ${
                        item.variance_vs_reference < 0 ? 'text-red-600' : 'text-emerald-600'
                      }`}
                    >
                      {item.variance_vs_reference > 0 ? '+' : ''}
                      {item.variance_vs_reference.toFixed(1)}
                    </span>
                  )}
                  <span className="font-mono text-base font-extrabold text-slate-900">{item.formatted_value}</span>
                </div>
              </div>

              {/* Bar Container */}
              <div className="w-full bg-slate-100 rounded-xl h-7 p-1 border border-slate-200/80 relative flex items-center overflow-hidden">
                <div
                  className={`${barBg} h-full rounded-lg transition-all duration-500 flex items-center justify-end pr-3 shadow-xs`}
                  style={{ width: `${barPct}%` }}
                >
                  {barPct > 25 && (
                    <span className="text-[11px] font-bold text-white font-mono">
                      {item.formatted_value}
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}

        {/* Reference Baseline Overlay Vertical Tick Line */}
        {referenceValue > 0 && (
          <div
            className="absolute top-0 bottom-0 border-r-2 border-dashed border-slate-800 pointer-events-none z-10"
            style={{ left: `${Math.min(95, (referenceValue / maxVal) * 100)}%` }}
          />
        )}
      </div>
    </div>
  );
};
