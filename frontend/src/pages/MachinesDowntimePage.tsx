import React, { useEffect, useState } from 'react';
import { MachinePerformanceSection } from '../components/machines/MachinePerformanceSection';
import { ProductionLossByMachineSection } from '../components/machines/ProductionLossByMachineSection';
import { DowntimeAnalysisSection } from '../components/machines/DowntimeAnalysisSection';
import { MachineTrendSection } from '../components/machines/MachineTrendSection';
import { MachineDetailSection } from '../components/machines/MachineDetailSection';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Card } from '../components/ui/Card';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { machinesService } from '../services/machinesService';
import { MachinesModuleData } from '../types/machines';

export const MachinesDowntimePage: React.FC = () => {
  const [data, setData] = useState<MachinesModuleData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [period, setPeriod] = useState<string>('THIS_MONTH');
  const [machineType, setMachineType] = useState<string>('ALL');
  const [machineId, setMachineId] = useState<string>('ALL');

  const fetchMachinesData = async (isInitial = false) => {
    if (isInitial || !data) {
      setLoading(true);
    }
    setError(null);
    try {
      const res = await machinesService.getMachinesData(period, machineType, machineId);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load Machines & Downtime data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMachinesData(data === null);
  }, [period, machineType, machineId]);

  if (loading) {
    return <LoadingSpinner label="Loading machine telemetry, downtime logs, and root cause analytics..." />;
  }

  if (error) {
    return (
      <Card variant="outline" className="border-rose-300 bg-rose-50/50 p-6">
        <div className="flex items-center gap-3 text-rose-700">
          <AlertCircle className="w-6 h-6 shrink-0" />
          <div className="flex-1">
            <h3 className="font-bold text-slate-900">Machines & Downtime Connection Error</h3>
            <p className="text-xs text-rose-600">{error}</p>
          </div>
          <button
            onClick={() => fetchMachinesData(true)}
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
      {/* SECTION 1 — MACHINE PERFORMANCE */}
      <MachinePerformanceSection
        spotlight={data.spotlight_machine}
        machines={data.all_machines}
        machineTypes={data.machine_types}
        selectedPeriod={period}
        onPeriodChange={setPeriod}
        selectedType={machineType}
        onTypeChange={setMachineType}
        selectedMachineId={machineId}
        onMachineIdChange={setMachineId}
      />

      {/* SECTION 2 — PRODUCTION LOSS BY MACHINE & SECTION 3 — DOWNTIME ANALYSIS */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ProductionLossByMachineSection machines={data.all_machines} />
        <DowntimeAnalysisSection kpis={data.downtime_kpis} reasons={data.downtime_reasons} />
      </div>

      {/* SECTION 4 — MACHINE PERFORMANCE TREND */}
      <MachineTrendSection
        trend={data.machine_trend}
        selectedMachineId={machineId}
        onMachineIdChange={setMachineId}
        availableMachineIds={['V-09', 'V-05', 'SMX-03', 'V-12', 'RF-04', 'A-02']}
        trendsById={data.machine_trends_by_id}
      />

      {/* SECTION 5 — MACHINE DETAIL */}
      <MachineDetailSection detail={data.machine_detail} />
    </div>
  );
};
