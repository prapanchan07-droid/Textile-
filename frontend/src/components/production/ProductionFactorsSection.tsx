import React from 'react';
import { ProductionFactorItem } from '../../types/production';
import { Card } from '../ui/Card';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';

interface ProductionFactorsSectionProps {
  factors?: ProductionFactorItem[];
}

export const ProductionFactorsSection: React.FC<ProductionFactorsSectionProps> = ({ factors }) => {
  const defaultFactors: ProductionFactorItem[] = [
    { name: 'Downtime', display_value: '112 min', direction: 'UP', status: 'CRITICAL' },
    { name: 'Efficiency', display_value: '3.2 pts', direction: 'DOWN', status: 'ATTENTION' },
    { name: 'Power Events', display_value: '2', direction: 'UP', status: 'ATTENTION' },
    { name: 'Warp Breaks', display_value: '8%', direction: 'UP', status: 'ATTENTION' },
    { name: 'Weft Breaks', display_value: '3%', direction: 'DOWN', status: 'HEALTHY' },
  ];

  const activeFactors = factors && factors.length > 0 ? factors : defaultFactors;

  return (
    <Card className="p-5 space-y-4">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          PRODUCTION FACTORS
        </h2>
        <p className="text-xs text-slate-500 font-medium mt-0.5">
          Key operational factors driving immediate production performance
        </p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-1">
        {activeFactors.map((item) => {
          const isUp = item.direction === 'UP';
          const isCritical = item.status === 'CRITICAL';
          const isAttention = item.status === 'ATTENTION';
          const isHealthy = item.status === 'HEALTHY';

          const textColor = isCritical
            ? 'text-red-600'
            : isAttention
            ? 'text-amber-600'
            : isHealthy
            ? 'text-emerald-600'
            : 'text-slate-900';

          const badgeBg = isCritical
            ? 'bg-red-50 text-red-700 border-red-200'
            : isAttention
            ? 'bg-amber-50 text-amber-700 border-amber-200'
            : 'bg-emerald-50 text-emerald-700 border-emerald-200';

          return (
            <div
              key={item.name}
              className="bg-slate-50 border border-slate-200/80 rounded-xl p-3 space-y-1.5"
            >
              <span className="text-[11px] font-bold text-slate-400 block uppercase tracking-wider">
                {item.name}
              </span>
              <div className="flex items-center justify-between">
                <span className={`text-base font-black font-mono ${textColor}`}>
                  {item.display_value}
                </span>
                <span className={`inline-flex items-center p-1 rounded-md border text-[11px] font-bold ${badgeBg}`}>
                  {isUp ? <ArrowUpRight className="w-3.5 h-3.5" /> : <ArrowDownRight className="w-3.5 h-3.5" />}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
};
