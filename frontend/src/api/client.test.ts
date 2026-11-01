import { afterEach, expect, it, vi } from 'vitest';
import { searchPlaces } from './client';

afterEach(() => vi.unstubAllGlobals());
it('reports structured provider errors without presenting a successful response', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValue(
        new Response(
          JSON.stringify({ error: { message: 'Free service quota reached.' } }),
          { status: 503 },
        ),
      ),
  );
  await expect(
    searchPlaces('Dallas', new AbortController().signal),
  ).rejects.toThrow('Free service quota');
});
it('reports unreadable upstream HTML safely', async () => {
  vi.stubGlobal(
    'fetch',
    vi
      .fn()
      .mockResolvedValue(
        new Response('<html>Unavailable</html>', { status: 502 }),
      ),
  );
  await expect(
    searchPlaces('Dallas', new AbortController().signal),
  ).rejects.toThrow('unreadable response');
});
it('rejects malformed geocoding coordinates', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          places: [{ id: 'a', label: 'Invalid', position: [200, 30] }],
        }),
      ),
    ),
  );
  await expect(
    searchPlaces('Dallas', new AbortController().signal),
  ).rejects.toThrow('unexpected response');
});
