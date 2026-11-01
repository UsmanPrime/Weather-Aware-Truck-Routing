import { z } from 'zod';
import { placeSchema, planSchema, type PlanRequest } from './contracts';

const base = (import.meta.env.VITE_API_BASE_URL || '/api/v1').replace(
  /\/$/,
  '',
);
function messages(value: unknown): string[] {
  if (typeof value === 'string') return [value];
  if (Array.isArray(value)) return value.flatMap(messages);
  if (typeof value === 'object' && value !== null)
    return Object.values(value).flatMap(messages);
  return [];
}
export async function request<T>(
  path: string,
  schema: z.ZodType<T>,
  signal: AbortSignal,
  body?: unknown,
): Promise<T> {
  const response = await fetch(base + path, {
    signal: AbortSignal.any([signal, AbortSignal.timeout(45000)]),
    method: body === undefined ? 'GET' : 'POST',
    headers:
      body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data: unknown = await response.json();
  if (!response.ok) {
    const parsed = z
      .object({
        error: z.object({
          message: z.string(),
          fields: z.unknown().optional(),
        }),
      })
      .safeParse(data);
    throw new Error(
      parsed.success
        ? messages(parsed.data.error.fields).join(' ') ||
            parsed.data.error.message
        : 'The service could not complete this request.',
    );
  }
  const parsed = schema.safeParse(data);
  if (!parsed.success)
    throw new Error(
      'The service returned an unexpected response. Please try again.',
    );
  return parsed.data;
}
export const searchPlaces = (query: string, signal: AbortSignal) =>
  request(
    '/geocode?q=' + encodeURIComponent(query),
    z.object({ places: z.array(placeSchema) }),
    signal,
  );
export const createPlan = (body: PlanRequest, signal: AbortSignal) =>
  request('/plans', planSchema, signal, body);
