import React, { useState, useEffect } from 'react';
import { MachineComparisonResponse } from '../types/machineComparison';
import { machineComparisonService } from '../services/machineComparisonService';

import { ComparisonControls } from '../components/comparison/ComparisonControls';
import { PrimaryComparisonChart } from '../components/comparison/PrimaryComparisonChart';
import { HeadToHeadComparison } from '../components/comparison/HeadToHeadComparison';
import { MultiMetricComparison } from '../components/comparison/MultiMetricComparison';
import { ComparisonInsight } from '../components/comparison/ComparisonInsight';
import { Loader2, BarChart2, PlusCircle } from 'lucide-react';

export const MachineComparisonPage: React.FC = () => {
  const [selectedIds, setSelectedIds] = useState<string[]>(['V-09', 'V-05', 'V-12']);
  const [selectedMachineType, setSelectedMachineType] = useState<string>('ALL');
  const [selectedMetric, setSelectedMetric] = useState<string>('EFFICIENCY');
  const [selectedPeriod, setSelectedPeriod] = useState<string>('TODAY');
  const [selectedReference, setSelectedReference] = useState<string>('FACTORY_AVG');

  const [data, setData] = useState<MachineComparisonResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchComparison = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await machineComparisonService.getComparisonData(
        selectedIds,
        selectedMetric,
        selectedPeriod,
        selectedMachineType,
        selectedReference
      );
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load machine comparison data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchComparison();
  }, [selectedIds, selectedMetric, selectedPeriod, selectedMachineType, selectedReference]);

  const metricNameMap: Record<string, string> = {
    EFFICIENCY: 'Efficiency',
    PRODUCTION: 'Production',
    PRODUCTION_LOSS: 'Production Loss',
    DOWNTIME: 'Downtime',
    UTILIZATION: 'Utilization',
    ENERGY_PER_KG: 'Energy / kg',
    QUALITY: 'Quality Rating',
  };

  const metricName = metricNameMap[selectedMetric] || 'Efficiency';

  return (
    <div className="space-y-6 pb-12">
      {/* 1. Header */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs">
        <div className="flex items-center gap-2">
          <BarChart2 className="w-6 h-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight uppercase">
            Machine Comparison
          </h1>
        </div>
        <p className="text-sm font-medium text-slate-500 mt-1">
          Compare selected machines across performance, downtime, quality and energy.
        </p>
      </div>

      {/* 2. Controls Component */}
      <ComparisonControls
        allMasterMachines={data?.all_master_machines || []}
        selectedMachineIds={selectedIds}
        onSelectionChange={setSelectedIds}
        selectedMachineType={selectedMachineType}
        onMachineTypeChange={setSelectedMachineType}
        selectedPeriod={selectedPeriod}
        onPeriodChange={setSelectedPeriod}
        selectedMetric={selectedMetric}
        onMetricChange={setSelectedMetric}
        selectedReference={selectedReference}
        onReferenceChange={setSelectedReference}
      />

      {/* Loading State */}
      {loading && !data && (
        <div className="flex flex-col items-center justify-center min-h-[300px] bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3">
          <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          <p className="text-sm font-semibold text-slate-600">
            Calculating machine comparison telemetry...
          </p>
        </div>
      )}

      {/* 3. Empty State (0 machines selected) */}
      {selectedIds.length === 0 && (
        <div className="bg-white border-2 border-dashed border-slate-300 rounded-2xl p-12 text-center space-y-3">
          <div className="w-12 h-12 rounded-full bg-blue-50 text-blue-600 flex items-center justify-center mx-auto">
            <BarChart2 className="w-6 h-6" />
          </div>
          <h3 className="text-base font-bold text-slate-900">
            Select machines to compare
          </h3>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            Use the dropdown selector above to pick one or more machines for visual comparison across efficiency, downtime, and production.
          </p>
        </div>
      )}

      {/* 4. Single Machine Prompt Notice */}
      {selectedIds.length === 1 && (
        <div className="bg-blue-50/70 border border-blue-200 rounded-xl p-3.5 flex items-center justify-between text-xs text-blue-900 font-medium">
          <div className="flex items-center gap-2">
            <PlusCircle className="w-4 h-4 text-blue-600 shrink-0" />
            <span>Select at least one more machine for a direct machine-to-machine comparison.</span>
          </div>
        </div>
      )}

      {/* 5. Primary Visualization */}
      {selectedIds.length > 0 && data && (
        <>
          <PrimaryComparisonChart
            metrics={data.primary_metrics}
            metricName={metricName}
            referenceFormatted={data.reference_formatted}
            referenceValue={data.reference_value}
          />

          {/* 6. Head-to-Head View (when exactly 2 machines selected) */}
          {selectedIds.length === 2 && data.head_to_head && (
            <HeadToHeadComparison
              machine1Id={selectedIds[0]}
              machine2Id={selectedIds[1]}
              metrics={data.head_to_head}
            />
          )}

          {/* 7. Multi-Metric Matrix */}
          <MultiMetricComparison
            selectedMachineIds={selectedIds}
            matrix={data.multi_metric_matrix}
          />

          {/* 8. Factual Insight */}
          <ComparisonInsight insight={data.insight} />
        </>
      )}
    </div>
  );
};
export default MachineComparisonPage;
