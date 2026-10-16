import axios, { AxiosError } from 'axios';
import type { StandardResponse } from '../types/api';
import { clearToken, getToken } from '../auth/token';

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 120_000,
});

http.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/** Fired when the API rejects our token, so the app can send the user back to sign in. */
export const UNAUTHORIZED_EVENT = 'auth:unauthorized';

http.interceptors.response.use(
  (res) => res,
  (err) => {
    // A failed sign-in is also a 401, but the login form shows that error itself.
    if (err?.response?.status === 401 && !String(err.config?.url).includes('/auth/login')) {
      clearToken();
      window.dispatchEvent(new Event(UNAUTHORIZED_EVENT));
    }
    return Promise.reject(err);
  },
);

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

export async function postJson<T>(url: string, body: unknown): Promise<T> {
  try {
    const res = await http.post<StandardResponse<T>>(url, body);
    if (res.data.data == null) throw new ApiError(res.data.error?.message || 'Request failed', res.status);
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
