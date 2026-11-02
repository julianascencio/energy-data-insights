# Leaflet 1.9.4

Unmodified ESM distribution (`leaflet-src.esm.js`, renamed `leaflet.mjs`), CSS
and images from https://unpkg.com/leaflet@1.9.4/dist/.
Upstream: https://github.com/Leaflet/Leaflet/tree/v1.9.4.
BSD-2-Clause license: see `LICENSE`. API: https://leafletjs.com/reference.html.

Vendored so the database viewer makes no CDN or map-tile requests. The build
copies the existing Natural Earth 5.1.1 1:110m country outlines from
`examples/connectors/data/generation_coverage_world.geojson` to
`_static/database-world.geojson`; that fixture retains its provenance metadata.
Natural Earth is public domain: https://www.naturalearthdata.com/about/terms-of-use/.
The overview boundaries do not imply site-level positional accuracy.
