import React, { useState } from 'react';
import { MachineTypePerformanceItem } from '../../types/production';
import { Card } from '../ui/Card';

interface MachineTypePerformanceSectionProps {
  machineTypes: MachineTypePerformanceItem[];
}

export const MachineTypePerformanceSection: React.FC<MachineTypePerformanceSectionProps> = ({
  machineTypes,
}) => {
  const [selectedMetric, setSelectedMetric] = useState<'PRODUCTION' | 'ACHIEVEMENT' | 'EFFICIENCY' | 'LOSS'>('PRODUCTION');

  const getMetricValue = (item: MachineTypePerformanceItem) => {
    switch (selectedMetric) {
      case 'PRODUCTION':
        return { val: item.actual_kg, fmt: `${item.actual_kg.toLocaleString()} kg`, max: 15000, pct: (item.actual_kg / 15000) * 100 };
      case 'ACHIEVEMENT':
        const ach = item.target_kg > 0 ? (item.actual_kg / item.target_kg) * 100 : 90;
        return { val: ach, fmt: `${ach.toFixed(1)}%`, max: 100, pct: ach };
      case 'EFFICIENCY':
        return { val: item.efficiency_pct, fmt: `${item.efficiency_pct.toFixed(1)}%`, max: 100, pct: item.efficiency_pct };
      case 'LOSS':
        return { val: item.loss_kg, fmt: `${item.loss_kg.toLocaleString()} kg`, max: 1500, pct: (item.loss_kg / 1500) * 100 };
    }
  };

  return (
    <Card className="p-5 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            PRODUCTION BY MACHINE TYPE
          </h2>
          <p className="text-xs text-slate-500 font-medium mt-0.5">
            Aggregated performance by machinery classification
          </p>
        </div>

        <select
          value={selectedMetric}
          onChange={(e) => setSelectedMetric(e.target.value as any)}
          className="bg-slate-50 border border-slate-200 text-slate-900 font-bold text-xs px-3 py-1.5 rounded-xl focus:outline-hidden cursor-pointer"
        >
          <option value="PRODUCTION">Production (kg)</option>
          <option value="ACHIEVEMENT">Target Achievement (%)</option>
          <option value="EFFICIENCY">Efficiency (%)</option>
          <option value="LOSS">Production Loss (kg)</option>
        </select>
      </div>

      <div className="space-y-3 pt-1">
        {machineTypes.map((item) => {
          const metricData = getMetricValue(item);
          const barBg = selectedMetric === 'LOSS' ? 'bg-red-500' : 'bg-blue-600';

          return (
            <div key={item.machine_type} className="space-y-1">
              <div className="flex items-center justify-between text-xs font-bold text-slate-900">
                <span>{item.machine_type}</span>
                <span className="font-mono">{metricData.fmt}</span>
              </div>

              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden p-0.5 border border-slate-200/80">
                <div
                  className={`${barBg} h-full rounded-full transition-all duration-500`}
                  style={{ width: `${Math.min(100, metricData.pct)}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
