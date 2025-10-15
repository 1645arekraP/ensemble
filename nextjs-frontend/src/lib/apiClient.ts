let accessToken: string | null = null;
let isRefreshing = false;

// The queue now stores both resolve and reject functions for each pending request
let failedQueue: { resolve: (value: any) => void; reject: (reason?: any) => void; }[] = [];

const processQueue = (error: Error | null, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      // If there's an error, reject the promise of the waiting request
      prom.reject(error);
    } else {
      // If we have a new token, resolve the promise of the waiting request
      // (Note: The promise itself will re-run the fetch, so we don't pass the token here)
      prom.resolve(undefined);
    }
  });
  failedQueue = [];
};

export const apiClient = async (url: string, options: RequestInit = {}) => {
  const headers = new Headers(options.headers);

  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }
  options.headers = headers;

  let response = await fetch(url, options);

  if (response.status === 401) {
    if (!isRefreshing) {
      isRefreshing = true;
      try {
        const refreshResponse = await fetch('/api/auth/refresh/', { method: 'POST' });
        if (!refreshResponse.ok) throw new Error('Session expired.');

        const { access: newAccessToken } = await refreshResponse.json();
        setAccessToken(newAccessToken);
        
        processQueue(null, newAccessToken); // Process queued requests successfully
        
        // Retry the original request
        headers.set('Authorization', `Bearer ${newAccessToken}`);
        options.headers = headers;
        return await fetch(url, options);

      } catch (error) {
        processQueue(error as Error, null); // Process queued requests with an error
        logout();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(error);
      } finally {
        isRefreshing = false;
      }
    }

    // Queue the failed request
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve: () => resolve(apiClient(url, options)), reject });
    });
  }

  return response;
};

// --- Helper Functions ---

export const setAccessToken = (token: string | null) => {
  console.log("token set");
  accessToken = token;
};

export class AuthError extends Error {
  constructor(message = 'Authentication Error') {
    super(message);
    this.name = 'AuthError';
  }
}

export const logout = () => {
  // Send an authenticated request to the backend to invalidate the session
  // and clear the httpOnly cookie.
  // We don't need to do anything with the response.
  try {
    apiClient('/api/auth/logout/', {
      method: 'POST',
    });
  } catch (error) {
    // Even if this call fails, the user is logged out on the frontend.
    // This could happen if the network is down.
    console.error("Logout API call failed", error);
  }
  setAccessToken(null);
};

export const initializeAuth = async (): Promise<void> => {
  try {
    const refreshResponse = await fetch('/api/auth/refresh/', { method: 'POST' });
    if (!refreshResponse.ok) throw new Error('No valid session.');
    
    const { access: newAccessToken } = await refreshResponse.json();
    setAccessToken(newAccessToken);
    console.log("Refreshed")
  } catch (error) {
    processQueue(error as Error, null);
    logout();
    if (typeof window !== 'undefined') {
        window.location.href = '/login';
    }
    // Throw our new custom error instead of a generic one
    return Promise.reject(new AuthError('Session expired.'));
    } 
};