import type { Corridor } from '../../api/contracts';
import { timestamp } from '../../components/format';

export default function ForecastSlider({
  forecast,
  hour,
  setHour,
  zone,
}: {
  forecast: Corridor;
  hour: number;
  setHour: (hour: number) => void;
  zone: string;
}) {
  const wind = forecast.frames[hour].wind_mph.filter(
    (value): value is number => value !== null,
  );
  return (
    <section
      className="forecast-scrubber"
      aria-label="Corridor forecast timeline"
    >
      <div className="scrubber-label">
        <span className="eyebrow">CORRIDOR FORECAST</span>
        <strong>
          +{hour}h{' '}
          <span>{timestamp(forecast.frames[hour].valid_at, zone)}</span>
        </strong>
      </div>
      <div className="scrubber-track">
        <label className="sr-only" htmlFor="forecast-hour">
          Forecast hour
        </label>
        <input
          id="forecast-hour"
          type="range"
          min="0"
          max="48"
          step="1"
          value={hour}
          aria-valuetext={`Departure plus ${hour} hours, ${timestamp(forecast.frames[hour].valid_at, zone)}`}
          onChange={(event) => setHour(Number(event.target.value))}
        />
        <div className="forecast-ticks">
          {[0, 12, 24, 36, 48].map((value) => (
            <button key={value} onClick={() => setHour(value)}>
              {value === 0 ? 'Departure' : `+${value}h`}
            </button>
          ))}
        </div>
      </div>
      <p>
        Independent of truck ETA risk · Corridor wind{' '}
        {wind.length
          ? `${Math.min(...wind).toFixed(1)}–${Math.max(...wind).toFixed(1)} mph`
          : 'unavailable'}
      </p>
    </section>
  );
}
