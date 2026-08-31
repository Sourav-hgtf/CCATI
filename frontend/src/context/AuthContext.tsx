import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { loginApi, logoutApi, getMeApi, refreshApi } from '../api/auth';
import { UserProfileResponse, TokenResponse } from '../types';

export interface AuthContextType {
  user: UserProfileResponse | null;
  token: string | null;
  role: string;
  permissions: string[];
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password?: string) => Promise<TokenResponse>;
  logout: () => Promise<void>;
  hasRole: (allowedRoles: string[]) => boolean;
  hasPermission: (permission: string) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfileResponse | null>(() => {
    try {
      const saved = localStorage.getItem('auth_user');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [token, setToken] = useState<string | null>(() => {
    const saved = localStorage.getItem('auth_token');
    return saved && saved !== 'null' && saved !== 'undefined' ? saved : null;
  });

  const [isLoading, setIsLoading] = useState<boolean>(true);

  const clearSession = useCallback(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('auth_user');
    setToken(null);
    setUser(null);
  }, []);

  // Verify session with server on initial load
  useEffect(() => {
    const initAuth = async () => {
      const storedToken = localStorage.getItem('auth_token');
      if (storedToken && storedToken !== 'null' && storedToken !== 'undefined') {
        try {
          const profile = await getMeApi();
          setUser(profile);
          localStorage.setItem('auth_user', JSON.stringify(profile));
        } catch (err) {
          // If token invalid, attempt refresh or clear
          const refToken = localStorage.getItem('refresh_token');
          if (refToken) {
            try {
              const res = await refreshApi(refToken);
              localStorage.setItem('auth_token', res.access_token);
              if (res.refresh_token) {
                localStorage.setItem('refresh_token', res.refresh_token);
              }
              setToken(res.access_token);
              const profile = await getMeApi();
              setUser(profile);
              localStorage.setItem('auth_user', JSON.stringify(profile));
            } catch {
              clearSession();
            }
          } else {
            clearSession();
          }
        }
      } else {
        clearSession();
      }
      setIsLoading(false);
    };

    initAuth();

    const handleUnauthorized = () => {
      clearSession();
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized);
  }, [clearSession]);

  const login = async (email: string, password: string = 'password'): Promise<TokenResponse> => {
    setIsLoading(true);
    try {
      const res = await loginApi({ email, password });
      localStorage.setItem('auth_token', res.access_token);
      if (res.refresh_token) {
        localStorage.setItem('refresh_token', res.refresh_token);
      }
      setToken(res.access_token);

      const usernameFromEmail = email.split('@')[0];
      const displayName = res.full_name || res.username || (usernameFromEmail.charAt(0).toUpperCase() + usernameFromEmail.slice(1));

      const profile: UserProfileResponse = {
        user_id: res.user_id,
        email: res.email,
        username: res.username,
        name: displayName,
        role: res.role,
        permissions: res.permissions || [],
      };

      setUser(profile);
      localStorage.setItem('auth_user', JSON.stringify(profile));
      return res;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = async () => {
    try {
      if (token) {
        await logoutApi().catch(() => {});
      }
    } finally {
      clearSession();
    }
  };

  const hasRole = (allowedRoles: string[]): boolean => {
    if (!user) return false;
    if (user.role === 'Admin') return true;
    return allowedRoles.includes(user.role);
  };

  const hasPermission = (permission: string): boolean => {
    if (!user) return false;
    if (user.role === 'Admin') return true;
    return user.permissions?.includes(permission) || false;
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        role: user?.role || 'Anonymous',
        permissions: user?.permissions || [],
        isAuthenticated: !!token && !!user,
        isLoading,
        login,
        logout,
        hasRole,
        hasPermission,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
