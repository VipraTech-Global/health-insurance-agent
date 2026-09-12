export type ApiError = { error?: { code?: string; message?: string } };

export async function ensureCsrf(): Promise<string> {
  const response = await fetch("/api/v1/auth/csrf/", { credentials: "include", cache: "no-store" });
  const data = await response.json();
  return data.csrfToken;
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const method = init.method?.toUpperCase() ?? "GET";
  const headers = new Headers(init.headers);
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) headers.set("X-CSRFToken", await ensureCsrf());
  if (init.body) headers.set("Content-Type", "application/json");
  const response = await fetch(path, { ...init, headers, credentials: "include", cache: "no-store" });
  if (!response.ok) {
    const data: ApiError = await response.json().catch(() => ({}));
    throw new Error(data.error?.message ?? `Request failed (${response.status})`);
  }
  if (response.status === 204) return undefined as T;
  return response.json();
}
