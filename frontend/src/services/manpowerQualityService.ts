import { apiClient } from './apiClient';
import { StandardResponse } from '../types/api';
import { ManpowerQualityModuleData } from '../types/manpowerQuality';

export const manpowerQualityService = {
  async getManpowerQualityData(period: string = 'THIS_MONTH'): Promise<ManpowerQualityModuleData> {
    const response = await apiClient.get<StandardResponse<ManpowerQualityModuleData>>('/manpower-quality', {
      params: { period },
    });

    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.error?.message || 'Failed to fetch Manpower & Quality module data');
  },
};
