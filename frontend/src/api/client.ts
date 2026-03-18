const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

async function parseResponse<T>(response: Response, method: string, path: string): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API ${method} ${path} failed: ${response.status} ${text}`);
  }

  return response.json() as Promise<T>;
}

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  return parseResponse<T>(response, "GET", path);
}

export async function apiPost<TResponse, TRequest>(
  path: string,
  payload: TRequest
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return parseResponse<TResponse>(response, "POST", path);
}

export async function apiPostEmpty<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
  });

  return parseResponse<TResponse>(response, "POST", path);
}

export async function apiPut<TResponse, TRequest>(
  path: string,
  payload: TRequest
): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  return parseResponse<TResponse>(response, "PUT", path);
}

export async function apiDelete<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "DELETE",
  });

  return parseResponse<TResponse>(response, "DELETE", path);
}