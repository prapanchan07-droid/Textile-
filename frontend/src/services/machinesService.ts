import { apiClient } from './apiClient';
import { StandardResponse } from '../types/api';
import { MachinesModuleData } from '../types/machines';

export const machinesService = {
  async getMachinesData(
    period: string = 'THIS_MONTH',
    machineType: string = 'ALL',
    machineId: string = 'ALL'
  ): Promise<MachinesModuleData> {
    const response = await apiClient.get<StandardResponse<MachinesModuleData>>('/machines', {
      params: { period, machine_type: machineType, machine_id: machineId },
    });

    if (response.data.success && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.error?.message || 'Failed to fetch Machines & Downtime data');
  },
};
