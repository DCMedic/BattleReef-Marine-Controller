const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "/api/v1";

export async function apiGet<T>(path: string): Promise<T> {
  const url = `${API_BASE_URL}${path}`;

  let response: Response;

  try {
    response = await fetch(url, {
      method: "GET",
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown network error";
    throw new Error(`Network request failed for ${url}: ${message}`);
  }

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`API GET ${url} failed: ${response.status} ${text}`);
  }

  return response.json() as Promise<T>;
}