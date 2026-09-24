import React, { useState } from 'react';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { UploadReportModal } from '../modals/UploadReportModal';
import { TimePeriod, ComparisonPeriod } from '../../types/overview';

interface AppShellProps {
  children: React.ReactNode;
  activeTab: string;
  onTabChange: (tabId: string) => void;
  selectedPeriod: TimePeriod;
  onPeriodChange: (period: TimePeriod) => void;
  selectedComparison: ComparisonPeriod;
  onComparisonChange: (comparison: ComparisonPeriod) => void;
  selectedUnit: string;
  onUnitChange: (unit: string) => void;
  apiStatus: 'healthy' | 'unhealthy' | 'degraded';
}

export const AppShell: React.FC<AppShellProps> = ({
  children,
  activeTab,
  onTabChange,
  selectedPeriod,
  onPeriodChange,
  selectedComparison,
  onComparisonChange,
  selectedUnit,
  onUnitChange,
  apiStatus,
}) => {
  const [isUploadModalOpen, setIsUploadModalOpen] = useState<boolean>(false);

  const handleUploadSuccess = () => {
    // Notify application to refresh data
    window.dispatchEvent(new CustomEvent('reportUploaded'));
  };

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#f8fafc] text-slate-900 font-sans">
      {/* Fixed Left Sidebar */}
      <Sidebar
        activeTab={activeTab}
        onTabChange={onTabChange}
        selectedUnit={selectedUnit}
        onUnitChange={onUnitChange}
      />

      {/* Right Column (Header + Scrollable Main Content) */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
        {/* Fixed Non-Overlapping Header */}
        <Header
          selectedPeriod={selectedPeriod}
          onPeriodChange={onPeriodChange}
          selectedComparison={selectedComparison}
          onComparisonChange={onComparisonChange}
          apiStatus={apiStatus}
          onUploadClick={() => {
            console.log("AppShell onUploadClick triggered, setting isUploadModalOpen to true");
            setIsUploadModalOpen(true);
          }}
        />

        {/* Scrollable Main Workspace (Starts strictly below Header) */}
        <div className="flex-1 overflow-y-auto bg-[#f8fafc]">
          <main className="p-6 max-w-7xl mx-auto space-y-6">
            {children}
          </main>

          <footer className="border-t border-slate-200 bg-white py-4 px-6 text-center text-xs text-slate-500 mt-12">
            AI Factory Manager • Ashok Textiles © 2026 • Executive Decision Support System
          </footer>
        </div>
      </div>

      {/* Upload Report Modal Drawer */}
      <UploadReportModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
        onUploadSuccess={handleUploadSuccess}
      />
    </div>
  );
};
