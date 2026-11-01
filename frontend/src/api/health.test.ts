import { afterEach, describe, expect, it, vi } from 'vitest';
import { fetchHealth } from './health';

afterEach(() => vi.unstubAllGlobals());
describe('health API (synthetic fetch responses)', () => {
  it('accepts the health contract', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('{"status":"ok"}')),
    );
    await expect(fetchHealth()).resolves.toEqual({ status: 'ok' });
  });
  it('rejects unsuccessful HTTP status', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(new Response('{}', { status: 503 })),
    );
    await expect(fetchHealth()).rejects.toThrow('health check failed');
  });
  it.each([null, {}, { status: 'unknown' }])(
    'rejects malformed payload %j',
    async (payload) => {
      vi.stubGlobal(
        'fetch',
        vi.fn().mockResolvedValue(new Response(JSON.stringify(payload))),
      );
      await expect(fetchHealth()).rejects.toThrow('Unexpected health response');
    },
  );
});
