export const AUTH = 'Basic ' + btoa('admin:ziva_admin_password');

async function get(path) {
  const res = await fetch(path, { headers: { Authorization: AUTH } });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return res.json();
}

export function fetchStats() { return get('/api/stats'); }
export function fetchMemory() { return get('/api/memory'); }
export function fetchMetrics() { return get('/metrics').catch(() => null); }
export function fetchAgents() { return get('/api/v1/agents/status').catch(() => null); }
export function fetchSyncStats() { return get('/sync/stats').catch(() => null); }

export async function sendChat(message, signal) {
  const res = await fetch('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: AUTH },
    body: JSON.stringify({ message, compact: true }),
    signal,
  });
  return res.json();
}
