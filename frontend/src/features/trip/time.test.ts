import { describe, expect, it } from 'vitest';
import { localFields, wallTimeToInstant } from './time';

describe('explicit timezone conversion', () => {
  it.each([
    ['2026-11-02', '12:30', 'America/Chicago', '2026-11-02T18:30:00.000Z'],
    ['2026-11-02', '12:30', 'Asia/Karachi', '2026-11-02T07:30:00.000Z'],
    ['2026-11-02', '00:00', 'UTC', '2026-11-02T00:00:00.000Z'],
    ['2026-11-01', '02:30', 'America/New_York', '2026-11-01T07:30:00.000Z'],
  ])('converts %s %s in %s', (date, time, zone, expected) => {
    expect(wallTimeToInstant(date, time, zone)).toBe(expected);
  });
  it('rejects nonexistent spring-forward wall time', () => {
    expect(() =>
      wallTimeToInstant('2026-03-08', '02:30', 'America/New_York'),
    ).toThrow('does not exist');
  });
  it('rejects ambiguous fall-back wall time', () => {
    expect(() =>
      wallTimeToInstant('2026-11-01', '01:30', 'America/New_York'),
    ).toThrow('occurs twice');
  });
  it('formats local date across midnight without losing the day', () => {
    expect(
      localFields(new Date('2026-11-02T02:00Z'), 'America/Chicago'),
    ).toEqual({ date: '2026-11-01', time: '20:00' });
  });
});
