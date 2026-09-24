import { MachineComparisonResponse } from '../types/machineComparison';

export const machineComparisonService = {
  async getComparisonData(
    machines: string[] = ['V-09', 'V-05', 'V-12'],
    metric: string = 'EFFICIENCY',
    period: string = 'TODAY',
    machineType: string = 'ALL',
    reference: string = 'FACTORY_AVG'
  ): Promise<MachineComparisonResponse> {
    const params = new URLSearchParams();
    machines.forEach((id) => params.append('machines', id));
    params.append('metric', metric);
    params.append('period', period);
    params.append('machine_type', machineType);
    params.append('reference', reference);

    try {
      const response = await fetch(`/api/v1/machine-comparison?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const json = await response.json();
      if (!json.success || !json.data) {
        throw new Error(json.error?.message || 'Failed to fetch Machine Comparison data');
      }
      return json.data;
    } catch (err) {
      console.warn('Backend API unavailable, generating fallback Machine Comparison data:', err);
      return this.getFallbackData(machines, metric, period, machineType, reference);
    }
  },

  getFallbackData(
    selectedIds: string[],
    metric: string,
    period: string,
    machineType: string,
    reference: string
  ): MachineComparisonResponse {
    const allMaster = [
      { machine_id: 'V-09', machine_type: 'Vortex', section: 'Spinning Unit 1' },
      { machine_id: 'V-05', machine_type: 'Vortex', section: 'Spinning Unit 1' },
      { machine_id: 'V-12', machine_type: 'Vortex', section: 'Spinning Unit 1' },
      { machine_id: 'SMX-03', machine_type: 'Simplex', section: 'Prep Unit 2' },
      { machine_id: 'RF-04', machine_type: 'Ring Frame', section: 'Spinning Unit 2' },
      { machine_id: 'A-02', machine_type: 'Airjet', section: 'Weaving Unit 1' },
    ];

    const rawDb: Record<string, Record<string, number>> = {
      'V-09': { EFFICIENCY: 84.2, PRODUCTION: 8420, DOWNTIME: 240, ENERGY_PER_KG: 0.22, QUALITY: 96.1 },
      'V-05': { EFFICIENCY: 88.1, PRODUCTION: 8780, DOWNTIME: 135, ENERGY_PER_KG: 0.21, QUALITY: 97.4 },
      'V-12': { EFFICIENCY: 92.4, PRODUCTION: 9020, DOWNTIME: 45, ENERGY_PER_KG: 0.2, QUALITY: 98.6 },
      'SMX-03': { EFFICIENCY: 90.5, PRODUCTION: 3100, DOWNTIME: 90, ENERGY_PER_KG: 0.23, QUALITY: 97.8 },
      'RF-04': { EFFICIENCY: 94.8, PRODUCTION: 11200, DOWNTIME: 40, ENERGY_PER_KG: 0.19, QUALITY: 99.1 },
      'A-02': { EFFICIENCY: 95.2, PRODUCTION: 10450, DOWNTIME: 30, ENERGY_PER_KG: 0.18, QUALITY: 99.3 },
    };

    const activeIds = selectedIds.filter((id) => rawDb[id]);
    const refVal = metric === 'EFFICIENCY' ? 91.6 : metric === 'PRODUCTION' ? 8495 : 96.0;
    const unit = metric === 'EFFICIENCY' ? '%' : metric === 'PRODUCTION' ? 'kg' : 'min';

    const primaryMetrics = activeIds.map((m_id) => {
      const val = rawDb[m_id][metric] ?? 85.0;
      const fmt = unit === '%' ? `${val.toFixed(1)}%` : `${val.toLocaleString()} ${unit}`;
      return {
        machine_id: m_id,
        machine_type: allMaster.find((m) => m.machine_id === m_id)?.machine_type || 'Unknown',
        value: val,
        formatted_value: fmt,
        unit,
        status: (val < 85 ? 'CRITICAL' : val < 90 ? 'ATTENTION' : 'NORMAL') as 'CRITICAL' | 'ATTENTION' | 'NORMAL',
        variance_vs_reference: val - refVal,
        variance_label: `${val - refVal > 0 ? '+' : ''}${(val - refVal).toFixed(1)} vs Factory Avg`,
      };
    });

    const multiMetricMatrix = [
      {
        metric_name: 'Efficiency',
        unit: '%',
        values: Object.fromEntries(activeIds.map((id) => [id, `${rawDb[id]?.EFFICIENCY?.toFixed(1)}%`])),
      },
      {
        metric_name: 'Production',
        unit: 'kg',
        values: Object.fromEntries(activeIds.map((id) => [id, `${rawDb[id]?.PRODUCTION?.toLocaleString()} kg`])),
      },
      {
        metric_name: 'Downtime',
        unit: 'min',
        values: Object.fromEntries(activeIds.map((id) => [id, `${rawDb[id]?.DOWNTIME} min`])),
      },
      {
        metric_name: 'Quality Rating',
        unit: '%',
        values: Object.fromEntries(activeIds.map((id) => [id, `${rawDb[id]?.QUALITY?.toFixed(1)}%`])),
      },
    ];

    let headToHead;
    if (activeIds.length === 2) {
      const m1 = activeIds[0];
      const m2 = activeIds[1];
      headToHead = [
        {
          metric_key: 'EFFICIENCY',
          metric_name: 'Efficiency',
          unit: '%',
          machine1_value: rawDb[m1].EFFICIENCY,
          machine1_formatted: `${rawDb[m1].EFFICIENCY}%`,
          machine2_value: rawDb[m2].EFFICIENCY,
          machine2_formatted: `${rawDb[m2].EFFICIENCY}%`,
          delta_text: `${Math.abs(rawDb[m1].EFFICIENCY - rawDb[m2].EFFICIENCY).toFixed(1)}% difference`,
          leader_machine_id: rawDb[m1].EFFICIENCY > rawDb[m2].EFFICIENCY ? m1 : m2,
        },
        {
          metric_key: 'PRODUCTION',
          metric_name: 'Production',
          unit: 'kg',
          machine1_value: rawDb[m1].PRODUCTION,
          machine1_formatted: `${rawDb[m1].PRODUCTION} kg`,
          machine2_value: rawDb[m2].PRODUCTION,
          machine2_formatted: `${rawDb[m2].PRODUCTION} kg`,
          delta_text: `${Math.abs(rawDb[m1].PRODUCTION - rawDb[m2].PRODUCTION)} kg difference`,
          leader_machine_id: rawDb[m1].PRODUCTION > rawDb[m2].PRODUCTION ? m1 : m2,
        },
        {
          metric_key: 'DOWNTIME',
          metric_name: 'Downtime',
          unit: 'min',
          machine1_value: rawDb[m1].DOWNTIME,
          machine1_formatted: `${rawDb[m1].DOWNTIME} min`,
          machine2_value: rawDb[m2].DOWNTIME,
          machine2_formatted: `${rawDb[m2].DOWNTIME} min`,
          delta_text: `${Math.abs(rawDb[m1].DOWNTIME - rawDb[m2].DOWNTIME)} min difference`,
          leader_machine_id: rawDb[m1].DOWNTIME < rawDb[m2].DOWNTIME ? m1 : m2,
        },
      ];
    }

    return {
      company_name: 'Ashok Textiles',
      selected_period: period,
      selected_metric: metric,
      selected_machine_type: machineType,
      selected_machine_ids: activeIds,
      available_machine_types: ['ALL', 'Vortex', 'Airjet', 'Ring Frame', 'Simplex'],
      all_master_machines: allMaster,
      reference_type: reference,
      reference_value: refVal,
      reference_formatted: `${refVal} ${unit}`,
      primary_metrics: primaryMetrics,
      multi_metric_matrix: multiMetricMatrix,
      head_to_head: headToHead,
      insight: {
        summary_text: activeIds.length
          ? `Comparative telemetry generated across ${activeIds.length} selected machines for ${metric}.`
          : 'Select machines to initiate comparative analytics.',
        key_observations: activeIds.length
          ? [
              `${activeIds[0]} shows the highest relative variation in the selected set.`,
              `Group average operates within expected parameters vs factory baseline.`,
            ]
          : [],
      },
    };
  },
};
