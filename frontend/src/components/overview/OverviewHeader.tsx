import React from 'react';
import { Calendar, Filter, Clock, Shield, Building } from 'lucide-react';
import { TimePeriod, ComparisonPeriod } from '../../types/overview';

interface OverviewHeaderProps {
  selectedPeriod: TimePeriod;
  onPeriodChange: (period: TimePeriod) => void;
  selectedComparison: ComparisonPeriod;
  onComparisonChange: (comparison: ComparisonPeriod) => void;
  selectedUnit: string;
  onUnitChange: (unit: string) => void;
  userRole: string;
  sectionAccess: string;
  onSectionAccessChange: (section: string) => void;
}

export const OverviewHeader: React.FC<OverviewHeaderProps> = ({
  selectedPeriod,
  onPeriodChange,
  selectedComparison,
  onComparisonChange,
  selectedUnit,
  onUnitChange,
  userRole,
  sectionAccess,
  onSectionAccessChange,
}) => {
  const currentDateStr = new Date().toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <div className="bg-factory-surface border-b border-factory-border px-6 py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-3 text-xs">
      <div className="flex items-center gap-4 flex-wrap">
        {/* Company & Unit Selector */}
        <div className="flex items-center gap-2">
          <Building className="w-4 h-4 text-slate-400" />
          <select
            value={selectedUnit}
            onChange={(e) => onUnitChange(e.target.value)}
            className="bg-factory-card border border-factory-border rounded-lg px-2.5 py-1 text-slate-200 font-medium focus:outline-none focus:border-factory-accent"
          >
            <option value="All Units">Ashok Textiles — All Units</option>
            <option value="Unit I">Unit I — Spinning & Weaving</option>
            <option value="Unit II">Unit II — Vortex & Sizing</option>
          </select>
        </div>

        {/* Period Selector */}
        <div className="flex items-center gap-1.5 bg-factory-card border border-factory-border p-1 rounded-lg">
          <Calendar className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
          <span className="text-slate-400 font-medium mr-1">Period:</span>
          {(
            [
              { id: 'TODAY', label: 'Today' },
              { id: 'SHIFT', label: 'Shift' },
              { id: 'YESTERDAY', label: 'Yesterday' },
              { id: 'THIS_WEEK', label: 'This Week' },
              { id: 'THIS_MONTH', label: 'This Month' },
            ] as const
          ).map((p) => (
            <button
              key={p.id}
              onClick={() => onPeriodChange(p.id)}
              className={`px-2.5 py-1 rounded font-medium transition-colors ${
                selectedPeriod === p.id
                  ? 'bg-factory-accent text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-factory-surface'
              }`}
            >
              {p.label}
            </button>
          ))}
        </div>

        {/* Comparison Selector */}
        <div className="flex items-center gap-1.5 bg-factory-card border border-factory-border p-1 rounded-lg">
          <Filter className="w-3.5 h-3.5 text-slate-400 ml-1.5" />
          <span className="text-slate-400 font-medium mr-1">Compare vs:</span>
          <select
            value={selectedComparison}
            onChange={(e) => onComparisonChange(e.target.value as ComparisonPeriod)}
            className="bg-transparent text-slate-200 font-medium focus:outline-none cursor-pointer pr-1"
          >
            <option value="PREVIOUS_DAY" className="bg-factory-card text-slate-200">Previous Day</option>
            <option value="PREVIOUS_SHIFT" className="bg-factory-card text-slate-200">Previous Shift</option>
            <option value="PREVIOUS_WEEK" className="bg-factory-card text-slate-200">Previous Week</option>
            <option value="PREVIOUS_MONTH" className="bg-factory-card text-slate-200">Previous Month</option>
            <option value="THREE_MONTH_AVG" className="bg-factory-card text-slate-200">3-Month Average</option>
          </select>
        </div>
      </div>

      {/* Right Side: RBAC & Date */}
      <div className="flex items-center gap-3 self-end md:self-auto">
        <div className="flex items-center gap-1.5 bg-factory-card border border-factory-border px-2.5 py-1 rounded-lg text-slate-300">
          <Shield className="w-3.5 h-3.5 text-indigo-400" />
          <span className="text-slate-400">Role:</span>
          <span className="font-semibold text-white">{userRole}</span>
          <span className="text-slate-500">|</span>
          <select
            value={sectionAccess}
            onChange={(e) => onSectionAccessChange(e.target.value)}
            className="bg-transparent text-indigo-300 font-medium focus:outline-none cursor-pointer"
          >
            <option value="ALL" className="bg-factory-card text-slate-200">All Sections</option>
            <option value="Section A" className="bg-factory-card text-slate-200">Section A</option>
            <option value="Section B" className="bg-factory-card text-slate-200">Section B</option>
          </select>
        </div>

        <div className="flex items-center gap-1.5 text-slate-400 bg-factory-card border border-factory-border px-2.5 py-1 rounded-lg">
          <Clock className="w-3.5 h-3.5 text-slate-400" />
          <span>{currentDateStr}</span>
        </div>
      </div>
    </div>
  );
};
