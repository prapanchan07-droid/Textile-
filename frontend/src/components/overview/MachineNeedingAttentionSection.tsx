import React from 'react';
import { MachineAttentionItem } from '../../types/overview';
import { Card } from '../ui/Card';

interface MachineNeedingAttentionSectionProps {
  machines: MachineAttentionItem[];
  onViewMachineDetails?: () => void;
}

export const MachineNeedingAttentionSection: React.FC<MachineNeedingAttentionSectionProps> = ({
  machines,
  onViewMachineDetails,
}) => {
  const topMachine = machines.length > 0 ? machines[0] : null;
  const otherMachines = machines.slice(1, 3);

  return (
    <Card className="space-y-5 p-6">
      <div className="flex justify-between items-center border-b border-slate-100 pb-3">
        <div>
          <h2 className="text-xs font-bold uppercase tracking-wider text-slate-400 font-sans">
            4. MACHINE NEEDING ATTENTION
          </h2>
          <p className="text-sm font-bold text-slate-900 mt-0.5">
            Top Problem Machine: <span className="text-rose-600 font-mono font-extrabold">{topMachine?.machine_id || 'V-09'}</span>
          </p>
        </div>
        <span className="text-xs font-bold text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-lg">
          Needs Attention
        </span>
      </div>

      {topMachine && (
        <div className="bg-rose-50/70 border border-rose-200 rounded-xl p-4 space-y-3">
          <div className="flex justify-between items-baseline">
            <h3 className="text-2xl font-extrabold text-slate-900 font-mono">{topMachine.machine_id}</h3>
            <span className="text-xs text-rose-700 font-bold bg-white px-2.5 py-1 rounded-md border border-rose-200">
              Loss: -{topMachine.loss_kg} kg
            </span>
          </div>

          <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
            <div className="bg-white p-2.5 rounded-lg border border-rose-200">
              <span className="text-[10px] text-slate-400 block uppercase font-sans">Efficiency</span>
              <span className="text-amber-700 font-extrabold text-sm">{topMachine.efficiency_pct}%</span>
            </div>
            <div className="bg-white p-2.5 rounded-lg border border-rose-200">
              <span className="text-[10px] text-slate-400 block uppercase font-sans">Factory Avg</span>
              <span className="text-slate-900 font-extrabold text-sm">91.6%</span>
            </div>
            <div className="bg-white p-2.5 rounded-lg border border-rose-200">
              <span className="text-[10px] text-slate-400 block uppercase font-sans">Downtime</span>
              <span className="text-rose-700 font-extrabold text-sm">{topMachine.downtime_minutes} min</span>
            </div>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed pt-1">
            <strong>Summary:</strong> V-09 has the highest observed production loss ({topMachine.loss_kg} kg) and lowest efficiency ({topMachine.efficiency_pct}%) among all machines analyzed today.
          </p>
        </div>
      )}

      {/* Other Machines Summary */}
      {otherMachines.length > 0 && (
        <div className="space-y-2 pt-1">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider">Other machines to watch:</div>
          <div className="space-y-1.5 text-xs">
            {otherMachines.map((m) => (
              <div key={m.machine_id} className="flex justify-between items-center bg-slate-50 p-2.5 rounded-lg border border-slate-200">
                <span className="font-bold text-slate-900 font-mono">{m.machine_id} ({m.machine_type})</span>
                <div className="font-mono text-xs">
                  <span className="text-slate-600 mr-2">Eff: {m.efficiency_pct}%</span>
                  <span className="text-rose-600 font-bold">-{m.loss_kg} kg</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
};
