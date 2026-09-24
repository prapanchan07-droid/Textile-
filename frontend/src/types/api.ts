export interface ErrorDetail {
  code: string;
  message: string;
  details?: any;
}

export interface StandardResponse<T> {
  success: boolean;
  data?: T;
  error?: ErrorDetail;
}

export interface DatabaseHealth {
  status: 'healthy' | 'unhealthy' | 'degraded';
  database_type?: string;
  error?: string;
  reason?: string;
}

export interface HealthResponseData {
  status: 'healthy' | 'unhealthy' | 'degraded';
  project_name: string;
  company: string;
  version: string;
  environment: string;
  database: DatabaseHealth;
  active_module: string;
}
