import React, { useState } from 'react';
import { DowntimeKpi, DowntimeReasonItem } from '../../types/machines';
import { Card } from '../ui/Card';
import { Clock, AlertTriangle, ShieldCheck, Activity } from 'lucide-react';

interface DowntimeAnalysisSectionProps {
  kpis: DowntimeKpi;
  reasons: DowntimeReasonItem[];
}

export const DowntimeAnalysisSection: React.FC<DowntimeAnalysisSectionProps> = ({
  kpis,
  reasons,
}) => {
  const [hoveredReason, setHoveredReason] = useState<DowntimeReasonItem | null>(null);

  const maxMin = Math.max(...reasons.map((r) => r.downtime_min), 1);

  return (
    <Card className="space-y-6 p-6 overflow-visible">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          3. DOWNTIME ANALYSIS
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          Downtime duration metrics and main stoppage root causes
        </p>
      </div>

      {/* 4 Core KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase">
            <Clock className="w-3.5 h-3.5 text-slate-600" />
            <span>TOTAL DOWNTIME</span>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            {kpis.total_downtime_min} <span className="text-xs font-normal text-slate-500">min</span>
          </div>
        </div>

        <div className="bg-rose-50/70 border border-rose-200/80 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-rose-700 uppercase">
            <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
            <span>UNPLANNED</span>
          </div>
          <div className="text-2xl font-extrabold text-rose-700 font-mono">
            {kpis.unplanned_downtime_min} <span className="text-xs font-normal text-rose-500">min</span>
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase">
            <ShieldCheck className="w-3.5 h-3.5 text-slate-600" />
            <span>PLANNED</span>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            {kpis.planned_downtime_min} <span className="text-xs font-normal text-slate-500">min</span>
          </div>
        </div>

        <div className="bg-slate-50 border border-slate-200 rounded-xl p-3.5 space-y-1">
          <div className="flex items-center gap-1.5 text-[10px] font-bold text-slate-500 uppercase">
            <Activity className="w-3.5 h-3.5 text-slate-600" />
            <span>STOPPAGES</span>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 font-mono">
            {kpis.stoppage_count} <span className="text-xs font-normal text-slate-500">events</span>
          </div>
        </div>
      </div>

      {/* Downtime By Reason (Horizontal Bar Chart) */}
      <div className="space-y-3 pt-2 border-t border-slate-100">
        <div className="text-xs font-bold text-slate-700 uppercase tracking-wider">
          Main Causes of Downtime
        </div>

        <div className="space-y-3">
          {reasons.map((r) => {
            const widthPct = Math.max(6, (r.downtime_min / maxMin) * 100);
            const isHovered = hoveredReason?.category === r.category;

            return (
              <div
                key={r.category}
                onMouseEnter={() => setHoveredReason(r)}
                onMouseLeave={() => setHoveredReason(null)}
                className="relative flex items-center gap-3 cursor-pointer group text-xs"
              >
                {/* Category Label */}
                <div className="w-36 font-semibold text-slate-700 shrink-0 truncate">
                  {r.category}
                </div>

                {/* Horizontal Bar */}
                <div className="flex-1 bg-slate-100 rounded-lg h-7 p-1 border border-slate-200/80 flex items-center relative">
                  <div
                    className="bg-slate-800 group-hover:bg-slate-900 h-full rounded-md transition-all duration-300 flex items-center justify-end pr-2.5 text-[11px] font-bold text-white shadow-sm"
                    style={{ width: `${widthPct}%` }}
                  >
                    <span className="font-mono">{r.downtime_min} min</span>
                  </div>
                </div>

                {/* Percentage */}
                <div className="w-14 text-right font-mono font-bold text-slate-600 shrink-0">
                  {r.percentage.toFixed(1)}%
                </div>

                {/* Instant Custom Tooltip Overlay */}
                {isHovered && (
                  <div className="absolute bottom-full mb-2.5 left-1/2 -translate-x-1/2 z-50 pointer-events-none w-60 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left animate-in fade-in zoom-in-95 duration-75 font-sans">
                    <div className="border-b border-slate-100 pb-1.5 mb-2 text-xs font-bold text-slate-900">
                      Reason: {r.category}
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Downtime Duration:</span>
                        <span className="font-mono font-bold text-rose-600">
                          {r.downtime_min} min
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Downtime Contribution:</span>
                        <span className="font-mono font-bold text-slate-900">
                          {r.percentage.toFixed(1)}%
                        </span>
                      </div>
                    </div>

                    {/* Tooltip pointer arrow */}
                    <div className="absolute -bottom-1.5 left-1/2 -translate-x-1/2 w-3 h-3 bg-white rotate-45 border-r border-b border-slate-200" />
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
};
