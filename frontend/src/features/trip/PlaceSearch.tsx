import { useEffect, useId, useState } from 'react';
import type { Place } from '../../api/contracts';
import { searchPlaces } from '../../api/client';

export default function PlaceSearch({
  label,
  value,
  onChange,
  mark,
}: {
  label: string;
  value: Place | null;
  onChange: (place: Place | null) => void;
  mark: string;
}) {
  const id = useId();
  const [query, setQuery] = useState(value?.label || '');
  const [places, setPlaces] = useState<Place[]>([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    if (query.length < 3 || value) return () => controller.abort();
    const timer = setTimeout(() => {
      setBusy(true);
      setMessage('');
      void searchPlaces(query, controller.signal)
        .then((data) => {
          if (controller.signal.aborted) return;
          setPlaces(data.places);
          setActive(0);
          setOpen(document.activeElement?.id === id);
          if (!data.places.length)
            setMessage('No matches. Try a city and state.');
        })
        .catch((error: unknown) => {
          if (!controller.signal.aborted)
            setMessage(
              error instanceof Error
                ? error.message
                : 'Location search unavailable.',
            );
        })
        .finally(() => {
          if (!controller.signal.aborted) setBusy(false);
        });
    }, 350);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
  }, [query, value, id]);
  const choose = (place: Place) => {
    onChange(place);
    setQuery(place.label);
    setOpen(false);
    setPlaces([]);
    setMessage('');
  };
  return (
    <div className="place-field">
      <label htmlFor={id}>{label}</label>
      <div className="place-input">
        <span className="place-mark">{mark}</span>
        <input
          id={id}
          required
          value={value?.label || query}
          placeholder={
            label === 'Origin' ? 'City or address' : 'Where are you headed?'
          }
          autoComplete="off"
          role="combobox"
          aria-expanded={open && places.length > 0}
          aria-controls={id + '-options'}
          aria-autocomplete="list"
          aria-activedescendant={
            open && places[active] ? `${id}-${active}` : undefined
          }
          onFocus={() => {
            if (places.length) setOpen(true);
          }}
          onBlur={() => setOpen(false)}
          onChange={(event) => {
            setQuery(event.target.value);
            setMessage('');
            setPlaces([]);
            onChange(null);
            setOpen(false);
            setBusy(false);
          }}
          onKeyDown={(event) => {
            if (event.key === 'Escape') setOpen(false);
            if (!open || !places.length) return;
            if (event.key === 'ArrowDown') {
              event.preventDefault();
              setActive((active + 1) % places.length);
            }
            if (event.key === 'ArrowUp') {
              event.preventDefault();
              setActive((active + places.length - 1) % places.length);
            }
            if (event.key === 'Enter') {
              event.preventDefault();
              choose(places[active]);
            }
          }}
        />
      </div>
      {open && places.length > 0 && (
        <ul
          className="suggestions"
          id={id + '-options'}
          role="listbox"
          aria-label={label + ' results'}
        >
          {places.map((place, index) => (
            <li
              key={place.id}
              role="option"
              id={`${id}-${index}`}
              aria-selected={index === active}
              onMouseDown={(event) => event.preventDefault()}
              onClick={() => choose(place)}
            >
              {place.label}
            </li>
          ))}
        </ul>
      )}
      {busy && !value && <small role="status">Searching places…</small>}
      {message && !value && <small role="status">{message}</small>}
    </div>
  );
}
