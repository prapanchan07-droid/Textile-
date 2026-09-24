import React from 'react';
import { QualityMachineItem } from '../../types/manpowerQuality';
import { Card } from '../ui/Card';

interface QualityIssueMachineSectionProps {
  issues: QualityMachineItem[];
}

export const QualityIssueMachineSection: React.FC<QualityIssueMachineSectionProps> = ({
  issues,
}) => {
  return (
    <Card className="space-y-4 p-6">
      <div className="border-b border-slate-100 pb-3">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
          7. QUALITY ISSUE BY MACHINE / PROCESS
        </h2>
        <p className="text-sm font-bold text-slate-900 mt-0.5">
          Machines & processes associated with quality parameter deviations
        </p>
      </div>

      <div className="overflow-x-auto rounded-xl border border-slate-200">
        <table className="w-full text-left text-xs font-sans">
          <thead className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
            <tr>
              <th className="py-3 px-4">Machine / Process</th>
              <th className="py-3 px-4">Quality Issue</th>
              <th className="py-3 px-4 text-right">Current Value</th>
              <th className="py-3 px-4 text-right">Spec Limit</th>
              <th className="py-3 px-4 text-center">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-medium text-slate-900">
            {issues.map((item, idx) => {
              const isOutOfLimit = item.status === 'OUT OF LIMIT';
              const isAttention = item.status === 'ATTENTION';

              const badgeStyle = isOutOfLimit
                ? 'bg-rose-50 text-rose-700 border-rose-200'
                : isAttention
                ? 'bg-amber-50 text-amber-800 border-amber-200'
                : 'bg-emerald-50 text-emerald-700 border-emerald-200';

              return (
                <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                  <td className="py-3 px-4 font-bold text-slate-900 font-mono">{item.machine_process}</td>
                  <td className="py-3 px-4 text-slate-700 font-semibold">{item.quality_issue}</td>
                  <td className="py-3 px-4 text-right font-mono font-bold">
                    <span className={isOutOfLimit ? 'text-rose-600' : 'text-slate-900'}>
                      {item.current_value} {item.unit}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right font-mono text-slate-500">
                    {item.limit} {item.unit}
                  </td>
                  <td className="py-3 px-4 text-center font-sans">
                    <span className={`inline-block px-2.5 py-0.5 rounded-full text-[10px] font-extrabold border ${badgeStyle}`}>
                      {item.status}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
};
