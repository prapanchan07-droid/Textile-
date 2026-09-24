import { apiClient } from './apiClient';
import { StandardResponse } from '../types/api';
import { FactoryOverviewData, TimePeriod, ComparisonPeriod } from '../types/overview';

export const overviewService = {
  async getOverview(
    period: TimePeriod = 'TODAY',
    comparison: ComparisonPeriod = 'PREVIOUS_DAY',
    unitId?: string,
    userRole: string = 'SUPER_ADMIN',
    sectionAccess: string = 'ALL'
  ): Promise<FactoryOverviewData> {
    const response = await apiClient.get<StandardResponse<FactoryOverviewData>>('/overview', {
      params: {
        period,
        comparison,
        unit_id: unitId,
      },
      headers: {
        'X-User-Role': userRole,
        'X-Section-Access': sectionAccess,
      },
    });

    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.error?.message || 'Failed to fetch factory overview');
  },
};
