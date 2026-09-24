import React from 'react';
import { 
  ChevronRight, 
  Download, 
  Plus, 
  Bell, 
  Calendar,
  Building
} from 'lucide-react';
import { TimePeriod, ComparisonPeriod } from '../../types/overview';

interface HeaderProps {
  selectedPeriod: TimePeriod;
  onPeriodChange: (period: TimePeriod) => void;
  selectedComparison: ComparisonPeriod;
  onComparisonChange: (comparison: ComparisonPeriod) => void;
  apiStatus: 'healthy' | 'unhealthy' | 'degraded';
  onUploadClick?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  selectedPeriod,
  onPeriodChange,
  selectedComparison,
  onComparisonChange,
  apiStatus,
  onUploadClick,
}) => {
  return (
    <header className="h-16 shrink-0 bg-white border-b border-slate-200 px-6 flex items-center justify-between gap-4 z-20 shadow-sm">
      {/* Left Breadcrumbs & Operational Status */}
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <div className="bg-slate-900 text-white p-1 rounded-md">
            <Building className="w-3.5 h-3.5" />
          </div>
          <span>Ashok Textiles</span>
          <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-slate-900 font-bold text-sm">Factory Overview</span>
        </div>

        <div className="flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 text-emerald-700 px-2.5 py-0.5 rounded-full text-[11px] font-bold uppercase tracking-wider">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>OPERATIONAL</span>
        </div>
      </div>

      {/* Right Controls & Quick Actions */}
      <div className="flex items-center gap-3 text-xs flex-wrap">
        {/* Date Selector Pill */}
        <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm">
          <Calendar className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={selectedPeriod}
            onChange={(e) => onPeriodChange(e.target.value as TimePeriod)}
            className="bg-transparent text-slate-800 font-semibold focus:outline-none cursor-pointer"
          >
            <option value="TODAY">Today (Realtime)</option>
            <option value="SHIFT">Current Shift</option>
            <option value="YESTERDAY">Yesterday</option>
            <option value="THIS_WEEK">This Week</option>
            <option value="THIS_MONTH">This Month (30 Days)</option>
          </select>
        </div>

        {/* Export Button */}
        <button className="flex items-center gap-1.5 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 px-3 py-1.5 rounded-lg font-semibold shadow-sm transition-colors">
          <Download className="w-3.5 h-3.5 text-slate-500" />
          <span>Export</span>
        </button>

        {/* Primary Action Button */}
        <button 
          type="button"
          onClick={() => {
            console.log("HEADER UPLOAD REPORT CLICKED");
            if (onUploadClick) {
              onUploadClick();
            }
          }}
          className="flex items-center gap-1.5 bg-slate-900 hover:bg-slate-800 text-white px-3.5 py-1.5 rounded-lg font-semibold shadow-sm transition-colors cursor-pointer relative z-30 pointer-events-auto"
        >
          <Plus className="w-3.5 h-3.5 pointer-events-none" />
          <span className="pointer-events-none">Upload Report</span>
        </button>

        <div className="h-4 w-px bg-slate-200 mx-0.5" />

        {/* Notifications & Avatar */}
        <button className="relative p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded-lg transition-colors">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 bg-rose-500 rounded-full border border-white" />
        </button>

        <div className="w-7 h-7 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center text-[11px]">
          AM
        </div>
      </div>
    </header>
  );
};
