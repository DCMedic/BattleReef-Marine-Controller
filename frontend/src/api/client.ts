const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";
const TOKEN_KEY = "battlereef.access_token";
const PRINCIPAL_KEY = "battlereef.principal";

export type AuthPrincipal = { username: string; role: string; principal_type: string };
export type LoginResponse = AuthPrincipal & { access_token: string; token_type: string; expires_in: number };

const ROLE_LEVEL: Record<string, number> = { viewer: 10, operator: 20, engineer: 30, administrator: 40 };
export function roleAllows(actual: string, required: string): boolean {
  return (ROLE_LEVEL[actual] ?? -1) >= (ROLE_LEVEL[required] ?? Number.MAX_SAFE_INTEGER);
}

export function getAccessToken(): string | null {
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getStoredPrincipal(): AuthPrincipal | null {
  const raw = window.localStorage.getItem(PRINCIPAL_KEY);
  if (!raw) return null;
  try { return JSON.parse(raw) as AuthPrincipal; } catch { return null; }
}

export function storeSession(session: LoginResponse): void {
  window.localStorage.setItem(TOKEN_KEY, session.access_token);
  window.localStorage.setItem(PRINCIPAL_KEY, JSON.stringify({ username: session.username, role: session.role, principal_type: session.principal_type }));
}

export function clearSession(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(PRINCIPAL_KEY);
}

function authHeaders(extra: Record<string, string> = {}): HeadersInit {
  const token = getAccessToken();
  return token ? { ...extra, Authorization: `Bearer ${token}` } : extra;
}

async function parseResponse<T>(response: Response, method: string, path: string): Promise<T> {
  if (response.status === 401) clearSession();
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${method} ${path} failed: ${response.status} ${text}`);
  }
  return response.json() as Promise<T>;
}

export async function login(username: string, password: string): Promise<LoginResponse> {
  const response = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  const session = await parseResponse<LoginResponse>(response, "POST", "/auth/login");
  storeSession(session);
  return session;
}

export async function fetchCurrentPrincipal(): Promise<AuthPrincipal> {
  const response = await fetch(`${API_BASE_URL}/auth/me`, { headers: authHeaders() });
  return parseResponse<AuthPrincipal>(response, "GET", "/auth/me");
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, { headers: authHeaders() });
  return parseResponse<T>(response, "GET", path);
}

export async function apiPost<TResponse, TRequest>(path: string, payload: TRequest): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  return parseResponse<TResponse>(response, "POST", path);
}

export async function apiPostEmpty<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, { method: "POST", headers: authHeaders() });
  return parseResponse<TResponse>(response, "POST", path);
}

export async function apiPut<TResponse, TRequest>(path: string, payload: TRequest): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: authHeaders({ "Content-Type": "application/json" }),
    body: JSON.stringify(payload),
  });
  return parseResponse<TResponse>(response, "PUT", path);
}

export async function apiDelete<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, { method: "DELETE", headers: authHeaders() });
  return parseResponse<TResponse>(response, "DELETE", path);
}
