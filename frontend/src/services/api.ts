// src/services/api.ts
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || '/api';

// =============================================================================
// Token storage
// =============================================================================
const ACCESS_KEY = 'rc_access_token';
const REFRESH_KEY = 'rc_refresh_token';

export const tokenStorage = {
  getAccess: (): string | null => localStorage.getItem(ACCESS_KEY),
  getRefresh: (): string | null => localStorage.getItem(REFRESH_KEY),
  set: (access: string, refresh: string): void => {
    localStorage.setItem(ACCESS_KEY, access);
    localStorage.setItem(REFRESH_KEY, refresh);
  },
  clear: (): void => {
    localStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
  },
};

// =============================================================================
// Axios instance
// =============================================================================
export const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  timeout: Number(import.meta.env.VITE_API_TIMEOUT) || 30000,
  headers: { 'Content-Type': 'application/json' },
});

// =============================================================================
// Request interceptor — افزودن Authorization
// =============================================================================
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = tokenStorage.getAccess();
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// =============================================================================
// Response interceptor — refresh خودکار
// =============================================================================
let isRefreshing = false;
let pendingRequests: Array<(token: string) => void> = [];

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status === 401 && !original._retry) {
      const refresh = tokenStorage.getRefresh();

      if (!refresh) {
        tokenStorage.clear();
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      original._retry = true;

      if (isRefreshing) {
        return new Promise((resolve) => {
          pendingRequests.push((token: string) => {
            if (original.headers) {
              original.headers.Authorization = `Bearer ${token}`;
            }
            resolve(api(original));
          });
        });
      }

      isRefreshing = true;

      try {
        const { data } = await axios.post(`${API_URL}/accounts/token/refresh/`, {
          refresh,
        });
        const newAccess: string = data.access;

        tokenStorage.set(newAccess, refresh);
        pendingRequests.forEach((cb) => cb(newAccess));
        pendingRequests = [];

        if (original.headers) {
          original.headers.Authorization = `Bearer ${newAccess}`;
        }
        return api(original);
      } catch {
        tokenStorage.clear();
        pendingRequests = [];
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  },
);

// =============================================================================
// Helper — پیام خطای DRF
// =============================================================================
export function getApiErrorMessage(error: unknown, fallback = 'خطایی رخ داد'): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as Record<string, unknown> | undefined;
    if (!data) return error.message || fallback;

    if (typeof data.detail === 'string') return data.detail;

    const errorsObj = (data.errors ?? data) as Record<string, string[] | string>;
    for (const value of Object.values(errorsObj)) {
      if (Array.isArray(value) && value.length > 0) return String(value[0]);
      if (typeof value === 'string') return value;
    }
  }
  return fallback;
}

// =============================================================================
// Helper — استخراج URL نسبی از URL مطلق (برای next/previous pagination)
// =============================================================================
export function stripHost(url: string): string {
  try {
    const parsed = new URL(url);
    return parsed.pathname.replace(/^\/api/, '') + parsed.search;
  } catch {
    return url.replace(/^https?:\/\/[^/]+/, '').replace(/^\/api/, '');
  }
}