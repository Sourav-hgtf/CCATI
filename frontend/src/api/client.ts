const API_BASE = '/api/v1';

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}, fallbackMockData?: T): Promise<T> {
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
      if (fallbackMockData !== undefined) {
        return fallbackMockData;
      }
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API error: ${response.status}`);
    }

    return await response.json();
  } catch (err) {
    if (fallbackMockData !== undefined) {
      return fallbackMockData;
    }
    throw err;
  }
}
