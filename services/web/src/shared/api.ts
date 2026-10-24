const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const accessTokenKey = "smart-farmland.access-token";
const refreshTokenKey = "smart-farmland.refresh-token";

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export function hasSession(): boolean {
  return Boolean(sessionStorage.getItem(accessTokenKey));
}

export function clearSession(): void {
  sessionStorage.removeItem(accessTokenKey);
  sessionStorage.removeItem(refreshTokenKey);
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  token = sessionStorage.getItem(accessTokenKey),
  refreshOnUnauthorized = true,
): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Accept", "application/json");
  if (options.body) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${apiBaseUrl}${path}`, { ...options, headers });
  if (response.status === 401 && path !== "/auth/login" && refreshOnUnauthorized) {
    const refreshToken = sessionStorage.getItem(refreshTokenKey);
    if (refreshToken) {
      const refreshResponse = await fetch(`${apiBaseUrl}/auth/refresh`, {
        method: "POST",
        headers: { Accept: "application/json", "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: refreshToken }),
      });
      if (refreshResponse.ok) {
        const refreshed = (await refreshResponse.json()) as AuthTokens;
        saveSession(refreshed);
        return request<T>(path, options, refreshed.access_token);
      }
    }
    clearSession();
    if (typeof window !== "undefined") window.location.assign("/login");
  }

  if (!response.ok) {
    let message = `درخواست با خطای ${response.status} مواجه شد`;
    try {
      const payload = (await response.json()) as { detail?: string; message?: string };
      message = payload.detail ?? payload.message ?? message;
    } catch {
      // Keep the HTTP status message when the server does not return JSON.
    }
    throw new Error(message);
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function saveSession(tokens: AuthTokens): void {
  sessionStorage.setItem(accessTokenKey, tokens.access_token);
  sessionStorage.setItem(refreshTokenKey, tokens.refresh_token);
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path);
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}

export async function endSession(): Promise<void> {
  const refreshToken = sessionStorage.getItem(refreshTokenKey);
  try {
    if (refreshToken) {
      await request<unknown>(
        "/auth/logout",
        { method: "POST", body: JSON.stringify({ refresh_token: refreshToken }) },
        null,
        false,
      );
    }
  } finally {
    clearSession();
  }
}
