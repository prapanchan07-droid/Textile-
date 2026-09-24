import React, { useEffect, useState } from 'react';
import { ProductionPerformanceSection } from '../components/production/ProductionPerformanceSection';
import { ProductionLossReasonsSection } from '../components/production/ProductionLossReasonsSection';
import { MachineTypePerformanceSection } from '../components/production/MachineTypePerformanceSection';
import { ShiftPerformanceSection } from '../components/production/ShiftPerformanceSection';
import { ProductionFactorsSection } from '../components/production/ProductionFactorsSection';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Card } from '../components/ui/Card';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { productionService } from '../services/productionService';
import { ProductionModuleData } from '../types/production';

export const ProductionPage: React.FC = () => {
  const [data, setData] = useState<ProductionModuleData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchProductionData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await productionService.getProductionData();
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load Production Module data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProductionData();

    const handleReportUploaded = () => {
      fetchProductionData();
    };

    window.addEventListener('reportUploaded', handleReportUploaded);
    return () => {
      window.removeEventListener('reportUploaded', handleReportUploaded);
    };
  }, []);

  if (loading) {
    return <LoadingSpinner label="Loading production analytics and performance drivers..." />;
  }

  if (error) {
    return (
      <Card variant="outline" className="border-rose-300 bg-rose-50/50 p-6">
        <div className="flex items-center gap-3 text-rose-700">
          <AlertCircle className="w-6 h-6 shrink-0" />
          <div className="flex-1">
            <h3 className="font-bold text-slate-900">Production Module Connection Error</h3>
            <p className="text-xs text-rose-600">{error}</p>
          </div>
          <button
            onClick={fetchProductionData}
            className="px-3.5 py-2 bg-rose-600 text-white text-xs font-bold rounded-lg hover:bg-rose-700 transition-colors flex items-center gap-1.5 cursor-pointer"
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
    <div className="space-y-6 pb-12">
      {/* 1. COMPACT PRODUCTION KPI & VISUALIZATION */}
      <ProductionPerformanceSection
        actualKg={data.actual_kg}
        targetKg={data.target_kg}
        gapKg={data.gap_kg}
        achievementPct={data.achievement_pct}
        shiftPerformance={data.shift_performance}
      />

      {/* 2. TWO-COLUMN ANALYTICAL GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* WHERE IS PRODUCTION LOSS? */}
        <ProductionLossReasonsSection reasons={data.loss_reasons} />

        {/* PRODUCTION BY MACHINE TYPE */}
        <MachineTypePerformanceSection machineTypes={data.machine_type_performance} />
      </div>

      {/* 4. SHIFT PERFORMANCE */}
      <ShiftPerformanceSection shifts={data.shift_performance} />

      {/* 5. PRODUCTION FACTORS */}
      <ProductionFactorsSection factors={data.production_factors} />
    </div>
  );
};

export default ProductionPage;
