import React from 'react';
import { Activity } from 'lucide-react';
import { ProductionTrendItem } from '../../types/overview';
import { Card } from '../ui/Card';

interface ProductionTrendChartProps {
  trend: ProductionTrendItem[];
}

export const ProductionTrendChart: React.FC<ProductionTrendChartProps> = ({ trend }) => {
  return (
    <Card className="space-y-4">
      <div className="flex items-center justify-between border-b border-slate-100 pb-3">
        <div>
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-600" />
            <h3 className="font-bold text-slate-900 text-base">Production Output Velocity & Traversal Trend</h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">Real-time shift output wave and gap traversal metrics</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="w-2 h-2 rounded-full bg-indigo-600" />
          <span className="text-slate-600 font-semibold">Live Buffer: 41.2 ms</span>
        </div>
      </div>

      {/* SVG Smooth Wave Velocity Curve */}
      <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 space-y-4">
        <div className="relative h-24 w-full">
          <svg className="w-full h-full overflow-visible" viewBox="0 0 500 80" preserveAspectRatio="none">
            <defs>
              <linearGradient id="waveGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#4f46e5" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#4f46e5" stopOpacity="0.0" />
              </linearGradient>
            </defs>
            <path
              d="M 0 50 Q 125 10 250 55 T 500 30 L 500 80 L 0 80 Z"
              fill="url(#waveGradient)"
            />
            <path
              d="M 0 50 Q 125 10 250 55 T 500 30"
              fill="none"
              stroke="#0f172a"
              strokeWidth="2.5"
            />
          </svg>
        </div>

        {/* Shift Detail Chips */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {trend.map((item, idx) => {
            const achievementPct = (item.actual_kg / item.target_kg) * 100;
            return (
              <div key={idx} className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm space-y-1.5">
                <div className="flex justify-between items-center text-xs font-bold text-slate-900">
                  <span>{item.label}</span>
                  <span className="font-mono text-emerald-600">{achievementPct.toFixed(1)}%</span>
                </div>
                <div className="flex justify-between items-center text-xs text-slate-500 font-mono">
                  <span>Target: {item.target_kg.toLocaleString()} kg</span>
                  <span className="font-bold text-slate-800">Actual: {item.actual_kg.toLocaleString()} kg</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full rounded-full"
                    style={{ width: `${Math.min(100, achievementPct)}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Card>
  );
};
