function parts(instant: Date, zone: string) {
  const formatted = new Intl.DateTimeFormat('en-CA', {
    timeZone: zone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(instant);
  const read = (key: string) =>
    formatted.find((part) => part.type === key)!.value;
  return {
    date: `${read('year')}-${read('month')}-${read('day')}`,
    time: `${read('hour')}:${read('minute')}`,
  };
}
export const localFields = (instant: Date, zone: string) =>
  parts(instant, zone);
export function wallTimeToInstant(
  date: string,
  time: string,
  zone: string,
): string {
  const target = Date.parse(`${date}T${time}:00Z`);
  if (!Number.isFinite(target))
    throw new Error('Enter a valid departure date and time.');
  const offsets = new Set<number>();
  for (const delta of [-36, 0, 36]) {
    const stamp = target + delta * 3600000;
    const local = parts(new Date(stamp), zone);
    offsets.add(Date.parse(`${local.date}T${local.time}:00Z`) - stamp);
  }
  const candidates = [...offsets]
    .map((offset) => target - offset)
    .filter((stamp) => {
      const local = parts(new Date(stamp), zone);
      return local.date === date && local.time === time;
    });
  if (!candidates.length)
    throw new Error(
      'This local time does not exist due to daylight saving. Choose another time.',
    );
  if (candidates.length > 1)
    throw new Error(
      'This local time occurs twice due to daylight saving. Choose another time or use UTC.',
    );
  return new Date(candidates[0]).toISOString();
}
