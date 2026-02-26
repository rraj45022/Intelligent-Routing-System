export async function authedFetch(token, path, options = {}) {
  if (!token) {
    throw new Error("Missing token; please log in again.");
  }
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
    Authorization: `Bearer ${token}`,
  };

  const resp = await fetch(`/api${path}`, { ...options, headers });
  if (resp.status === 401) {
    throw new Error("Session expired. Please log in again.");
  }
  return resp;
}

export async function authedJson(token, path, options = {}) {
  const resp = await authedFetch(token, path, options);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(text || `Request failed (${resp.status})`);
  }
  if (resp.status === 204) return null;
  return resp.json();
}
