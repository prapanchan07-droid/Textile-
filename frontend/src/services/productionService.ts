import { apiClient } from './apiClient';
import { StandardResponse } from '../types/api';
import { ProductionModuleData } from '../types/production';

export const productionService = {
  async getProductionData(period: string = 'THIS_MONTH', date?: string, unit?: string): Promise<ProductionModuleData> {
    try {
      const params: Record<string, string> = { period };
      if (date) params.date = date;
      if (unit) params.unit = unit;

      const response = await apiClient.get<StandardResponse<ProductionModuleData>>('/production', {
        params,
      });

      if (response.data.success && response.data.data) {
        return response.data.data;
      }
      throw new Error(response.data.error?.message || 'Failed to fetch Production module data');
    } catch (err) {
      console.warn('Backend production API unavailable, using fallback telemetry:', err);
      return this.getFallbackData(period);
    }
  },

  getFallbackData(period: string): ProductionModuleData {
    return {
      company_name: 'Ashok Textiles',
      selected_period: period,
      actual_kg: 0,
      target_kg: 0,
      gap_kg: 0,
      achievement_pct: 0,
      trend: [],
      machine_type_performance: [],
      loss_reasons: [],
      shift_performance: [],
      production_factors: [],
      comparison: {
        reference_period: 'Previous Period',
        reference_kg: 0,
        current_kg: 0,
        difference_kg: 0,
        difference_pct: 0,
        main_reason: 'No Data',
      },
      ai_analysis: {
        summary: 'No production data available for this period.',
        affected_machine_type: 'N/A',
        main_observed_factor: 'No Data Ingested',
        recommended_action: 'Upload a factory production report for this date.',
      },
    };
  },
};
