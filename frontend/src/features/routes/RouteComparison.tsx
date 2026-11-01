import { memo } from 'react';
import type { Plan } from '../../api/contracts';
import {
  duration,
  miles,
  routeColors,
  timestamp,
} from '../../components/format';
import Icon from '../../components/Icon';

function RouteComparison({
  plan,
  selected,
  onSelect,
}: {
  plan: Plan;
  selected: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <section className="comparison" aria-labelledby="comparison-title">
      <div className="section-heading">
        <span className="eyebrow">02 / COMPARE</span>
        <span className="count-label">{plan.actual_route_count} routes</span>
      </div>
      <h2 id="comparison-title">Your alternatives</h2>
      <p className="section-copy">
        Ranked by weather exposure, then travel time.
      </p>
      <div className="route-list">
        {plan.routes.map((route, index) => {
          const recommended = route.id === plan.recommendation.route_id;
          return (
            <button
              key={route.id}
              className={
                'route-option ' + (selected === route.id ? 'is-selected' : '')
              }
              aria-pressed={selected === route.id}
              onClick={() => onSelect(route.id)}
            >
              <span className="route-top">
                <span className="route-name">
                  <i style={{ background: routeColors[index] }} />
                  {route.label}
                </span>
                <span
                  className={
                    'route-status ' + (recommended ? 'preferred' : route.status)
                  }
                >
                  {recommended
                    ? plan.recommendation.state === 'provisional'
                      ? 'Provisional'
                      : 'Recommended'
                    : route.status === 'no_travel'
                      ? 'No Travel'
                      : route.status === 'incomplete'
                        ? 'Incomplete'
                        : 'Alternative'}
                </span>
              </span>
              <span className="route-main">
                <strong>{duration(route.duration_s)}</strong>
                <span>{miles(route.distance_m)} mi</span>
                <span className="selection-dot" />
              </span>
              <span className="route-arrival">
                Est. arrival{' '}
                {timestamp(route.arrival_at, plan.departure_timezone)}
              </span>
              <span className="route-metrics">
                <span>
                  <b>{miles(route.risk_distance_m.severe)} mi</b>Severe
                </span>
                <span>
                  <b>{miles(route.risk_distance_m.high)} mi</b>High
                </span>
                <span>
                  <b>{Math.round(route.coverage_fraction * 100)}%</b>Coverage
                </span>
                <span>
                  <b>{route.average_risk_index?.toFixed(2) ?? '—'}</b>Avg. risk
                  / 4
                </span>
              </span>
            </button>
          );
        })}
      </div>
      <div
        className={
          'recommendation-note ' +
          (!plan.recommendation.route_id ? 'attention' : '')
        }
      >
        <Icon name={plan.recommendation.route_id ? 'check' : 'wind'} />
        <div>
          <strong>
            {plan.recommendation.state === 'recommended'
              ? 'Best evaluated route'
              : plan.recommendation.state === 'provisional'
                ? 'Best available · provisional'
                : plan.recommendation.state === 'no_safe_route'
                  ? 'No eligible route · No Travel'
                  : 'Weather evaluation incomplete'}
          </strong>
          <p>{plan.recommendation.reasons.join(' ')}</p>
        </div>
      </div>
      {plan.warnings.map((warning, index) => (
        <p className="warning-message" key={index}>
          {warning.message}
        </p>
      ))}
    </section>
  );
}

export default memo(RouteComparison);
