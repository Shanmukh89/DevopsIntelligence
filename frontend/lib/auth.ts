/** Client-side auth token storage: localStorage + cookie (cookie enables middleware). */

export const AUTH_TOKEN_KEY = "auditr-token";
export const AUTH_COOKIE_NAME = "auditr-token";

const ONE_DAY_SECONDS = 60 * 60 * 24;

function isBrowser(): boolean {
  return typeof window !== "undefined" && typeof document !== "undefined";
}

export function getToken(): string | null {
  if (!isBrowser()) return null;
  return window.localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setToken(token: string): void {
  if (!isBrowser()) return;
  window.localStorage.setItem(AUTH_TOKEN_KEY, token);
  document.cookie = `${AUTH_COOKIE_NAME}=${encodeURIComponent(token)}; Path=/; Max-Age=${ONE_DAY_SECONDS}; SameSite=Lax`;
}

export function clearToken(): void {
  if (!isBrowser()) return;
  window.localStorage.removeItem(AUTH_TOKEN_KEY);
  document.cookie = `${AUTH_COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Lax`;
}
