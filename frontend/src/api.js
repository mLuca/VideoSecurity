const JSON_HEADERS = { "Content-Type": "application/json" };

async function apiFetch(path, options = {}) {
  return fetch(path, { credentials: "include", ...options });
}

export async function checkSession() {
  const res = await apiFetch("/api/session");
  if (!res.ok) return false;
  const data = await res.json();
  return Boolean(data.authenticated);
}

export async function login(password) {
  const res = await apiFetch("/api/login", {
    method: "POST",
    headers: JSON_HEADERS,
    body: JSON.stringify({ password }),
  });
  if (res.ok) return { ok: true };
  const data = await res.json().catch(() => ({}));
  return { ok: false, error: data.error || "Login failed." };
}

export async function logout() {
  await apiFetch("/api/logout", { method: "POST" });
}

export async function fetchCaptures() {
  const res = await apiFetch("/api/captures");
  if (!res.ok) throw new Error("Failed to load captures.");
  return res.json();
}

export async function deleteCapture(name) {
  const res = await apiFetch(`/api/captures/${encodeURIComponent(name)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error("Failed to delete capture.");
}

export async function fetchLogs() {
  const res = await apiFetch("/api/logs");
  if (!res.ok) throw new Error("Failed to load logs.");
  return res.json();
}
