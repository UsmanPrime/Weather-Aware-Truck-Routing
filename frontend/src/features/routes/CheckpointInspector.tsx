import type { Checkpoint, Plan, Route } from '../../api/contracts';
import {
  miles,
  riskColors,
  riskLabel,
  timestamp,
} from '../../components/format';
import Icon from '../../components/Icon';

export function RiskBadge({ risk }: { risk: Checkpoint['risk'] }) {
  return (
    <span
      className="risk-badge"
      style={
        { '--risk-color': riskColors[risk ?? 'unknown'] } as React.CSSProperties
      }
    >
      <i />
      {riskLabel(risk)}
    </span>
  );
}
export default function CheckpointInspector({
  checkpoint,
  route,
  plan,
}: {
  checkpoint: Checkpoint;
  route: Route;
  plan: Plan;
}) {
  const weather = checkpoint.weather;
  const value = (number: number | null, digits: number) =>
    number === null ? 'Unavailable' : number.toFixed(digits);
  return (
    <aside className="checkpoint-inspector" aria-label="Checkpoint weather">
      <div className="section-heading">
        <span className="eyebrow">CHECKPOINT WEATHER</span>
        <Icon name="pin" />
      </div>
      <div className="inspector-heading">
        <h3>Mile {miles(checkpoint.distance_from_start_m)}</h3>
        <RiskBadge risk={checkpoint.risk} />
      </div>
      <p className="inspector-route">
        {route.label} · ETA {timestamp(checkpoint.eta, plan.departure_timezone)}
      </p>
      <div className="weather-readings">
        {(
          [
            [
              'wind',
              'Wind',
              weather.wind_mph,
              1,
              'mph',
              checkpoint.hazards.wind,
            ],
            [
              'rain',
              'Rain',
              weather.rain_in_per_hr,
              2,
              'in/hr',
              checkpoint.hazards.rain,
            ],
            [
              'snow',
              'Snow',
              weather.snow_in_per_hr,
              2,
              'in/hr',
              checkpoint.hazards.snow,
            ],
          ] as const
        ).map(([icon, label, measurement, digits, unit, risk]) => (
          <div key={label}>
            <Icon name={icon} />
            <span>
              {label}
              <small>{riskLabel(risk)}</small>
            </span>
            <strong>
              {value(measurement, digits)}{' '}
              <small>{measurement !== null ? unit : ''}</small>
            </strong>
          </div>
        ))}
      </div>
      {checkpoint.missing_fields.length > 0 && (
        <p className="warning-message">
          Incomplete forecast. Missing values are not treated as Low risk.
        </p>
      )}
      <p className="inspector-foot">
        Wind valid{' '}
        {weather.wind_valid_at
          ? timestamp(weather.wind_valid_at, plan.departure_timezone)
          : 'unavailable'}
        . Rain/snow: preceding hour ending{' '}
        {weather.precipitation_interval_end
          ? timestamp(
              weather.precipitation_interval_end,
              plan.departure_timezone,
            )
          : 'unavailable'}
        .
      </p>
      <p className="source-note">
        Open-Meteo model forecast
        {weather.retrieved_at
          ? ` · retrieved ${timestamp(weather.retrieved_at, plan.departure_timezone)}`
          : ''}
      </p>
    </aside>
  );
}

export function CheckpointList({
  route,
  plan,
  active,
  onSelect,
}: {
  route: Route;
  plan: Plan;
  active: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="checkpoint-section" aria-labelledby="checkpoints-title">
      <div className="checkpoint-title">
        <div>
          <span className="eyebrow">03 / ALONG THE ROUTE</span>
          <h2 id="checkpoints-title">Weather at your estimated arrival</h2>
        </div>
        <span>
          {route.checkpoints.length} checkpoints · every{' '}
          {plan.checkpoint_interval_mi} mi
        </span>
      </div>
      <div className="checkpoint-list">
        {route.checkpoints.map((cp, index) => (
          <button
            key={cp.id}
            onClick={() => onSelect(cp.id)}
            aria-pressed={active === cp.id}
            className={active === cp.id ? 'active' : ''}
          >
            <span className="checkpoint-index">
              {String(index + 1).padStart(2, '0')}
            </span>
            <span>
              <strong>
                {index === 0
                  ? 'Origin'
                  : index === route.checkpoints.length - 1
                    ? 'Destination'
                    : `Mile ${miles(cp.distance_from_start_m)}`}
              </strong>
              <small>{timestamp(cp.eta, plan.departure_timezone)}</small>
            </span>
            <RiskBadge risk={cp.risk} />
          </button>
        ))}
      </div>
      <p className="method-note">
        {route.timing_notes.join(' ')} Exposure estimates conservatively assign
        each road interval the higher risk of its two checkpoints.
      </p>
      {route.provider_notices.map((notice, i) => (
        <p key={i} className="warning-message">
          Provider notice: {notice.message || notice.code}
        </p>
      ))}
    </section>
  );
}
