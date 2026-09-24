import React, { useState, useEffect } from 'react';
import { DecisionCenterData } from '../types/decisionCenter';
import { TimePeriod } from '../types/overview';
import { decisionCenterService } from '../services/decisionCenterService';

import { DecisionHeaderSection } from '../components/decision/DecisionHeaderSection';
import { TopPrioritySection } from '../components/decision/TopPrioritySection';
import { WhySection } from '../components/decision/WhySection';
import { WhereSection } from '../components/decision/WhereSection';
import { RecommendedActionsSection } from '../components/decision/RecommendedActionsSection';
import { IfContinuesSection } from '../components/decision/IfContinuesSection';
import { OtherIssuesSection } from '../components/decision/OtherIssuesSection';
import { ActionTrackerSection } from '../components/decision/ActionTrackerSection';
import { AIInsightSection } from '../components/decision/AIInsightSection';
import { Loader2, RefreshCw } from 'lucide-react';

interface DecisionCenterPageProps {
  onNavigateTab?: (tabId: string) => void;
}

export const DecisionCenterPage: React.FC<DecisionCenterPageProps> = ({
  onNavigateTab = () => {},
}) => {
  const [period, setPeriod] = useState<TimePeriod>('TODAY');
  const [data, setData] = useState<DecisionCenterData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTelemetry = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await decisionCenterService.getDecisionCenter(period);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load Decision Center data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, [period]);

  if (loading && !data) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-4">
        <Loader2 className="w-8 h-8 text-slate-700 animate-spin" />
        <p className="text-sm font-semibold text-slate-600">
          Synthesizing Decision Center Telemetry...
        </p>
      </div>
    );
  }

  if (error && !data) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-2xl p-8 text-center space-y-4">
        <h3 className="text-base font-bold text-red-800">
          Unable to Load Decision Center
        </h3>
        <p className="text-xs text-red-600 max-w-md mx-auto">{error}</p>
        <button
          onClick={fetchTelemetry}
          className="inline-flex items-center gap-2 bg-red-600 text-white font-bold text-xs px-4 py-2 rounded-xl hover:bg-red-700 transition-colors cursor-pointer"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Retry Loading</span>
        </button>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="space-y-6 pb-12">
      {/* 1. PAGE HEADER */}
      <DecisionHeaderSection
        selectedPeriod={period}
        onPeriodChange={setPeriod}
      />

      {/* 2. TOP PRIORITY (Visually Dominant) */}
      <TopPrioritySection
        data={data.top_priority}
        onNavigateTab={onNavigateTab}
      />

      {/* 3. WHY IS THIS HAPPENING? */}
      <WhySection contributors={data.why_contributors} />

      {/* 4. WHERE IS THE PROBLEM? */}
      <WhereSection
        data={data.where_location}
        onNavigateTab={onNavigateTab}
      />

      {/* 5. WHAT SHOULD WE DO? */}
      <RecommendedActionsSection
        actions={data.recommended_actions}
        onNavigateTab={onNavigateTab}
      />

      {/* 6. IF NOTHING IS DONE */}
      <IfContinuesSection data={data.if_continues} />

      {/* 7. OTHER IMPORTANT ISSUES */}
      <OtherIssuesSection
        issues={data.other_issues}
        onNavigateTab={(tab) => onNavigateTab(tab || 'overview')}
      />

      {/* 8. DECISION / ACTION TRACKER */}
      <ActionTrackerSection initialTracker={data.action_tracker} />

      {/* 9. AI INSIGHT */}
      <AIInsightSection data={data.ai_insight} />
    </div>
  );
};
export default DecisionCenterPage;
