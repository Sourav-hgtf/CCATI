import { fetchApi } from './client';
import { LoginRequest, TokenResponse, UserProfileResponse } from '../types';

export interface UserRecord {
  user_id: string;
  email: string;
  username: string;
  name: string;
  role: string;
  status: string;
  is_active: boolean;
  created_at?: string;
  last_login_at?: string;
}

export interface UsersListResponse {
  total: number;
  users: UserRecord[];
}

export interface CreateUserPayload {
  email: string;
  username: string;
  full_name: string;
  password: string;
  role: string;
}

export const loginApi = async (payload: LoginRequest): Promise<TokenResponse> => {
  return fetchApi<TokenResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

export const refreshApi = async (refreshToken: string): Promise<TokenResponse> => {
  return fetchApi<TokenResponse>('/auth/refresh', {
    method: 'POST',
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
};

export const logoutApi = async (): Promise<{ message: string }> => {
  return fetchApi<{ message: string }>('/auth/logout', {
    method: 'POST',
  });
};

export const getMeApi = async (): Promise<UserProfileResponse> => {
  return fetchApi<UserProfileResponse>('/auth/me');
};

export const listUsersApi = async (): Promise<UsersListResponse> => {
  return fetchApi<UsersListResponse>('/admin/users');
};

export const createUserApi = async (payload: CreateUserPayload): Promise<UserRecord> => {
  return fetchApi<UserRecord>('/admin/users', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
};

export const updateUserRoleApi = async (userId: string, role: string): Promise<UserRecord> => {
  return fetchApi<UserRecord>(`/admin/users/${userId}/role`, {
    method: 'PATCH',
    body: JSON.stringify({ role }),
  });
};

export const updateUserStatusApi = async (userId: string, isActive: boolean): Promise<UserRecord> => {
  return fetchApi<UserRecord>(`/admin/users/${userId}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ is_active: isActive }),
  });
};
