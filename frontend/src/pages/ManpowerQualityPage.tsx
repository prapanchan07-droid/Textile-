import React, { useEffect, useState } from 'react';
import { ManpowerStatusSection } from '../components/manpower/ManpowerStatusSection';
import { ManpowerGapDepartmentSection } from '../components/manpower/ManpowerGapDepartmentSection';
import { ManpowerTrendSection } from '../components/manpower/ManpowerTrendSection';
import { QualityStatusSection } from '../components/manpower/QualityStatusSection';
import { QualityParametersSection } from '../components/manpower/QualityParametersSection';
import { QualityTrendSection } from '../components/manpower/QualityTrendSection';
import { QualityIssueMachineSection } from '../components/manpower/QualityIssueMachineSection';
import { NeedsAttentionSection } from '../components/manpower/NeedsAttentionSection';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Card } from '../components/ui/Card';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { manpowerQualityService } from '../services/manpowerQualityService';
import { ManpowerQualityModuleData } from '../types/manpowerQuality';

export const ManpowerQualityPage: React.FC = () => {
  const [data, setData] = useState<ManpowerQualityModuleData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [period, setPeriod] = useState<string>('THIS_MONTH');

  const fetchManpowerQualityData = async (isInitial = false) => {
    if (isInitial || !data) {
      setLoading(true);
    }
    setError(null);
    try {
      const res = await manpowerQualityService.getManpowerQualityData(period);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load Manpower & Quality module data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchManpowerQualityData(data === null);
  }, [period]);

  if (loading) {
    return <LoadingSpinner label="Loading manpower availability, attendance logs, and yarn quality lab telemetry..." />;
  }

  if (error) {
    return (
      <Card variant="outline" className="border-rose-300 bg-rose-50/50 p-6">
        <div className="flex items-center gap-3 text-rose-700">
          <AlertCircle className="w-6 h-6 shrink-0" />
          <div className="flex-1">
            <h3 className="font-bold text-slate-900">Manpower & Quality Connection Error</h3>
            <p className="text-xs text-rose-600">{error}</p>
          </div>
          <button
            onClick={() => fetchManpowerQualityData(true)}
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
      {/* 1. MANPOWER STATUS */}
      <ManpowerStatusSection summary={data.manpower_summary} />

      {/* 2. MANPOWER GAP BY DEPARTMENT & 3. MANPOWER TREND */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ManpowerGapDepartmentSection departments={data.department_gaps} />
        <ManpowerTrendSection trend={data.manpower_trend} />
      </div>

      {/* 4. QUALITY STATUS */}
      <QualityStatusSection status={data.quality_status} />

      {/* 5. QUALITY PARAMETERS & 6. QUALITY TREND */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QualityParametersSection parameters={data.quality_parameters} />
        <QualityTrendSection trendsByParam={data.quality_trends_by_param} />
      </div>

      {/* 7. QUALITY ISSUE BY MACHINE / PROCESS */}
      <QualityIssueMachineSection issues={data.quality_issues_by_machine} />

      {/* 8. ACTION / ATTENTION AREA */}
      <NeedsAttentionSection items={data.needs_attention} />
    </div>
  );
};
