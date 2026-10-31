REAL CAPTURED DATA — Planta Icor, Arico, Tenerife

This example is about 19.2 km south of Candelaria, not in that municipality.
The official catalogue identifies the site; the OSM boundary is associated by
point containment, not surveyed or confirmed as the entire 2,000 kW plant.

Files and rights (the repository's code licence does not replace these):

* candelaria_catalogue.geojson: complete canonical JSON from Cabildo Insular de
  Tenerife / ITER, CC BY. candelaria_site.json preserves the original feature,
  request URL/date/checksum, provider power unit and derived spatial association.
  https://datos.canarias.es/catalogos/general/dataset/infraestructuras-de-generacion-de-energia-en-tenerife
* candelaria_osm.json: © OpenStreetMap contributors, ODbL-1.0.
  https://www.openstreetmap.org/copyright
  Original query-bound capture from Orbital PV commit
  498c47e182f9f0e1b0f0d40bc3125ef7c2110a05, examples/ground_imagery/_data/tenerife-osm.json.
  The unchanged sidecar retains its original query and 2026-10-30 retrieval date.
  Way 430266023 contains the official point; neighbouring plants are distinct.
* candelaria_visual/red/scl.tif and candelaria_scenes.json: contains modified
  Copernicus Sentinel data (2026), processed by ESA, distributed by Element 84
  Earth Search. Scene S2A_T28RCS_20260804T115232_L2A, 4 August 2026.
  Native 10 m RGB/red and 20 m SCL; no resampling or artificial sharpening.
  Full STAC asset metadata and checksums are in each unchanged TIFF sidecar.
  https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel2.html
* candelaria_pnoa.png: PNOA/IGN, rendered WMS aerial orthophotography, retrieved
  2026-10-31. Preserve this product/producer attribution and IGN licence terms.
  https://www.ign.es/wms-inspire/pnoa-ma
  https://pnoa.ign.es/web/portal/pnoa-imagen/visualizadores-y-servicios-web
  Acquisition date and native resolution are not established by this request.
  A 768 x 768 rendered viewport is not evidence of a native sensor GSD.
  The original sidecar retains its request, checksum and retrieval date.
* candelaria_tenerife.geojson: extracted, unsimplified Tenerife contour from
  Natural Earth 5.1.1 Admin 0 Countries, public domain. Map scale 1:10 million,
  not 10 m accuracy. Source archive and derived contour hashes are in site.json.
  https://www.naturalearthdata.com/about/terms-of-use/

Saved paths in original sidecars describe the capture environment; files may be
moved with their sidecars. Do not confuse retrieval dates with capture dates.
These data support layout/context checks, not measured output or degradation.
The offline script is ../plot_candelaria_solar_farm.py. Install Python 3.13 and
the pinned Orbital PV imagery dependency as described in docs/satellite-imagery.md.
Live capture is explicit: scripts/prepare_candelaria_imagery.py.
