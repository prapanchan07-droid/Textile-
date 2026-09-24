import { apiClient } from './apiClient';
import { StandardResponse, HealthResponseData } from '../types/api';

export const healthService = {
  async getHealth(): Promise<HealthResponseData> {
    const response = await apiClient.get<StandardResponse<HealthResponseData>>('/health');
    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.error?.message || 'Failed to fetch health status');
  },
};
