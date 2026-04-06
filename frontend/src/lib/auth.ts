import { removeToken, getToken } from './api';

/**
 * Returns true when a JWT token is present in localStorage.
 * NOTE: This only checks presence, not validity. The server will reject
 * expired tokens on the next authenticated request.
 */
export function isAuthenticated(): boolean {
  return Boolean(getToken());
}

/**
 * Clears the stored JWT and redirects to /login.
 */
export function logout(): void {
  removeToken();
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}
