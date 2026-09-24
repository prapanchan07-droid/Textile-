import React from 'react';
import { MultiMetricRow } from '../../types/machineComparison';
import { Layers } from 'lucide-react';

interface MultiMetricComparisonProps {
  selectedMachineIds: string[];
  matrix: MultiMetricRow[];
}

export const MultiMetricComparison: React.FC<MultiMetricComparisonProps> = ({
  selectedMachineIds,
  matrix,
}) => {
  if (!selectedMachineIds || selectedMachineIds.length === 0 || !matrix || matrix.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
      <div className="flex items-center gap-2 border-b border-slate-100 pb-3">
        <Layers className="w-4 h-4 text-slate-700" />
        <h3 className="text-base font-bold text-slate-900 uppercase tracking-tight">
          Multi-Metric Performance Matrix
        </h3>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead className="bg-slate-50 text-slate-500 uppercase font-bold text-[10px] tracking-wider border-b border-slate-200">
            <tr>
              <th className="px-4 py-3">Metric</th>
              {selectedMachineIds.map((id) => (
                <th key={id} className="px-4 py-3 text-center font-mono text-slate-900 font-extrabold text-xs">
                  {id}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 font-medium text-slate-800">
            {matrix.map((row) => (
              <tr key={row.metric_name} className="hover:bg-slate-50/80 transition-colors">
                <td className="px-4 py-3.5 font-bold text-slate-900">{row.metric_name}</td>
                {selectedMachineIds.map((id) => (
                  <td key={id} className="px-4 py-3.5 text-center font-mono font-bold text-slate-900 text-xs">
                    {row.values[id] || 'N/A'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
