/** Lazy boundary: the map engine is installed but not loaded by the foundation page. */
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';

export async function loadMapEngine() {
  const [maplibre] = await Promise.all([
    import('maplibre-gl'),
    import('maplibre-gl/dist/maplibre-gl.css'),
  ]);
  maplibre.setWorkerUrl(workerUrl);
  return maplibre;
}
