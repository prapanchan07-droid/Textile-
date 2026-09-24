import React, { useState, useEffect } from 'react';
import { AppShell } from './components/layout/AppShell';
import { FactoryOverviewPage } from './pages/FactoryOverviewPage';
import { ProductionPage } from './pages/ProductionPage';
import { MachinesDowntimePage } from './pages/MachinesDowntimePage';
import { MachineComparisonPage } from './pages/MachineComparisonPage';
import { ManpowerQualityPage } from './pages/ManpowerQualityPage';
import { RevenueLossPage } from './pages/RevenueLossPage';
import { DecisionCenterPage } from './pages/DecisionCenterPage';
import { Module01FoundationPage } from './pages/Module01FoundationPage';
import { healthService } from './services/healthService';
import { overviewService } from './services/overviewService';
import { FactoryOverviewData, TimePeriod, ComparisonPeriod } from './types/overview';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<string>('overview');
  const [apiStatus, setApiStatus] = useState<'healthy' | 'unhealthy' | 'degraded'>('healthy');
  
  const [period, setPeriod] = useState<TimePeriod>('TODAY');
  const [comparison, setComparison] = useState<ComparisonPeriod>('PREVIOUS_DAY');
  const [unit, setUnit] = useState<string>('All Units');
  const [userRole, setUserRole] = useState<string>('SUPER_ADMIN');
  const [sectionAccess, setSectionAccess] = useState<string>('ALL');

  // Bumped after every successful upload so the visible page reloads its data
  const [dataVersion, setDataVersion] = useState<number>(0);

  const [overviewData, setOverviewData] = useState<FactoryOverviewData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const checkHealth = async () => {
    try {
      const health = await healthService.getHealth();
      setApiStatus(health.status);
    } catch {
      setApiStatus('unhealthy');
    }
  };

  const fetchOverviewData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await overviewService.getOverview(
        period,
        comparison,
        unit,
        userRole,
        sectionAccess
      );
      setOverviewData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load Factory Overview telemetry.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkHealth();
    const onReportUploaded = () => setDataVersion((v) => v + 1);
    window.addEventListener('reportUploaded', onReportUploaded);
    return () => window.removeEventListener('reportUploaded', onReportUploaded);
  }, []);

  useEffect(() => {
    if (activeTab === 'overview') {
      fetchOverviewData();
    }
  }, [activeTab, period, comparison, unit, userRole, sectionAccess, dataVersion]);

  return (
    <AppShell
      activeTab={activeTab}
      onTabChange={setActiveTab}
      selectedPeriod={period}
      onPeriodChange={setPeriod}
      selectedComparison={comparison}
      onComparisonChange={setComparison}
      selectedUnit={unit}
      onUnitChange={setUnit}
      apiStatus={apiStatus}
    >
      <React.Fragment key={dataVersion}>
      {activeTab === 'overview' ? (
        <FactoryOverviewPage
          data={overviewData}
          loading={loading}
          error={error}
          onRetry={fetchOverviewData}
        />
      ) : activeTab === 'production' ? (
        <ProductionPage />
      ) : activeTab === 'machines' ? (
        <MachinesDowntimePage />
      ) : activeTab === 'machine_comparison' ? (
        <MachineComparisonPage />
      ) : activeTab === 'manpower' ? (
        <ManpowerQualityPage />
      ) : activeTab === 'revenue' ? (
        <RevenueLossPage />
      ) : activeTab === 'decision' ? (
        <DecisionCenterPage onNavigateTab={(tabId) => setActiveTab(tabId)} />
      ) : activeTab === 'foundation' ? (
        <Module01FoundationPage />
      ) : (
        <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center space-y-3">
          <h2 className="text-xl font-bold text-slate-900 capitalize">
            Module {activeTab}
          </h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            This module is scheduled for development according to the phased protocol. Select <strong>Factory Overview</strong> or <strong>Production</strong> in the sidebar to navigate.
          </p>
        </div>
      )}
      </React.Fragment>
    </AppShell>
  );
};

export default App;
