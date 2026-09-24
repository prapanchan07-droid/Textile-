import React from 'react';
import { Target, TrendingDown, CheckCircle2, Percent, Activity } from 'lucide-react';
import { ProductionSummary, ProductionVariance } from '../../types/overview';
import { StatCard } from '../ui/StatCard';

interface ProductionPerformanceCardProps {
  summary: ProductionSummary;
  variance: ProductionVariance;
}

export const ProductionPerformanceCard: React.FC<ProductionPerformanceCardProps> = ({
  summary,
  variance,
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        title="TARGET PRODUCTION"
        value={`${summary.target_kg.toLocaleString()}`}
        targetSubtext="kg"
        trendText="Quota"
        trendType="neutral"
        comparisonSubtext="Planned shift target"
        icon={<Target className="w-4 h-4" />}
      />

      <StatCard
        title="ACTUAL PRODUCTION"
        value={`${summary.actual_kg.toLocaleString()}`}
        targetSubtext="kg"
        trendText="-4.1% shift"
        trendType="negative"
        comparisonSubtext="vs prev day"
        icon={<Activity className="w-4 h-4 text-blue-600" />}
      />

      <StatCard
        title="PRODUCTION LOSS"
        value={`${summary.loss_kg.toLocaleString()}`}
        targetSubtext="kg"
        trendText={`${variance.variance_pct}% gap`}
        trendType="negative"
        comparisonSubtext="Downtime & Power"
        icon={<TrendingDown className="w-4 h-4 text-rose-600" />}
      />

      <StatCard
        title="ACHIEVEMENT RATE"
        value={`${summary.achievement_pct.toFixed(1)}%`}
        targetSubtext="target 100%"
        trendText={`${summary.efficiency_pct}% eff.`}
        trendType={summary.achievement_pct >= 95 ? 'positive' : 'negative'}
        comparisonSubtext="Factory Efficiency"
        icon={<Percent className="w-4 h-4 text-amber-600" />}
      />
    </div>
  );
};
