export interface Health {
  status: 'ok';
}

export async function fetchHealth(signal?: AbortSignal): Promise<Health> {
  const base = import.meta.env.VITE_API_BASE_URL || '/api/v1';
  const response = await fetch(`${base.replace(/\/$/, '')}/health`, { signal });
  if (!response.ok) throw new Error('Backend health check failed.');
  const data: unknown = await response.json();
  if (
    typeof data !== 'object' ||
    data === null ||
    !('status' in data) ||
    data.status !== 'ok'
  ) {
    throw new Error('Unexpected health response.');
  }
  return { status: 'ok' };
}
