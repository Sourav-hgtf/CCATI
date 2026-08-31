const API_BASE = ((import.meta.env.VITE_API_URL as string) || '').replace(/\/$/, '') + '/api/v1';

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const rawToken = localStorage.getItem('auth_token');
  const token = rawToken && rawToken !== 'null' && rawToken !== 'undefined' ? rawToken : '';
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...options.headers,
  };

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        // Clear invalid or expired session tokens
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('auth_user');
        window.dispatchEvent(new CustomEvent('auth:unauthorized'));
      }

      const errorData = await response.json().catch(() => ({}));
      const message =
        typeof errorData.detail === 'string'
          ? errorData.detail
          : errorData.error?.message || `API error: ${response.status}`;
      throw new Error(message);
    }

    return await response.json();
  } catch (err) {
    throw err;
  }
}
