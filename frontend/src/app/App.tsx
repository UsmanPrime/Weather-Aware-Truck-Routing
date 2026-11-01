import { lazy, Suspense, useEffect, useRef, useState } from 'react';
import { fetchHealth } from '../api/health';
import { createPlan, loadCorridor } from '../api/client';
import type {
  Plan,
  PlanRequest,
  Corridor,
  WeatherMetric,
} from '../api/contracts';
import ForecastControls from '../features/forecast/ForecastControls';
import Icon from '../components/Icon';
import { riskColors, riskLabel, timestamp } from '../components/format';
import TripForm from '../features/trip/TripForm';
import RouteComparison from '../features/routes/RouteComparison';
import CheckpointInspector, {
  CheckpointList,
} from '../features/routes/CheckpointInspector';

const RouteMap = lazy(() => import('../features/map/RouteMap'));

export default function App() {
  const [status, setStatus] = useState('Connecting');
  const [plan, setPlan] = useState<Plan | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [checkpoint, setCheckpoint] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [dirty, setDirty] = useState(false);
  const [forecast, setForecast] = useState<Corridor | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [forecastError, setForecastError] = useState('');
  const [hour, setHour] = useState(0);
  const [metric, setMetric] = useState<WeatherMetric>('risk');
  const [weatherVisible, setWeatherVisible] = useState(true);
  const forecastController = useRef<AbortController | null>(null);
  const revision = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const resultHeading = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    void fetchHealth(controller.signal).then(
      () => setStatus('API online'),
      () => {
        if (!controller.signal.aborted) setStatus('API unavailable');
      },
    );
    return () => controller.abort();
  }, []);
  useEffect(
    () => () => {
      controller.current?.abort();
      forecastController.current?.abort();
    },
    [],
  );
  const route =
    plan?.routes.find((route) => route.id === selected) || plan?.routes[0];
  const active =
    route?.checkpoints.find((cp) => cp.id === checkpoint) ||
    route?.checkpoints[0];
  const selectRoute = (id: string) => {
    setSelected(id);
    setCheckpoint(null);
  };
  const fetchForecast = async (result: Plan) => {
    forecastController.current?.abort();
    const next = new AbortController();
    forecastController.current = next;
    setForecastError('');
    if (!result.corridor_context) {
      setForecastLoading(false);
      setForecastError('Corridor forecast is unavailable for this plan.');
      return;
    }
    setForecastLoading(true);
    try {
      const data = await loadCorridor(result.corridor_context, next.signal);
      if (!next.signal.aborted) setForecast(data);
    } catch (error) {
      if (!next.signal.aborted)
        setForecastError(
          error instanceof Error
            ? error.message
            : 'Corridor forecast is unavailable.',
        );
    } finally {
      if (!next.signal.aborted) setForecastLoading(false);
    }
  };
  const generate = async (request: PlanRequest) => {
    const submittedRevision = revision.current;
    controller.current?.abort();
    const requestController = new AbortController();
    controller.current = requestController;
    setLoading(true);
    setError('');
    try {
      const result = await createPlan(request, requestController.signal);
      if (requestController.signal.aborted) return;
      setPlan(result);
      setSelected(result.recommendation.route_id || result.routes[0].id);
      setCheckpoint(null);
      setDirty(revision.current !== submittedRevision);
      setForecast(null);
      setHour(0);
      void fetchForecast(result);
      if (window.innerWidth < 800)
        resultHeading.current?.scrollIntoView({
          behavior: matchMedia('(prefers-reduced-motion: reduce)').matches
            ? 'instant'
            : 'smooth',
        });
    } catch (error) {
      if (!requestController.signal.aborted)
        setError(
          error instanceof Error
            ? error.message
            : 'The journey could not be calculated.',
        );
    } finally {
      if (!requestController.signal.aborted) setLoading(false);
    }
  };
  return (
    <>
      <header className="app-header">
        <a className="brand" href="#main">
          <span className="brand-mark">
            <Icon name="route" size={25} />
          </span>
          <span>
            Routecast<small>WEATHER-AWARE TRUCK ROUTING</small>
          </span>
        </a>
        <span className="header-description">
          A clearer view of the road ahead.
        </span>
        <div className="api-status">
          <i className={status === 'API online' ? 'online' : ''} />
          {status}
        </div>
      </header>
      <main id="main" className="workspace">
        <aside className="sidebar">
          <TripForm
            onGenerate={(data) => void generate(data)}
            loading={loading}
            onEdit={() => {
              revision.current += 1;
              if (plan) setDirty(true);
            }}
          />
          <details className="methodology">
            <summary>
              <Icon name="layers" />
              How the recommendation works
            </summary>
            <p>
              Eligible routes are compared in this order: fewest Severe miles,
              fewest High miles, lowest distance-weighted risk, then shortest
              estimated time. No Travel routes are excluded; missing weather
              prevents a definitive evaluation.
            </p>
            <p>
              Risk indices: Low 0, Moderate 1, High 2, Severe 3, No Travel 4.
              This is an ordinal index, not a probability.
            </p>
            <table>
              <caption>Checkpoint weather thresholds</caption>
              <thead>
                <tr>
                  <th>Risk</th>
                  <th>Wind mph</th>
                  <th>Rain in/hr</th>
                  <th>Snow in/hr</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>Low</td>
                  <td>&lt;25</td>
                  <td>&lt;0.10</td>
                  <td>&lt;0.5</td>
                </tr>
                <tr>
                  <td>Moderate</td>
                  <td>25–&lt;35</td>
                  <td>0.10–&lt;0.25</td>
                  <td>0.5–&lt;1</td>
                </tr>
                <tr>
                  <td>High</td>
                  <td>35–&lt;45</td>
                  <td>0.25–&lt;0.50</td>
                  <td>1–&lt;2</td>
                </tr>
                <tr>
                  <td>Severe</td>
                  <td>45–&lt;55</td>
                  <td>0.50–1</td>
                  <td>2–3</td>
                </tr>
                <tr>
                  <td>No Travel</td>
                  <td>≥55</td>
                  <td>&gt;1</td>
                  <td>&gt;3</td>
                </tr>
              </tbody>
            </table>
            <p>
              Wind 45–&lt;55 mph with cargo &gt;30,000 lb: No Travel. Wind
              35–&lt;45 mph with cargo &gt;40,000 lb: Severe. Shared rain/snow
              boundaries use the higher class; exactly 1 in/hr rain and 3 in/hr
              snow remain Severe.
            </p>
          </details>
          <p className="assessment-note">
            Assessment prototype. Forecasts and travel times are estimates, not
            certified dispatch or severe-weather guidance.
          </p>
        </aside>
        <div className="main-content">
          <div className="journey-bar" ref={resultHeading}>
            <div>
              <span className="eyebrow">
                {plan ? 'JOURNEY OVERVIEW' : 'ROUTE PLANNER'}
              </span>
              <h1>
                {plan ? (
                  <>
                    {plan.origin.label.split(',')[0]}{' '}
                    <span className="journey-arrow">→</span>{' '}
                    {plan.destination.label.split(',')[0]}
                  </>
                ) : (
                  'Every mile. Better informed.'
                )}
              </h1>
            </div>
            <div className="journey-meta">
              {plan ? (
                <>
                  <Icon name="clock" />
                  <span>
                    Depart{' '}
                    {timestamp(plan.departure_at, plan.departure_timezone)}
                    <small>
                      {plan.load_lb.toLocaleString()} lb cargo ·{' '}
                      {plan.checkpoint_interval_mi} mi sampling
                    </small>
                  </span>
                </>
              ) : (
                <span>Truck routes · ETA-based forecasts</span>
              )}
            </div>
          </div>
          {dirty && (
            <p className="stale-notice" role="status">
              Inputs changed. The map and comparison still show your previous
              plan. Generate routes to apply changes.
            </p>
          )}
          {error && (
            <p className="error-message api-error" role="alert">
              {error}
            </p>
          )}
          {loading && (
            <p className="loading-message" role="status">
              Finding truck routes and matching forecasts to checkpoint
              arrivals…
            </p>
          )}
          <Suspense
            fallback={
              <div className="map-loading" role="status">
                Loading map…
              </div>
            }
          >
            <RouteMap
              plan={plan}
              forecast={forecast}
              forecastHour={hour}
              metric={metric}
              weatherVisible={weatherVisible}
              selectedRoute={route?.id || null}
              activeCheckpoint={active?.id || null}
              onRoute={selectRoute}
              onCheckpoint={(routeId, id) => {
                setSelected(routeId);
                setCheckpoint(id);
              }}
            >
              {plan && route && active && (
                <CheckpointInspector
                  checkpoint={active}
                  route={route}
                  plan={plan}
                />
              )}
              <div className="risk-legend" aria-label="Checkpoint risk legend">
                <span>CHECKPOINT RISK</span>
                {Object.entries(riskColors).map(([name, color]) => (
                  <span key={name}>
                    <i style={{ background: color }} />
                    {riskLabel(
                      name === 'unknown'
                        ? null
                        : (name as keyof Omit<typeof riskColors, 'unknown'>),
                    )}
                  </span>
                ))}
              </div>
            </RouteMap>
          </Suspense>
          {plan && route && active && (
            <div className="mobile-inspector">
              <CheckpointInspector
                checkpoint={active}
                route={route}
                plan={plan}
              />
            </div>
          )}
          {plan && (
            <ForecastControls
              forecast={forecast}
              loading={forecastLoading}
              error={forecastError}
              hour={hour}
              setHour={setHour}
              metric={metric}
              setMetric={setMetric}
              visible={weatherVisible}
              setVisible={setWeatherVisible}
              zone={plan.departure_timezone}
              retry={() => void fetchForecast(plan)}
            />
          )}
          {plan && (
            <RouteComparison
              plan={plan}
              selected={route?.id || null}
              onSelect={selectRoute}
            />
          )}
          {plan && route && (
            <CheckpointList
              route={route}
              plan={plan}
              active={active?.id || null}
              onSelect={setCheckpoint}
            />
          )}
          <footer className="app-footer">
            <span>
              Forecasts:{' '}
              <a
                href="https://open-meteo.com/"
                target="_blank"
                rel="noreferrer"
              >
                Open-Meteo
              </a>{' '}
              ·{' '}
              <a
                href="https://openrouteservice.org/"
                target="_blank"
                rel="noreferrer"
              >
                © openrouteservice.org by HeiGIT
              </a>
            </span>
            <span>
              Map data © OpenStreetMap contributors · Forecast estimates
            </span>
          </footer>
        </div>
      </main>
    </>
  );
}
