import React, { useState } from 'react';
import { MachineTrendPoint } from '../../types/machines';
import { Card } from '../ui/Card';

interface MachineTrendSectionProps {
  trend: MachineTrendPoint[];
  selectedMachineId?: string;
  onMachineIdChange?: (id: string) => void;
  availableMachineIds?: string[];
  trendsById?: Record<string, MachineTrendPoint[]>;
}

const ALL_MASTER_MACHINES = ['V-09', 'V-05', 'SMX-03', 'V-12', 'RF-04', 'A-02'];

const DEFAULT_TREND_MAP: Record<string, MachineTrendPoint[]> = {
  'V-09': [
    { date_label: 'Sep 16', efficiency_pct: 89.2, loss_kg: 480 },
    { date_label: 'Sep 17', efficiency_pct: 87.5, loss_kg: 540 },
    { date_label: 'Sep 18', efficiency_pct: 91.0, loss_kg: 390 },
    { date_label: 'Sep 19', efficiency_pct: 82.1, loss_kg: 780 },
    { date_label: 'Sep 20', efficiency_pct: 88.4, loss_kg: 510 },
    { date_label: 'Sep 21', efficiency_pct: 86.0, loss_kg: 600 },
    { date_label: 'Sep 22', efficiency_pct: 84.2, loss_kg: 680 },
  ],
  'V-05': [
    { date_label: 'Sep 16', efficiency_pct: 91.5, loss_kg: 320 },
    { date_label: 'Sep 17', efficiency_pct: 90.0, loss_kg: 360 },
    { date_label: 'Sep 18', efficiency_pct: 89.2, loss_kg: 410 },
    { date_label: 'Sep 19', efficiency_pct: 87.0, loss_kg: 460 },
    { date_label: 'Sep 20', efficiency_pct: 88.5, loss_kg: 400 },
    { date_label: 'Sep 21', efficiency_pct: 89.0, loss_kg: 380 },
    { date_label: 'Sep 22', efficiency_pct: 88.1, loss_kg: 420 },
  ],
  'SMX-03': [
    { date_label: 'Sep 16', efficiency_pct: 92.0, loss_kg: 240 },
    { date_label: 'Sep 17', efficiency_pct: 91.8, loss_kg: 250 },
    { date_label: 'Sep 18', efficiency_pct: 89.5, loss_kg: 310 },
    { date_label: 'Sep 19', efficiency_pct: 90.0, loss_kg: 290 },
    { date_label: 'Sep 20', efficiency_pct: 91.2, loss_kg: 260 },
    { date_label: 'Sep 21', efficiency_pct: 89.8, loss_kg: 300 },
    { date_label: 'Sep 22', efficiency_pct: 90.5, loss_kg: 290 },
  ],
  'V-12': [
    { date_label: 'Sep 16', efficiency_pct: 94.5, loss_kg: 150 },
    { date_label: 'Sep 17', efficiency_pct: 95.0, loss_kg: 140 },
    { date_label: 'Sep 18', efficiency_pct: 93.0, loss_kg: 190 },
    { date_label: 'Sep 19', efficiency_pct: 94.2, loss_kg: 160 },
    { date_label: 'Sep 20', efficiency_pct: 93.8, loss_kg: 170 },
    { date_label: 'Sep 21', efficiency_pct: 94.0, loss_kg: 165 },
    { date_label: 'Sep 22', efficiency_pct: 93.5, loss_kg: 180 },
  ],
  'RF-04': [
    { date_label: 'Sep 16', efficiency_pct: 96.0, loss_kg: 220 },
    { date_label: 'Sep 17', efficiency_pct: 95.5, loss_kg: 240 },
    { date_label: 'Sep 18', efficiency_pct: 94.2, loss_kg: 310 },
    { date_label: 'Sep 19', efficiency_pct: 95.0, loss_kg: 280 },
    { date_label: 'Sep 20', efficiency_pct: 94.0, loss_kg: 320 },
    { date_label: 'Sep 21', efficiency_pct: 95.2, loss_kg: 260 },
    { date_label: 'Sep 22', efficiency_pct: 94.8, loss_kg: 300 },
  ],
  'A-02': [
    { date_label: 'Sep 16', efficiency_pct: 96.2, loss_kg: 200 },
    { date_label: 'Sep 17', efficiency_pct: 95.8, loss_kg: 220 },
    { date_label: 'Sep 18', efficiency_pct: 96.0, loss_kg: 210 },
    { date_label: 'Sep 19', efficiency_pct: 94.8, loss_kg: 270 },
    { date_label: 'Sep 20', efficiency_pct: 95.5, loss_kg: 230 },
    { date_label: 'Sep 21', efficiency_pct: 95.0, loss_kg: 260 },
    { date_label: 'Sep 22', efficiency_pct: 95.2, loss_kg: 250 },
  ],
};

export const MachineTrendSection: React.FC<MachineTrendSectionProps> = ({
  trend,
  selectedMachineId = 'V-09',
  onMachineIdChange,
  availableMachineIds,
  trendsById,
}) => {
  const [localMachineId, setLocalMachineId] = useState<string>(
    selectedMachineId && selectedMachineId !== 'ALL' ? selectedMachineId : 'V-09'
  );
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  // Machine options list: ALWAYS complete master list to ensure options never shrink
  const machineOptions =
    availableMachineIds && availableMachineIds.filter((id) => id !== 'ALL').length > 0
      ? Array.from(new Set([...availableMachineIds.filter((id) => id !== 'ALL'), ...ALL_MASTER_MACHINES]))
      : ALL_MASTER_MACHINES;

  // Active trend data map
  const activeTrendMap = trendsById || DEFAULT_TREND_MAP;
  const activePoints = activeTrendMap[localMachineId] || trend || DEFAULT_TREND_MAP['V-09'];

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newId = e.target.value;
    setLocalMachineId(newId);
    if (onMachineIdChange) {
      onMachineIdChange(newId);
    }
  };

  return (
    <Card className="space-y-5 p-6 overflow-visible">
      {/* Header & Machine Dropdown */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            4. MACHINE PERFORMANCE TREND
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            Track efficiency trends for individual machines over time
          </p>
        </div>

        {/* Client-Side Machine Dropdown */}
        <div className="flex items-center gap-2 bg-slate-100 p-1.5 px-3 rounded-lg border border-slate-200 text-xs font-semibold text-slate-700">
          <span>Machine:</span>
          <select
            value={localMachineId}
            onChange={handleSelectChange}
            className="bg-transparent font-bold text-slate-900 font-mono focus:outline-none cursor-pointer"
          >
            {machineOptions.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Vertical Bar Trend Chart Viewport */}
      <div className="relative pt-3 pb-1">
        <div className="flex items-end justify-around h-48 border-b border-slate-200 px-4">
          {activePoints.map((point, idx) => {
            const heightPct = (point.efficiency_pct / 100) * 100;
            const isHovered = hoveredIdx === idx;

            return (
              <div
                key={idx}
                onMouseEnter={() => setHoveredIdx(idx)}
                onMouseLeave={() => setHoveredIdx(null)}
                className="relative flex flex-col items-center h-full justify-end cursor-pointer group flex-1 max-w-[60px]"
              >
                {/* Vertical Bar */}
                <div
                  className={`w-4 sm:w-6 rounded-t-sm transition-all duration-150 ${
                    point.efficiency_pct >= 90
                      ? 'bg-blue-600 group-hover:bg-blue-700'
                      : 'bg-amber-600 group-hover:bg-amber-700'
                  }`}
                  style={{ height: `${heightPct}%` }}
                />

                {/* Instant Custom Tooltip Overlay */}
                {isHovered && (
                  <div className="absolute bottom-full mb-3 left-1/2 -translate-x-1/2 z-50 pointer-events-none w-56 bg-white border border-slate-200 rounded-xl p-3.5 shadow-xl text-left animate-in fade-in zoom-in-95 duration-75 font-sans">
                    <div className="border-b border-slate-100 pb-1.5 mb-2 flex justify-between items-center text-xs font-bold text-slate-900">
                      <span>{point.date_label}</span>
                      <span className="font-mono text-slate-500">{localMachineId}</span>
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Efficiency:</span>
                        <span className="font-mono font-bold text-slate-900">
                          {point.efficiency_pct}%
                        </span>
                      </div>

                      <div className="flex justify-between items-center">
                        <span className="text-slate-500">Production Loss:</span>
                        <span className="font-mono font-bold text-rose-600">
                          {point.loss_kg.toLocaleString()} kg
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

        {/* Date Labels */}
        <div className="flex justify-around pt-2 text-[11px] font-bold text-slate-500 font-mono">
          {activePoints.map((point, idx) => (
            <div key={idx} className="text-center flex-1 max-w-[60px]">
              {point.date_label}
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};
