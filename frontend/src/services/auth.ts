// src/services/auth.ts
import api, { tokenStorage } from './api';
import type { LoginPayload, LoginResponse, SignupPayload, User } from '../types';

export const authService = {
  async login(payload: LoginPayload): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/accounts/login/', payload);
    tokenStorage.set(data.access, data.refresh);
    return data;
  },

  async signup(payload: SignupPayload): Promise<{ user_id: number; email: string }> {
    const { data } = await api.post('/accounts/signup/', payload);
    return data;
  },

  async verifyEmail(email: string, code: string): Promise<LoginResponse> {
    const { data } = await api.post<LoginResponse>('/accounts/verify-email/', {
      email,
      code,
    });
    tokenStorage.set(data.access, data.refresh);
    return data;
  },

  async resendCode(email: string): Promise<void> {
    await api.post('/accounts/resend-code/', { email });
  },

  async logout(): Promise<void> {
    const refresh = tokenStorage.getRefresh();
    try {
      if (refresh) await api.post('/accounts/logout/', { refresh });
    } catch {
      // ignore
    } finally {
      tokenStorage.clear();
    }
  },

  async getProfile(): Promise<User> {
    const { data } = await api.get<User>('/accounts/profile/');
    return data;
  },

  async updateProfile(patch: Partial<User>): Promise<User> {
    const { data } = await api.patch<User>('/accounts/profile/', patch);
    return data;
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<void> {
    await api.post('/accounts/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },
};