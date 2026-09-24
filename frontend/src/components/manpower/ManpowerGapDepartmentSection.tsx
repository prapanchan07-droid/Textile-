import React, { useState } from 'react';
import { DepartmentManpowerItem } from '../../types/manpowerQuality';
import { Card } from '../ui/Card';

interface ManpowerGapDepartmentSectionProps {
  departments: DepartmentManpowerItem[];
}

export const ManpowerGapDepartmentSection: React.FC<ManpowerGapDepartmentSectionProps> = ({
  departments,
}) => {
  const [hoveredDept, setHoveredDept] = useState<DepartmentManpowerItem | null>(null);

  // Sort by largest negative gap first
  const sortedDepts = [...departments].sort((a, b) => a.gap - b.gap);
  const maxGap = Math.max(...sortedDepts.map((d) => Math.abs(d.gap)), 1);

  const formatGapLabel = (gap: number): string => {
    const absGap = Math.abs(gap);
    const noun = absGap === 1 ? 'worker' : 'workers';
    return `-${absGap} ${noun}`;
  };

  return (
    <Card className="space-y-5 p-6 overflow-visible">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          2. MANPOWER GAP BY DEPARTMENT
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          Departments experiencing workforce shortages
        </p>
      </div>

      <div className="space-y-3 pt-1">
        {sortedDepts.map((d) => {
          const absGap = Math.abs(d.gap);
          const widthPct = Math.max(4, (absGap / maxGap) * 100);
          const isWideBar = widthPct >= 32;
          const labelText = formatGapLabel(d.gap);
          const isHovered = hoveredDept?.department === d.department;

          const barColorClass =
            absGap >= 20
              ? 'bg-rose-600 group-hover:bg-rose-700'
              : absGap >= 10
              ? 'bg-amber-600 group-hover:bg-amber-700'
              : 'bg-slate-600 group-hover:bg-slate-700';

          return (
            <div
              key={d.department}
              onMouseEnter={() => setHoveredDept(d)}
              onMouseLeave={() => setHoveredDept(null)}
              className="relative flex items-center gap-3 cursor-pointer group text-xs"
            >
              {/* Department Name */}
              <div className="w-32 font-bold text-slate-900 truncate shrink-0">
                {d.department}
              </div>

              {/* Horizontal Bar Track */}
              <div className="flex-1 bg-slate-100 rounded-lg h-7 p-1 border border-slate-200/80 flex items-center relative overflow-hidden">
                {/* Visual Colored Bar */}
                <div
                  className={`h-full rounded-md transition-all duration-300 flex items-center ${
                    isWideBar ? 'justify-end pr-2.5' : 'justify-start'
                  } ${barColorClass}`}
                  style={{ width: `${widthPct}%` }}
                >
                  {isWideBar && (
                    <span className="font-mono text-[11px] font-bold text-white whitespace-nowrap">
                      {labelText}
                    </span>
                  )}
                </div>

                {/* Outside Label for Narrow Bars */}
                {!isWideBar && (
                  <span className="font-mono text-[11px] font-bold text-slate-800 whitespace-nowrap ml-2">
                    {labelText}
                  </span>
                )}
              </div>

              {/* Attendance % (Consistently Aligned on Far Right) */}
              <div className="w-16 text-right font-mono font-bold text-slate-600 shrink-0">
                {d.attendance_pct}%
              </div>

              {/* Instant Custom Tooltip Overlay */}
              {isHovered && (
                <div className="absolute bottom-full mb-2.5 left-1/2 -translate-x-1/2 z-50 pointer-events-none w-60 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left animate-in fade-in zoom-in-95 duration-75 font-sans">
                  <div className="border-b border-slate-100 pb-1.5 mb-2 font-bold text-xs text-slate-900">
                    Department: {d.department}
                  </div>

                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Required:</span>
                      <span className="font-mono font-bold text-slate-900">{d.required}</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Available:</span>
                      <span className="font-mono font-bold text-blue-600">{d.available}</span>
                    </div>

                    <div className="flex justify-between items-center border-t border-slate-100 pt-1.5">
                      <span className="text-slate-500">Shortage / Gap:</span>
                      <span className="font-mono font-bold text-rose-600">{labelText}</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Attendance Rate:</span>
                      <span className="font-mono font-bold text-slate-900">{d.attendance_pct}%</span>
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
    </Card>
  );
};
