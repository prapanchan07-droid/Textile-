import React, { useEffect, useState } from 'react';
import { RevenueCurrentSection } from '../components/revenue/RevenueCurrentSection';
import { RevenueTrendSection } from '../components/revenue/RevenueTrendSection';
import { DispatchOrdersSection } from '../components/revenue/DispatchOrdersSection';
import { MoneyPositionSection } from '../components/revenue/MoneyPositionSection';
import { StockPositionSection } from '../components/revenue/StockPositionSection';
import { BusinessPerformanceSection } from '../components/revenue/BusinessPerformanceSection';
import { BusinessAttentionSection } from '../components/revenue/BusinessAttentionSection';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Card } from '../components/ui/Card';
import { AlertCircle, RefreshCw } from 'lucide-react';
import { revenueLossService } from '../services/revenueLossService';
import { RevenueLossModuleData } from '../types/revenueLoss';

export const RevenueLossPage: React.FC = () => {
  const [data, setData] = useState<RevenueLossModuleData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [period, setPeriod] = useState<string>('THIS_MONTH');

  const fetchRevenueLossData = async (isInitial = false) => {
    if (isInitial || !data) {
      setLoading(true);
    }
    setError(null);
    try {
      const res = await revenueLossService.getRevenueLossData(period);
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to load Revenue & Loss module data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRevenueLossData(data === null);
  }, [period]);

  if (loading) {
    return <LoadingSpinner label="Loading sales revenue telemetry, dispatch metrics, receivables & stock valuation..." />;
  }

  if (error) {
    return (
      <Card variant="outline" className="border-rose-300 bg-rose-50/50 p-6">
        <div className="flex items-center gap-3 text-rose-700">
          <AlertCircle className="w-6 h-6 shrink-0" />
          <div className="flex-1">
            <h3 className="font-bold text-slate-900">Revenue & Loss Connection Error</h3>
            <p className="text-xs text-rose-600">{error}</p>
          </div>
          <button
            onClick={() => fetchRevenueLossData(true)}
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
      {/* 1. REVENUE CURRENT PERIOD */}
      <RevenueCurrentSection
        summary={data.revenue_summary}
        selectedPeriod={period}
        onPeriodChange={setPeriod}
      />

      {/* 2. REVENUE TREND */}
      <RevenueTrendSection trend={data.revenue_trend} />

      {/* 3. DISPATCH & ORDERS & 4. MONEY POSITION */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <DispatchOrdersSection data={data.dispatch_orders} />
        <MoneyPositionSection data={data.money_position} />
      </div>

      {/* 5. STOCK POSITION */}
      <StockPositionSection stockItems={data.stock_position} />

      {/* 6. BUSINESS PERFORMANCE */}
      <BusinessPerformanceSection summary={data.business_performance} />

      {/* 7. BUSINESS ATTENTION */}
      <BusinessAttentionSection items={data.needs_attention} />
    </div>
  );
};
