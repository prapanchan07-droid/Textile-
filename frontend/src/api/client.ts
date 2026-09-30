import axios, { AxiosError } from 'axios';
import type { StandardResponse } from '../types/api';

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 120_000,
});

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    readonly code?: string,
  ) {
    super(message);
  }
}

const toApiError = (err: unknown): ApiError => {
  if (err instanceof ApiError) return err;
  if (err instanceof AxiosError) {
    const body = err.response?.data as StandardResponse<unknown> | undefined;
    if (body?.error?.message) return new ApiError(body.error.message, err.response?.status, body.error.code);
    if (!err.response) return new ApiError('Cannot reach the server. Check that the API is running.', undefined, 'NETWORK');
    return new ApiError(`Request failed (${err.response.status})`, err.response.status);
  }
  return new ApiError(err instanceof Error ? err.message : 'Unexpected error');
};

/** GET an endpoint that returns the StandardResponse envelope and unwrap `data`. */
export async function getData<T>(url: string, params?: Record<string, unknown>): Promise<T> {
  try {
    const res = await http.get<StandardResponse<T>>(url, {
      params,
      // FastAPI expects repeated keys for list params: machines=a&machines=b
      paramsSerializer: { indexes: null },
    });
    if (!res.data.success || res.data.data == null) {
      throw new ApiError(res.data.error?.message || 'The server returned no data', res.status, res.data.error?.code);
    }
    return res.data.data;
  } catch (err) {
    throw toApiError(err);
  }
}

export async function postForm<T>(url: string, form: FormData): Promise<T> {
  try {
    const res = await http.post<StandardResponse<T>>(url, form);
    if (res.data.data == null) throw new ApiError(res.data.error?.message || 'Request failed', res.status);
    return res.data.data;
  } catch (err) {
    throw toApiError(err);
  }
}
