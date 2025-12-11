/**
 * JWT token storage and retrieval utilities
 */

const TOKEN_KEY = 'jwt_token';

export const jwtUtils = {
  getToken: (): string | null => {
    const token = localStorage.getItem(TOKEN_KEY);

    // Development fallback: use mock token if no real token exists
    // This allows testing without Google OAuth setup
    if (!token && import.meta.env.DEV) {
      console.log('[DEV] Using mock JWT token for unauthenticated development');
      return 'mock-jwt-token';
    }

    return token;
  },

  setToken: (token: string): void => {
    localStorage.setItem(TOKEN_KEY, token);
  },

  removeToken: (): void => {
    localStorage.removeItem(TOKEN_KEY);
  },

  hasToken: (): boolean => {
    return !!localStorage.getItem(TOKEN_KEY);
  }
};

