import React from 'react';
import { ProductionTodaySection } from '../components/overview/ProductionTodaySection';
import { WhyIsProductionLowSection } from '../components/overview/WhyIsProductionLowSection';
import { ComparedWithYesterdaySection } from '../components/overview/ComparedWithYesterdaySection';
import { MachineNeedingAttentionSection } from '../components/overview/MachineNeedingAttentionSection';
import { AiRecommendationSection } from '../components/overview/AiRecommendationSection';
import { IfThisContinuesSection } from '../components/overview/IfThisContinuesSection';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Card } from '../components/ui/Card';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { FactoryOverviewData } from '../types/overview';

interface FactoryOverviewPageProps {
  data: FactoryOverviewData | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
}

export const FactoryOverviewPage: React.FC<FactoryOverviewPageProps> = ({
  data,
  loading,
  error,
  onRetry,
}) => {
  const handleViewDetails = () => {
    alert("Machine V-09 detailed downtime telemetry will open when Module 08 (Machines & Downtime) is built.");
  };

  if (loading) {
    return <LoadingSpinner label="Loading factory summary..." />;
  }

  if (error) {
    return (
      <Card variant="outline" className="border-rose-300 bg-rose-50/50 p-6">
        <div className="flex items-center gap-3 text-rose-700">
          <AlertCircle className="w-6 h-6 shrink-0" />
          <div className="flex-1">
            <h3 className="font-bold text-slate-900">Overview Connection Error</h3>
            <p className="text-xs text-rose-600">{error}</p>
          </div>
          <button
            onClick={onRetry}
            className="px-3.5 py-2 bg-rose-600 text-white text-xs font-bold rounded-lg hover:bg-rose-700 transition-colors flex items-center gap-1.5"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Retry
          </button>
        </div>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6">
      {/* 1. PRODUCTION TODAY */}
      <ProductionTodaySection
        summary={data.production_summary}
        variance={data.variance}
      />

      {/* 2. WHY IS PRODUCTION LOW? & 3. COMPARED WITH YESTERDAY */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <WhyIsProductionLowSection
          contributors={data.loss_contributors}
          totalLossKg={data.production_summary.loss_kg}
        />
        <ComparedWithYesterdaySection
          yesterdayKg={36100}
          todayKg={data.production_summary.actual_kg}
        />
      </div>

      {/* 4. MACHINE NEEDING ATTENTION */}
      <MachineNeedingAttentionSection
        machines={data.machines_requiring_attention}
        onViewMachineDetails={handleViewDetails}
      />

      {/* 5. AI RECOMMENDATION (WHAT SHOULD I DO?) */}
      <AiRecommendationSection
        onViewDetails={handleViewDetails}
      />

      {/* 6. IF THIS CONTINUES */}
      <IfThisContinuesSection
        dailyGapKg={data.production_summary.loss_kg}
        projected7dKg={data.impact_projection.projected_7d_gap_kg}
        projected30dKg={data.impact_projection.projected_30d_gap_kg}
      />
    </div>
  );
};
