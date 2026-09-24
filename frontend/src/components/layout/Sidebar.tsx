import React, { useState } from 'react';
import { 
  Building, 
  ChevronDown, 
  Search, 
  LayoutDashboard, 
  TrendingUp, 
  Cpu, 
  Users, 
  DollarSign, 
  Target, 
  ShieldCheck, 
  Settings, 
  HelpCircle,
  MoreVertical,
  Layers,
  BarChart2
} from 'lucide-react';

interface SidebarProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  selectedUnit: string;
  onUnitChange: (unit: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  onTabChange,
  selectedUnit,
  onUnitChange,
}) => {
  const [searchQuery, setSearchQuery] = useState('');

  const navigationGroups = [
    {
      title: 'PLATFORM',
      items: [
        { id: 'overview', label: 'Factory Overview', icon: LayoutDashboard, badge: null },
        { id: 'production', label: 'Production', icon: TrendingUp, badge: 'Phase 2' },
        { id: 'machines', label: 'Machines &\nDowntime', icon: Cpu, badge: 'Phase 2' },
        { id: 'machine_comparison', label: 'Machine Comparison', icon: BarChart2, badge: 'New' },
        { id: 'manpower', label: 'Manpower & Quality', icon: Users, badge: 'Phase 4' },
        { id: 'revenue', label: 'Revenue & Loss', icon: DollarSign, badge: 'Phase 5' },
        { id: 'decision', label: 'Decision Center', icon: Target, badge: 'Phase 7' },
      ],
    },
    {
      title: 'SYSTEM',
      items: [
        { id: 'foundation', label: 'Foundation Specs', icon: Layers, badge: null },
        { id: 'access', label: 'Access Control', icon: ShieldCheck, badge: null },
        { id: 'settings', label: 'Settings', icon: Settings, badge: null },
        { id: 'support', label: 'Support & Docs', icon: HelpCircle, badge: null },
      ],
    },
  ];

  return (
    <aside className="w-64 h-screen bg-white border-r border-slate-200 flex flex-col justify-between shrink-0 font-sans select-none z-30">
      {/* Top Section */}
      <div className="p-4 space-y-4 overflow-y-auto">
        {/* Workspace Brand Switcher */}
        <div className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200 hover:bg-slate-100 transition-colors cursor-pointer">
          <div className="flex items-center gap-2.5">
            <div className="bg-slate-900 text-white p-2 rounded-lg font-bold">
              <Building className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-extrabold text-sm text-slate-900 leading-tight">Ashok Textiles</h2>
              <p className="text-[11px] text-slate-500 font-medium">{selectedUnit}</p>
            </div>
          </div>
          <ChevronDown className="w-4 h-4 text-slate-400" />
        </div>

        {/* Quick Action Search Bar */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Quick action..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-50 border border-slate-200 rounded-lg pl-8 pr-8 py-1.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-slate-400 focus:bg-white transition-colors"
          />
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] bg-white border border-slate-200 px-1.5 py-0.5 rounded text-slate-400 font-mono">
            ⌘K
          </kbd>
        </div>

        {/* Navigation Sections */}
        <div className="space-y-5 pt-1">
          {navigationGroups.map((group) => (
            <div key={group.title} className="space-y-1">
              <div className="px-3 text-[10px] font-extrabold text-slate-400 tracking-wider uppercase">
                {group.title}
              </div>
              <div className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = activeTab === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => onTabChange(item.id)}
                      className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                        isActive
                          ? 'bg-indigo-50 border-l-4 border-indigo-600 text-indigo-950 font-bold shadow-sm'
                          : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100 border-l-4 border-transparent'
                      }`}
                    >
                      <div className="flex items-center gap-2.5 min-w-0 pr-1">
                        <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-indigo-600' : 'text-slate-500'}`} />
                        <span className="text-left leading-tight whitespace-pre-line">{item.label}</span>
                      </div>
                      {item.badge && (
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium shrink-0 ${
                          isActive
                            ? 'bg-indigo-100 text-indigo-800'
                            : 'bg-slate-100 text-slate-500 border border-slate-200'
                        }`}>
                          {item.badge}
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bottom User Profile Section */}
      <div className="p-3 border-t border-slate-200 m-3 rounded-xl bg-slate-50 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-full bg-slate-900 text-white font-bold flex items-center justify-center text-xs shadow-sm">
            AT
          </div>
          <div>
            <div className="text-xs font-bold text-slate-900 leading-none">Ashok Manager</div>
            <div className="text-[11px] text-slate-500 mt-0.5">Factory Owner</div>
          </div>
        </div>
        <button className="p-1 hover:bg-slate-200 rounded-lg transition-colors text-slate-400 hover:text-slate-600">
          <MoreVertical className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};
