import { useState } from 'react';
import type { Place, PlanRequest } from '../../api/contracts';
import Icon from '../../components/Icon';
import PlaceSearch from './PlaceSearch';
import { localFields, wallTimeToInstant } from './time';

export default function TripForm({
  onGenerate,
  loading,
  onEdit,
}: {
  onGenerate: (request: PlanRequest) => void;
  loading: boolean;
  onEdit: () => void;
}) {
  const browserZone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const [zone, setZone] = useState(browserZone);
  const [initial] = useState(() =>
    localFields(new Date(Date.now() + 3600000), browserZone),
  );
  const [date, setDate] = useState(initial.date);
  const [time, setTime] = useState(initial.time);
  const [origin, setOrigin] = useState<Place | null>(null);
  const [destination, setDestination] = useState<Place | null>(null);
  const [load, setLoad] = useState('30000');
  const [interval, setInterval] = useState<10 | 25 | 50>(25);
  const [error, setError] = useState('');
  const zones = [
    ...new Set([
      browserZone,
      'America/New_York',
      'America/Chicago',
      'America/Denver',
      'America/Los_Angeles',
      'UTC',
    ]),
  ];
  const example = () => {
    setOrigin({
      id: 'example-ftw',
      label: 'Fort Worth, Texas',
      position: [-97.3308, 32.7555],
    });
    setDestination({
      id: 'example-dallas',
      label: 'Dallas, Texas',
      position: [-96.797, 32.7767],
    });
    setZone('America/Chicago');
    const fields = localFields(
      new Date(Date.now() + 3600000),
      'America/Chicago',
    );
    setDate(fields.date);
    setTime(fields.time);
    setError('');
    onEdit();
  };
  return (
    <form
      className="trip-form"
      onSubmit={(event) => {
        event.preventDefault();
        setError('');
        try {
          if (!origin || !destination)
            throw new Error(
              'Select both locations from the search results, or use the example journey.',
            );
          const departure_at = wallTimeToInstant(date, time, zone);
          if (Date.parse(departure_at) < Date.now() - 60000)
            throw new Error('Choose a departure time in the future.');
          if (Date.parse(departure_at) > Date.now() + 6 * 86400000)
            throw new Error('Choose a departure within the next six days.');
          if (
            !load.trim() ||
            !Number.isFinite(Number(load)) ||
            Number(load) < 0 ||
            Number(load) > 200000
          )
            throw new Error('Enter a cargo weight between 0 and 200,000 lb.');
          onGenerate({
            origin,
            destination,
            departure_at,
            departure_timezone: zone,
            load_lb: Number(load),
            checkpoint_interval_mi: interval,
          });
        } catch (error) {
          setError(
            error instanceof Error
              ? error.message
              : 'Check your journey details.',
          );
        }
      }}
    >
      <div className="section-heading">
        <span className="eyebrow">01 / JOURNEY</span>
        <Icon name="route" />
      </div>
      <h2>Plan your route</h2>
      <p className="section-copy">
        Compare truck routes with the weather ahead.
      </p>
      <div className="location-fields">
        <PlaceSearch
          label="Origin"
          mark="A"
          value={origin}
          onChange={(value) => {
            setOrigin(value);
            onEdit();
          }}
        />
        <PlaceSearch
          label="Destination"
          mark="B"
          value={destination}
          onChange={(value) => {
            setDestination(value);
            onEdit();
          }}
        />
      </div>
      <button type="button" className="example-button" onClick={example}>
        Try Fort Worth → Dallas <span>↗</span>
      </button>
      <div className="form-divider" />
      <div className="field-pair">
        <div>
          <label htmlFor="departure-date">Departure date</label>
          <input
            id="departure-date"
            type="date"
            required
            value={date}
            onChange={(e) => {
              setDate(e.target.value);
              onEdit();
            }}
          />
        </div>
        <div>
          <label htmlFor="departure-time">Time</label>
          <input
            id="departure-time"
            type="time"
            required
            value={time}
            onChange={(e) => {
              setTime(e.target.value);
              onEdit();
            }}
          />
        </div>
      </div>
      <label htmlFor="departure-zone">Departure timezone</label>
      <select
        id="departure-zone"
        value={zone}
        onChange={(e) => {
          setZone(e.target.value);
          onEdit();
        }}
      >
        {zones.map((zone) => (
          <option key={zone} value={zone}>
            {zone.replaceAll('_', ' ')}
            {zone === browserZone ? ' · device zone' : ''}
          </option>
        ))}
      </select>
      <div className="field-pair cargo-row">
        <div>
          <label htmlFor="load">
            Cargo weight <span>lb</span>
          </label>
          <input
            id="load"
            type="number"
            min="0"
            max="200000"
            step="any"
            required
            value={load}
            onChange={(e) => {
              setLoad(e.target.value);
              onEdit();
            }}
          />
        </div>
        <div>
          <label htmlFor="interval">Weather sampling</label>
          <select
            id="interval"
            value={interval}
            onChange={(e) => {
              setInterval(Number(e.target.value) as 10 | 25 | 50);
              onEdit();
            }}
          >
            <option value="10">Every 10 mi</option>
            <option value="25">Every 25 mi</option>
            <option value="50">Every 50 mi</option>
          </select>
        </div>
      </div>
      <p className="field-note">
        Cargo weight adjusts wind risk. It is not vehicle gross weight.
      </p>
      {error && (
        <p className="error-message" role="alert">
          {error}
        </p>
      )}
      <button className="primary-button" type="submit" disabled={loading}>
        {loading ? 'Calculating routes…' : 'Generate routes'}
        <Icon name="arrow" />
      </button>
      <p className="provider-note">
        Free truck alternatives up to 100 km. Longer trips may return one truck
        route.
      </p>
    </form>
  );
}
