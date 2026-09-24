import React, { useState } from 'react';
import { ActionTrackerItem } from '../../types/decisionCenter';

interface ActionTrackerSectionProps {
  initialTracker: ActionTrackerItem[];
}

export const ActionTrackerSection: React.FC<ActionTrackerSectionProps> = ({
  initialTracker,
}) => {
  const [trackerList, setTrackerList] = useState<ActionTrackerItem[]>(initialTracker);

  const toggleStatus = (id: string) => {
    setTrackerList((prev) =>
      prev.map((item) => {
        if (item.id === id) {
          let nextStatus = 'IN_PROGRESS';
          let nextBadge = '🟠 IN PROGRESS';
          if (item.status === 'OPEN') {
            nextStatus = 'IN_PROGRESS';
            nextBadge = '🟠 IN PROGRESS';
          } else if (item.status === 'IN_PROGRESS') {
            nextStatus = 'COMPLETED';
            nextBadge = '🟢 COMPLETED';
          } else {
            nextStatus = 'OPEN';
            nextBadge = '🔴 OPEN';
          }
          return {
            ...item,
            status: nextStatus,
            status_badge: nextBadge,
          };
        }
        return item;
      })
    );
  };

  return (
    <section className="space-y-3">
      <div className="flex items-center justify-between">
        <h2 className="text-xs font-bold text-slate-500 uppercase tracking-wider">
          7. ACTION TRACKER
        </h2>
        <span className="text-[11px] text-slate-400 font-medium">
          Click status badge to cycle state
        </span>
      </div>

      <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-500 uppercase font-bold text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="px-5 py-3.5">Issue</th>
                <th className="px-5 py-3.5">Action</th>
                <th className="px-5 py-3.5">Owner</th>
                <th className="px-5 py-3.5 text-center">Status</th>
                <th className="px-5 py-3.5 text-right">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
              {trackerList.map((row) => (
                <tr key={row.id} className="hover:bg-slate-50/80 transition-colors">
                  <td className="px-5 py-4 font-bold text-slate-900">{row.issue}</td>
                  <td className="px-5 py-4 text-slate-600">{row.action}</td>
                  <td className="px-5 py-4 font-semibold text-slate-700">{row.owner}</td>
                  <td className="px-5 py-4 text-center">
                    <button
                      onClick={() => toggleStatus(row.id)}
                      className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border transition-all cursor-pointer ${
                        row.status === 'OPEN'
                          ? 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100'
                          : row.status === 'IN_PROGRESS'
                          ? 'bg-amber-50 text-amber-700 border-amber-200 hover:bg-amber-100'
                          : 'bg-emerald-50 text-emerald-700 border-emerald-200 hover:bg-emerald-100'
                      }`}
                      title="Click to cycle status: OPEN -> IN_PROGRESS -> COMPLETED"
                    >
                      <span>{row.status_badge}</span>
                    </button>
                  </td>
                  <td className="px-5 py-4 text-right font-mono text-slate-500 text-[11px]">
                    {row.created_date}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
};
