export type AuthToken = string;

const TOKEN_KEY = 'api_auth_token';

export function getToken(): AuthToken | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token: AuthToken) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

