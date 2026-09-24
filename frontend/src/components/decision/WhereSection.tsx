import React from 'react';
import { WhereLocationData } from '../../types/decisionCenter';

interface WhereSectionProps {
  data: WhereLocationData;
  onNavigateTab: (tabId: string) => void;
}

export const WhereSection: React.FC<WhereSectionProps> = ({ data, onNavigateTab }) => {
  return (
    <section className="space-y-3">
      <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
        3. WHERE?
      </h2>

      <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
        {/* Primary Machine Card */}
        <div className="bg-red-50/80 border border-red-200 rounded-xl p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xl font-extrabold text-slate-900 tracking-tight">
                {data.primary_machine_id}
              </span>
              <span className="text-xs font-bold bg-white text-slate-700 border border-slate-300 px-2.5 py-0.5 rounded-md">
                {data.primary_machine_type}
              </span>
              <span className="text-xs font-bold text-red-700 bg-red-100 border border-red-300 px-2 py-0.5 rounded-md ml-auto sm:ml-0">
                {data.status}
              </span>
            </div>
            <p className="text-xs font-medium text-slate-600">
              Section: {data.primary_section}
            </p>
          </div>

          <div className="flex items-center gap-6 text-xs sm:text-sm">
            <div>
              <span className="text-slate-500 block text-[11px]">Production Loss</span>
              <span className="font-bold text-red-600 font-mono text-base">
                {data.production_loss_kg} kg
              </span>
            </div>
            <div className="h-8 w-px bg-slate-200"></div>
            <div>
              <span className="text-slate-500 block text-[11px]">Efficiency</span>
              <span className="font-bold text-slate-900 font-mono text-base">
                {data.efficiency_pct}%
              </span>
            </div>
            <div className="h-8 w-px bg-slate-200"></div>
            <div>
              <span className="text-slate-500 block text-[11px]">Downtime</span>
              <span className="font-bold text-slate-900 font-mono text-base">
                {data.downtime_minutes} min
              </span>
            </div>
          </div>
        </div>

        {/* Secondary Contributors */}
        {data.secondary_machines && data.secondary_machines.length > 0 && (
          <div className="pt-2">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">
              Secondary Contributors
            </span>
            <div className="flex flex-wrap gap-3">
              {data.secondary_machines.map((sec, idx) => (
                <div
                  key={idx}
                  onClick={() => onNavigateTab('machines')}
                  className="flex items-center gap-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-2 rounded-xl text-xs font-bold text-slate-800 transition-colors cursor-pointer"
                >
                  <span className="text-amber-500">🟠</span>
                  <span>
                    {sec.machine_id} ({sec.machine_type})
                  </span>
                  <span className="font-mono text-red-600">
                    {sec.loss_kg} kg
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </section>
  );
};
