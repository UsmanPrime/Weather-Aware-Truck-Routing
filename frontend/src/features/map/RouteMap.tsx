import { useEffect, useRef, useState } from 'react';
import type {
  GeoJSONSource,
  Map as MapLibreMap,
  Marker,
  Popup,
} from 'maplibre-gl';
import type { Plan, Corridor, WeatherMetric } from '../../api/contracts';
import { forecastFeatures } from '../forecast/forecastFeatures';
import { timestamp } from '../../components/format';
import { routeFeatures, checkpointFeatures } from './mapSources';
import Icon from '../../components/Icon';
import { loadMapEngine } from './loadMap';

export default function RouteMap({
  plan,
  selectedRoute,
  activeCheckpoint,
  onRoute,
  onCheckpoint,
  children,
  forecast,
  forecastHour,
  metric,
  weatherVisible,
}: {
  plan: Plan | null;
  selectedRoute: string | null;
  activeCheckpoint: string | null;
  onRoute: (id: string) => void;
  onCheckpoint: (routeId: string, id: string) => void;
  children?: React.ReactNode;
  forecast: Corridor | null;
  forecastHour: number;
  metric: WeatherMetric;
  weatherVisible: boolean;
}) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<MapLibreMap | null>(null);
  const markers = useRef<Marker[]>([]);
  const popup = useRef<Popup | null>(null);
  const current = useRef({ plan, onRoute, onCheckpoint });
  useEffect(() => {
    current.current = { plan, onRoute, onCheckpoint };
  });
  const [ready, setReady] = useState(false);
  const [notice, setNotice] = useState('');
  const fit = () => {
    const coordinates = current.current.plan?.routes.flatMap(
      (route) => route.geometry.coordinates,
    );
    if (!map.current || !coordinates?.length) return;
    const longs = coordinates.map((p) => p[0]),
      lats = coordinates.map((p) => p[1]);
    map.current.fitBounds(
      [
        [Math.min(...longs), Math.min(...lats)],
        [Math.max(...longs), Math.max(...lats)],
      ],
      {
        padding: {
          top: 75,
          bottom: 115,
          left: 55,
          right: window.innerWidth > 1100 ? 310 : 55,
        },
        duration: matchMedia('(prefers-reduced-motion: reduce)').matches
          ? 0
          : 600,
      },
    );
  };
  useEffect(() => {
    let cancelled = false;
    void loadMapEngine()
      .then((library) => {
        if (cancelled || !container.current) return;
        const instance = new library.Map({
          container: container.current,
          style: 'https://tiles.openfreemap.org/styles/positron',
          center: [-97.07, 32.78],
          zoom: 8.8,
          attributionControl: { compact: true },
        });
        map.current = instance;
        // Development-only handle lets browser tests inspect actual MapLibre sources/layers.
        if (import.meta.env.DEV)
          Object.assign(container.current, { mapInstance: instance });
        instance.addControl(
          new library.NavigationControl({ showCompass: false }),
          'top-left',
        );
        instance.on('error', () =>
          setNotice(
            'Some map tiles could not load. Journey details remain available below.',
          ),
        );
        instance.on('load', () => {
          if (cancelled) return;
          for (const id of ['truck-routes', 'checkpoints', 'corridor-cells'])
            instance.addSource(id, {
              type: 'geojson',
              data: { type: 'FeatureCollection', features: [] },
            });
          instance.addLayer({
            id: 'corridor-fill',
            type: 'fill',
            source: 'corridor-cells',
            paint: { 'fill-color': ['get', 'color'], 'fill-opacity': 0.23 },
          });
          instance.addLayer({
            id: 'corridor-grid',
            type: 'line',
            source: 'corridor-cells',
            paint: {
              'line-color': '#6f9596',
              'line-width': 0.5,
              'line-opacity': 0.28,
            },
          });
          instance.addLayer({
            id: 'corridor-unknown',
            type: 'line',
            source: 'corridor-cells',
            filter: ['==', ['get', 'missing'], true],
            paint: {
              'line-color': '#6c7b88',
              'line-width': 1,
              'line-dasharray': [2, 2],
            },
          });
          popup.current = new library.Popup({
            closeButton: false,
            closeOnClick: false,
            maxWidth: '240px',
            className: 'weather-popup',
          });
          instance.on('mousemove', 'corridor-fill', (event) => {
            const props = event.features?.[0]?.properties;
            if (!props || !popup.current) return;
            const node = document.createElement('div');
            const format = (value: unknown, units: string) =>
              value === null || value === undefined
                ? 'Unavailable'
                : `${Number(value).toFixed(2)} ${units}`;
            node.textContent = `Corridor forecast · ${timestamp(String(props.valid_at), current.current.plan?.departure_timezone || 'UTC')}\nWind ${format(props.wind_mph, 'mph')} · Rain ${format(props.rain_in_per_hr, 'in/hr')} · Snow ${format(props.snow_in_per_hr, 'in/hr')}\n${props.missing ? 'This cell has missing data.' : 'Open-Meteo sampled model forecast.'}`;
            popup.current
              .setLngLat(event.lngLat)
              .setDOMContent(node)
              .addTo(instance);
          });
          instance.on('mouseleave', 'corridor-fill', () =>
            popup.current?.remove(),
          );
          instance.addLayer({
            id: 'route-outline',
            type: 'line',
            source: 'truck-routes',
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: {
              'line-color': '#fff',
              'line-width': ['case', ['get', 'selected'], 10, 6],
              'line-opacity': 0.9,
            },
          });
          instance.addLayer({
            id: 'route-lines',
            type: 'line',
            source: 'truck-routes',
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: {
              'line-color': ['get', 'color'],
              'line-width': ['case', ['get', 'selected'], 6, 3],
              'line-opacity': ['case', ['get', 'selected'], 1, 0.65],
            },
          });
          instance.addLayer({
            id: 'selected-route-outline',
            type: 'line',
            source: 'truck-routes',
            filter: ['==', ['get', 'selected'], true],
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: { 'line-color': '#fff', 'line-width': 10 },
          });
          instance.addLayer({
            id: 'selected-route',
            type: 'line',
            source: 'truck-routes',
            filter: ['==', ['get', 'selected'], true],
            layout: { 'line-join': 'round', 'line-cap': 'round' },
            paint: { 'line-color': ['get', 'color'], 'line-width': 6 },
          });
          instance.addLayer({
            id: 'checkpoint-points',
            type: 'circle',
            source: 'checkpoints',
            filter: ['==', ['get', 'selected'], true],
            paint: {
              'circle-radius': ['case', ['get', 'active'], 9, 6],
              'circle-color': ['get', 'color'],
              'circle-stroke-width': 2.5,
              'circle-stroke-color': '#fff',
            },
          });
          instance.on('click', 'route-lines', (event) => {
            const id = event.features?.[0]?.properties?.route_id;
            if (typeof id === 'string') current.current.onRoute(id);
          });
          instance.on('click', 'checkpoint-points', (event) => {
            const props = event.features?.[0]?.properties;
            if (props)
              current.current.onCheckpoint(
                String(props.route_id),
                String(props.checkpoint_id),
              );
          });
          instance.on('mouseenter', 'checkpoint-points', (event) => {
            instance.getCanvas().style.cursor = 'pointer';
            const props = event.features?.[0]?.properties;
            if (props)
              current.current.onCheckpoint(
                String(props.route_id),
                String(props.checkpoint_id),
              );
          });
          instance.on('mouseleave', 'checkpoint-points', () => {
            instance.getCanvas().style.cursor = '';
          });
          instance.on('mouseenter', 'route-lines', () => {
            instance.getCanvas().style.cursor = 'pointer';
          });
          instance.on('mouseleave', 'route-lines', () => {
            instance.getCanvas().style.cursor = '';
          });
          setReady(true);
        });
      })
      .catch(() => {
        if (!cancelled)
          setNotice(
            'The interactive map is unavailable. Use the route and checkpoint lists.',
          );
      });
    return () => {
      cancelled = true;
      markers.current.forEach((marker) => marker.remove());
      markers.current = [];
      popup.current?.remove();
      map.current?.remove();
      map.current = null;
    };
  }, []);
  useEffect(() => {
    if (!ready || !map.current) return;
    (map.current.getSource('truck-routes') as GeoJSONSource).setData(
      routeFeatures(plan, selectedRoute),
    );
    (map.current.getSource('checkpoints') as GeoJSONSource).setData(
      checkpointFeatures(plan, selectedRoute, activeCheckpoint),
    );
  }, [plan, selectedRoute, activeCheckpoint, ready]);
  useEffect(() => {
    if (!ready || !map.current) return;
    const handle = requestAnimationFrame(() => {
      if (!map.current) return;
      (map.current.getSource('corridor-cells') as GeoJSONSource).setData(
        forecastFeatures(forecast, forecastHour, metric),
      );
      for (const id of ['corridor-fill', 'corridor-grid', 'corridor-unknown'])
        map.current.setLayoutProperty(
          id,
          'visibility',
          weatherVisible ? 'visible' : 'none',
        );
      popup.current?.remove();
    });
    return () => cancelAnimationFrame(handle);
  }, [forecast, forecastHour, metric, weatherVisible, ready]);
  useEffect(() => {
    if (!ready || !plan || !map.current) return;
    fit();
    let cancelled = false;
    markers.current.forEach((marker) => marker.remove());
    markers.current = [];
    void loadMapEngine().then((library) => {
      if (cancelled || !map.current) return;
      const geometry = plan.routes[0].geometry.coordinates;
      for (const [index, point] of [
        geometry[0],
        geometry[geometry.length - 1],
      ].entries()) {
        const element = document.createElement('div');
        element.className = 'endpoint-marker';
        element.textContent = index ? 'B' : 'A';
        element.setAttribute('aria-label', index ? 'Destination' : 'Origin');
        markers.current.push(
          new library.Marker({ element }).setLngLat(point).addTo(map.current),
        );
      }
    });
    return () => {
      cancelled = true;
    };
    // A new request fits once. Ordinary selection and slider changes keep the camera.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [plan?.request_id, ready]);
  return (
    <div className="map-shell" data-selected-route={selectedRoute || ''}>
      <div
        ref={container}
        className="map-canvas"
        data-testid="route-map"
        role="region"
        aria-label="Interactive route map"
      />
      <button className="fit-button" onClick={fit} disabled={!plan || !ready}>
        <Icon name="focus" />
        Fit routes
      </button>
      {!plan && (
        <div className="map-empty">
          <span className="eyebrow">A CLEARER VIEW OF THE ROAD</span>
          <h2>
            Weather insights,
            <br />
            mile by mile.
          </h2>
          <p>
            Enter your journey to compare truck routes and inspect the forecast
            at arrival.
          </p>
        </div>
      )}
      {notice && (
        <p className="map-notice" role="status">
          {notice}
        </p>
      )}
      <div className="map-attribution">
        Routing © openrouteservice.org by HeiGIT · Map data © OpenStreetMap
        contributors
      </div>
      {children}
    </div>
  );
}
