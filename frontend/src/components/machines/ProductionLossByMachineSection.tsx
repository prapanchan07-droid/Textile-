import React, { useState } from 'react';
import { MachinePerformanceItem } from '../../types/machines';
import { Card } from '../ui/Card';

interface ProductionLossByMachineSectionProps {
  machines: MachinePerformanceItem[];
}

export const ProductionLossByMachineSection: React.FC<ProductionLossByMachineSectionProps> = ({
  machines,
}) => {
  const [hoveredMachine, setHoveredMachine] = useState<MachinePerformanceItem | null>(null);

  // Sort machines by loss descending
  const sortedMachines = [...machines].sort((a, b) => b.loss_kg - a.loss_kg);
  const maxLoss = sortedMachines[0]?.loss_kg || 1000;

  return (
    <Card className="space-y-5 p-6 overflow-visible">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          2. PRODUCTION LOSS BY MACHINE
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          Individual machines responsible for the largest production losses
        </p>
      </div>

      <div className="space-y-3.5 pt-1">
        {sortedMachines.map((m) => {
          const widthPct = Math.max(8, (m.loss_kg / maxLoss) * 100);
          const isHovered = hoveredMachine?.machine_id === m.machine_id;

          return (
            <div
              key={m.machine_id}
              onMouseEnter={() => setHoveredMachine(m)}
              onMouseLeave={() => setHoveredMachine(null)}
              className="relative flex items-center gap-3 cursor-pointer group"
            >
              {/* Machine ID */}
              <div className="w-16 text-xs font-extrabold text-slate-900 font-mono shrink-0">
                {m.machine_id}
              </div>

              {/* Bar Viewport */}
              <div className="flex-1 bg-slate-100 rounded-lg h-7 p-1 border border-slate-200/80 flex items-center relative">
                <div
                  className={`h-full rounded-md transition-all duration-300 flex items-center justify-end pr-2.5 text-[11px] font-bold text-white shadow-sm ${
                    m.status === 'CRITICAL'
                      ? 'bg-rose-600 group-hover:bg-rose-700'
                      : m.status === 'ATTENTION'
                      ? 'bg-amber-600 group-hover:bg-amber-700'
                      : 'bg-blue-600 group-hover:bg-blue-700'
                  }`}
                  style={{ width: `${widthPct}%` }}
                >
                  <span className="font-mono">{m.loss_kg.toLocaleString()} kg</span>
                </div>
              </div>

              {/* Machine Type */}
              <div className="w-20 text-[11px] text-slate-500 font-medium text-right shrink-0">
                {m.machine_type}
              </div>

              {/* Instant Custom Tooltip Overlay */}
              {isHovered && (
                <div className="absolute bottom-full mb-2.5 left-1/2 -translate-x-1/2 z-50 pointer-events-none w-64 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left animate-in fade-in zoom-in-95 duration-75 font-sans">
                  <div className="border-b border-slate-100 pb-2 mb-2 flex justify-between items-center">
                    <span className="text-xs font-bold text-slate-900 font-mono">
                      Machine: {m.machine_id}
                    </span>
                    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-slate-100 text-slate-700">
                      {m.machine_type}
                    </span>
                  </div>

                  <div className="space-y-1.5 text-xs">
                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Production Loss:</span>
                      <span className="font-mono font-bold text-rose-600">
                        {m.loss_kg.toLocaleString()} kg
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Efficiency:</span>
                      <span className="font-mono font-bold text-slate-900">
                        {m.efficiency_pct}%
                      </span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-slate-500">Downtime:</span>
                      <span className="font-mono font-bold text-amber-700">
                        {m.downtime_min} min
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
    </Card>
  );
};
