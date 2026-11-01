import { useEffect, useState } from 'react';
import { fetchHealth } from '../api/health';

export default function App() {
  const [status, setStatus] = useState('Checking backend…');
  useEffect(() => {
    const controller = new AbortController();
    void fetchHealth(controller.signal).then(
      () => setStatus('Backend connected'),
      () => {
        if (!controller.signal.aborted)
          setStatus('Backend unavailable. Start Django and refresh.');
      },
    );
    return () => controller.abort();
  }, []);
  return (
    <main className="mx-auto max-w-4xl px-6 py-16 sm:py-24">
      <p className="mb-6 text-sm font-semibold uppercase tracking-widest text-emerald-800">
        Weather-aware truck routing
      </p>
      <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-6xl">
        Better information for the road ahead.
      </h1>
      <p className="mt-6 max-w-xl text-lg leading-relaxed text-slate-600">
        The application foundation is ready. Route planning, checkpoint
        forecasts and the corridor map are the next milestone.
      </p>
      <div className="mt-10 rounded-2xl border border-emerald-900/15 bg-white p-6 shadow-sm">
        <p className="text-sm font-semibold text-slate-600">Service status</p>
        <p className="mt-2 font-medium" role="status">
          {status}
        </p>
      </div>
      <p className="mt-6 text-sm text-slate-600">
        Milestone 1 · No route or weather observations are displayed.
      </p>
    </main>
  );
}
