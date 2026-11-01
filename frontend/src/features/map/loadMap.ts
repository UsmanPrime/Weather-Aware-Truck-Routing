/** Lazy boundary: the map engine is installed but not loaded by the foundation page. */
export async function loadMapEngine() {
  const [maplibre] = await Promise.all([
    import('maplibre-gl'),
    import('maplibre-gl/dist/maplibre-gl.css'),
  ]);
  return maplibre;
}
