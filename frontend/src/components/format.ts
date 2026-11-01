import type { Risk } from '../api/contracts';
export const miles = (meters: number) =>
  (meters / 1609.344).toLocaleString('en-US', { maximumFractionDigits: 1 });
export function duration(seconds: number) {
  const minutes = Math.round(seconds / 60);
  return minutes >= 60
    ? `${Math.floor(minutes / 60)}h ${minutes % 60}m`
    : `${minutes} min`;
}
export const timestamp = (value: string, zone: string) =>
  new Intl.DateTimeFormat('en-US', {
    timeZone: zone,
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(new Date(value));
export const riskLabel = (risk: Risk | null) =>
  risk === null
    ? 'Unknown'
    : risk === 'no_travel'
      ? 'No Travel'
      : risk[0].toUpperCase() + risk.slice(1);
export const riskColors: Record<Risk | 'unknown', string> = {
  low: '#277b67',
  moderate: '#b28a1c',
  high: '#d27331',
  severe: '#c34d4a',
  no_travel: '#742e53',
  unknown: '#82909e',
};
export const routeColors = ['#177e82', '#5a6f9c', '#aa7844'];
