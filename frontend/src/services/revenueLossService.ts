import { apiClient } from './apiClient';
import { StandardResponse } from '../types/api';
import { RevenueLossModuleData } from '../types/revenueLoss';

export const revenueLossService = {
  async getRevenueLossData(period: string = 'THIS_MONTH'): Promise<RevenueLossModuleData> {
    const response = await apiClient.get<StandardResponse<RevenueLossModuleData>>('/revenue-loss', {
      params: { period },
    });

    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.error?.message || 'Failed to fetch Revenue & Loss module data');
  },
};
