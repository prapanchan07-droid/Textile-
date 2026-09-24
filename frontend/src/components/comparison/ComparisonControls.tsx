import React, { useState, useRef, useEffect } from 'react';
import { MachineMasterOption } from '../../types/machineComparison';
import { Search, ChevronDown, X, Check, Filter } from 'lucide-react';

interface ComparisonControlsProps {
  allMasterMachines: MachineMasterOption[];
  selectedMachineIds: string[];
  onSelectionChange: (ids: string[]) => void;
  selectedMachineType: string;
  onMachineTypeChange: (type: string) => void;
  selectedPeriod: string;
  onPeriodChange: (period: string) => void;
  selectedMetric: string;
  onMetricChange: (metric: string) => void;
  selectedReference: string;
  onReferenceChange: (ref: string) => void;
}

export const ComparisonControls: React.FC<ComparisonControlsProps> = ({
  allMasterMachines,
  selectedMachineIds,
  onSelectionChange,
  selectedMachineType,
  onMachineTypeChange,
  selectedPeriod,
  onPeriodChange,
  selectedMetric,
  onMetricChange,
  selectedReference,
  onReferenceChange,
}) => {
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter machines based on machine type filter & search query
  const filteredMachines = allMasterMachines.filter((m) => {
    const matchesType =
      selectedMachineType === 'ALL' ||
      m.machine_type.toLowerCase() === selectedMachineType.toLowerCase();
    const matchesSearch =
      m.machine_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.machine_type.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesType && matchesSearch;
  });

  const toggleMachine = (id: string) => {
    if (selectedMachineIds.includes(id)) {
      onSelectionChange(selectedMachineIds.filter((item) => item !== id));
    } else {
      onSelectionChange([...selectedMachineIds, id]);
    }
  };

  const selectAll = () => {
    const visibleIds = filteredMachines.map((m) => m.machine_id);
    const combined = Array.from(new Set([...selectedMachineIds, ...visibleIds]));
    onSelectionChange(combined);
  };

  const clearAll = () => {
    onSelectionChange([]);
  };

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 1. Machine Multi-Select Searchable Dropdown */}
        <div className="space-y-1.5 relative" ref={dropdownRef}>
          <label className="text-xs font-bold text-slate-700 block uppercase tracking-wider">
            Select Machines
          </label>
          <button
            type="button"
            onClick={() => setDropdownOpen(!dropdownOpen)}
            className="w-full inline-flex items-center justify-between bg-slate-50 border border-slate-200 hover:border-slate-300 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-900 transition-colors cursor-pointer"
          >
            <span className="truncate">
              {selectedMachineIds.length === 0
                ? 'Select machines...'
                : `${selectedMachineIds.length} machine${selectedMachineIds.length > 1 ? 's' : ''} selected`}
            </span>
            <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
          </button>

          {/* Searchable Dropdown Modal */}
          {dropdownOpen && (
            <div className="absolute left-0 top-full mt-1.5 w-72 bg-white border border-slate-200 rounded-xl shadow-xl z-50 p-3 space-y-2">
              {/* Search Field */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  placeholder="Search machine..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-900 focus:outline-hidden focus:border-slate-400"
                />
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-between text-[11px] font-bold text-blue-600 px-1 border-b border-slate-100 pb-1.5">
                <button type="button" onClick={selectAll} className="hover:underline cursor-pointer">
                  Select All
                </button>
                <button type="button" onClick={clearAll} className="text-slate-500 hover:underline cursor-pointer">
                  Clear
                </button>
              </div>

              {/* Options List */}
              <div className="max-h-48 overflow-y-auto space-y-1 pr-1">
                {filteredMachines.map((m) => {
                  const isChecked = selectedMachineIds.includes(m.machine_id);
                  return (
                    <label
                      key={m.machine_id}
                      onClick={() => toggleMachine(m.machine_id)}
                      className={`flex items-center justify-between p-2 rounded-lg text-xs cursor-pointer select-none transition-colors ${
                        isChecked ? 'bg-slate-100 text-slate-900 font-bold' : 'hover:bg-slate-50 text-slate-700'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        <div
                          className={`w-4 h-4 rounded-md border flex items-center justify-center transition-colors ${
                            isChecked ? 'bg-slate-900 border-slate-900 text-white' : 'border-slate-300 bg-white'
                          }`}
                        >
                          {isChecked && <Check className="w-3 h-3 stroke-[3]" />}
                        </div>
                        <span>{m.machine_id}</span>
                      </div>
                      <span className="text-[10px] text-slate-400 font-mono">{m.machine_type}</span>
                    </label>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* 2. Machine Type Filter */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 block uppercase tracking-wider">
            Machine Type
          </label>
          <select
            value={selectedMachineType}
            onChange={(e) => onMachineTypeChange(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 hover:border-slate-300 px-3.5 py-2.5 rounded-xl text-xs font-semibold text-slate-900 focus:outline-hidden cursor-pointer"
          >
            <option value="ALL">All Machine Types</option>
            <option value="Vortex">Vortex</option>
            <option value="Ring Frame">Ring Frame</option>
            <option value="Simplex">Simplex</option>
            <option value="Airjet">Airjet</option>
          </select>
        </div>

        {/* 3. Compare Metric Selector */}
        <div className="space-y-1.5">
          <label className="text-xs font-bold text-slate-700 block uppercase tracking-wider">
            Compare By
          </label>
          <select
            value={selectedMetric}
            onChange={(e) => onMetricChange(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 hover:border-slate-300 px-3.5 py-2.5 rounded-xl text-xs font-bold text-blue-600 focus:outline-hidden cursor-pointer"
          >
            <option value="EFFICIENCY">Efficiency (%)</option>
            <option value="PRODUCTION">Production (kg)</option>
            <option value="PRODUCTION_LOSS">Production Loss (kg)</option>
            <option value="DOWNTIME">Downtime (min)</option>
            <option value="UTILIZATION">Utilization (%)</option>
            <option value="ENERGY_PER_KG">Energy / kg (kWh/kg)</option>
            <option value="QUALITY">Quality Rating (%)</option>
          </select>
        </div>

        {/* 4. Period & Reference Baseline */}
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 block uppercase tracking-wider">
              Period
            </label>
            <select
              value={selectedPeriod}
              onChange={(e) => onPeriodChange(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 hover:border-slate-300 px-2.5 py-2.5 rounded-xl text-xs font-semibold text-slate-900 focus:outline-hidden cursor-pointer"
            >
              <option value="TODAY">Today</option>
              <option value="YESTERDAY">Yesterday</option>
              <option value="LAST_7_DAYS">Last 7 Days</option>
              <option value="THIS_MONTH">This Month</option>
            </select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-slate-700 block uppercase tracking-wider">
              Reference
            </label>
            <select
              value={selectedReference}
              onChange={(e) => onReferenceChange(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 hover:border-slate-300 px-2.5 py-2.5 rounded-xl text-xs font-semibold text-slate-900 focus:outline-hidden cursor-pointer"
            >
              <option value="FACTORY_AVG">Factory Avg</option>
              <option value="TARGET">Target</option>
              <option value="NONE">None</option>
            </select>
          </div>
        </div>
      </div>

      {/* Selected Machines Tag Chips */}
      {selectedMachineIds.length > 0 && (
        <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-slate-100">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mr-1">
            Active:
          </span>
          {selectedMachineIds.map((id) => (
            <span
              key={id}
              className="inline-flex items-center gap-1.5 bg-slate-900 text-white px-2.5 py-1 rounded-lg text-xs font-bold shadow-xs"
            >
              <span>{id}</span>
              <button
                type="button"
                onClick={() => toggleMachine(id)}
                className="hover:text-red-300 cursor-pointer"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </span>
          ))}
          {selectedMachineIds.length > 0 && (
            <button
              type="button"
              onClick={clearAll}
              className="text-xs font-semibold text-slate-500 hover:text-red-600 underline ml-2 cursor-pointer"
            >
              Clear All
            </button>
          )}
        </div>
      )}
    </div>
  );
};
