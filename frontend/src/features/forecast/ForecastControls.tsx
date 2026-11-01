import type { Corridor, WeatherMetric } from '../../api/contracts';
import { riskColors, timestamp } from '../../components/format';
import Icon from '../../components/Icon';

export default function ForecastControls({
  forecast,
  loading,
  error,
  hour,
  metric,
  setMetric,
  visible,
  setVisible,
  zone,
  retry,
}: {
  forecast: Corridor | null;
  loading: boolean;
  error: string;
  hour: number;
  metric: WeatherMetric;
  setMetric: (metric: WeatherMetric) => void;
  visible: boolean;
  setVisible: (visible: boolean) => void;
  zone: string;
  retry: () => void;
}) {
  const frame = forecast?.frames[hour];
  const windTimes = [
    ...new Set(frame?.wind_valid_at.filter((at) => at !== null)),
  ];
  const precipitationTimes = [
    ...new Set(frame?.precipitation_interval_end.filter((at) => at !== null)),
  ];
  const timeLabel = (times: string[]) =>
    times.length === 1
      ? timestamp(times[0], zone)
      : times.length
        ? 'varies by cell'
        : 'unavailable';
  const legends = {
    risk: ['Low', 'Moderate', 'High', 'Severe', 'No Travel'],
    wind_mph: ['<25', '25–<35', '35–<45', '45–<55', '≥55 mph'],
    rain_in_per_hr: ['<0.10', '0.10–<0.25', '0.25–<0.50', '0.50–1', '>1 in/hr'],
    snow_in_per_hr: ['<0.5', '0.5–<1', '1–<2', '2–3', '>3 in/hr'],
  };
  return (
    <section className="forecast-controls" aria-labelledby="forecast-title">
      <div className="forecast-heading">
        <div>
          <span className="eyebrow">48-HOUR CORRIDOR OUTLOOK</span>
          <h2 id="forecast-title">Weather beyond the next turn</h2>
        </div>
        <Icon name="layers" />
      </div>
      <p className="section-copy">
        A sampled forecast across all route corridors. Checkpoint risk above
        follows truck arrival times; this slider is independent.
      </p>
      {loading && (
        <p className="loading-message" role="status">
          Loading real corridor forecasts…
        </p>
      )}
      {error && (
        <p className="error-message" role="alert">
          {error}{' '}
          <button className="text-button" onClick={retry}>
            Retry forecast
          </button>
        </p>
      )}
      {forecast && frame && (
        <>
          <div className="forecast-toolbar">
            <label className="layer-toggle">
              <input
                type="checkbox"
                checked={visible}
                onChange={(e) => setVisible(e.target.checked)}
              />
              Show corridor weather
            </label>
            <div>
              <label htmlFor="weather-metric">Map layer</label>
              <select
                id="weather-metric"
                value={metric}
                onChange={(e) => setMetric(e.target.value as WeatherMetric)}
              >
                <option value="risk">Combined weather risk</option>
                <option value="wind_mph">Wind · mph</option>
                <option value="rain_in_per_hr">Rain · in/hr</option>
                <option value="snow_in_per_hr">Snow · in/hr</option>
              </select>
            </div>
          </div>
          <div className="forecast-time">
            <span className="forecast-offset">
              +{hour}
              <small>hours</small>
            </span>
            <div>
              <strong data-testid="forecast-time">
                {timestamp(frame.valid_at, zone)}
              </strong>
              <span>
                Selected forecast time ·{' '}
                {Math.round(frame.coverage_fraction * 100)}% weather coverage
              </span>
            </div>
            <span className="forecast-resolution">
              {forecast.cells.length} model samples
              <br />
              {Math.round(forecast.grid_spacing_m / 1000)} km grid
            </span>
          </div>
          <div className="forecast-legend" aria-label="Corridor weather legend">
            {legends[metric].map((label, index) => (
              <span key={label}>
                <i style={{ background: Object.values(riskColors)[index] }} />
                {label}
              </span>
            ))}
            <span>
              <i className="unknown-swatch" />
              Unavailable
            </span>
          </div>
          <p className="forecast-validity">
            Wind valid {timeLabel(windTimes)}. Rain/snow: preceding hour ending{' '}
            {timeLabel(precipitationTimes)}.
          </p>
          <p className="source-note">
            Open-Meteo model forecasts · oldest retrieval{' '}
            {forecast.oldest_retrieved_at
              ? timestamp(forecast.oldest_retrieved_at, zone)
              : 'unavailable'}
            . Cells show sampled values, without blending across missing data.
            Corridor extends approximately{' '}
            {forecast.corridor_half_width_m / 1000} km either side of routes;
            edge cells extend by half a grid spacing.
          </p>
          {frame.coverage_fraction < 1 && (
            <p className="warning-message">
              Some cells are unavailable at this time. Unknown cells remain
              gray; your ETA-based route recommendation is unchanged.
            </p>
          )}
        </>
      )}
    </section>
  );
}
