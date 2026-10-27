import { useQuery } from '@tanstack/react-query';
import { getData } from './client';
import type { HealthResponseData } from '../types/api';

export const qk = {
  all: ['api'] as const,
  health: ['api', 'health'] as const,
};

export const useHealth = () =>
  useQuery({
    queryKey: qk.health,
    queryFn: () => getData<HealthResponseData>('/health'),
    refetchInterval: 60_000,
    retry: false,
  });
