# PVGIS: complete version 5 and version 6 connectors

`energy_data_retrieval.sources.pvgis` connects to all seven documented PVGIS 5
calculation/data endpoints and all **27 operations on 20 paths** in the PVGIS 6
OpenAPI contract reviewed on **31 October 2026**. No API key is required.
Version 5.3 is the default for `PVGISClient`; version 5.2 is explicit. Use the
separate `PVGIS6Client` for the newer API. No unversioned URL or automatic
version fallback is used.

The data are satellite/reanalysis resource estimates and modelled PV outputs,
not measurements of an operating plant. Coverage, source years and model choices
vary by API version and location. A successful request does not validate a model
against field observations.

See the executable [seven-tool PVGIS 5 example](../examples/connectors/plot_pvgis_legacy.py)
and [PVGIS 6 site workflow](../examples/connectors/plot_pvgis_v6.py). Their complete
real API responses, metadata and SHA-256 manifests are bundled for offline use.

## Quick start: hourly resource and PV estimates

```python
from pathlib import Path
from energy_data_retrieval.sources.pvgis import PVGISClient, PVGIS_HOSTS
from energy_data_retrieval.transport import HTTPClient

with HTTPClient(PVGIS_HOSTS) as http:
    result = PVGISClient(http).hourly(
        28.4775,
        -16.3294,
        startyear=2020,
        endyear=2020,
        components=True,
        pvcalculation=True,
        peakpower=1,
        loss=14,
        angle=25,
        aspect=0,
    )

hourly = result.table("outputs", "hourly")
inputs = result.json()["inputs"]
field_metadata = result.json()["meta"]
result.save(Path("pvgis_hourly.json"))
```

This requests a 1 kWp system at 25° tilt with south-facing orientation under
PVGIS 5 conventions. Returned hourly `P` is watts; radiation components are
W/m². `loss=14` is the provider's aggregate system-loss input in percent, not
an annual degradation rate. Inspect the full metadata before interpreting or
combining returned fields. The table helper retains native column names and
values. It does not round timestamps, convert units or fill missing data.

## PVGIS 5: all seven endpoints

All are GET requests under `https://re.jrc.ec.europa.eu/api/v5_3/`, or `/v5_2/`
when `PVGISClient(http, version="5.2")` is selected. Coordinates are supplied
as `latitude, longitude` to convenience methods and as `lat, lon` to `request`.

| Native endpoint | Python method | Product / required additional inputs |
| --- | --- | --- |
| `PVcalc` | `grid_connected` | Grid-connected energy/performance; `peakpower` **kW**, `loss` percent |
| `SHScalc` | `off_grid` | Off-grid PV/battery; `peakpower` **W**, `batterysize` **Wh**, `consumptionday` **Wh/day**, `cutoff` percent |
| `MRcalc` | `monthly_radiation` | Monthly radiation/temperature; select at least one output flag, e.g. `horirrad=True` |
| `DRcalc` | `daily_radiation` | Representative daily profiles; `month` (0 = all months) and at least one output flag |
| `seriescalc` | `hourly` | Hourly irradiance/weather; optional `pvcalculation=True` also requires peakpower kW and loss percent |
| `tmy` | `typical_year` | Typical meteorological year, selected source months and metadata |
| `printhorizon` | `horizon` | Terrain horizon and solar profiles |

Every documented optional parameter is accepted through the generic request or
named methods: radiation database, module technology, tracking, optimum angles,
user horizon, hourly demand, energy-cost assumptions and output selections.
Unknown parameters fail before network access, making spelling errors visible.

```python
# Call inside the HTTPClient context from the quick-start example.
api = PVGISClient(http)
monthly = api.monthly_radiation(28.4775, -16.3294, horirrad=True, avtemp=True)
daily = api.daily_radiation(28.4775, -16.3294, month=6, **{"global": True})
# "global" is a Python keyword, so use a dictionary for the native API name.
off_grid = api.off_grid(
    28.4775,
    -16.3294,
    peakpower=1000,
    batterysize=2000,
    consumptionday=3000,
    cutoff=20,
    hourconsumption=[1 / 24] * 24,
)
# This API version exposes CSV/basic for all tools and EPW for TMY.
epw = api.typical_year(28.4775, -16.3294, outputformat="epw")
epw.save(Path("weather.epw"))
```

`hourconsumption` requires 24 nonnegative fractions summing to one, ordered by
local standard time without daylight saving. `userhorizon` accepts a numerical
sequence or comma-separated heights, beginning at north and moving clockwise.
The connector defaults to JSON rather than the provider's CSV default, so input
and output metadata are easy to inspect. Native CSV/basic/EPW bytes remain
available without rewriting headers.

Provider database selection is used when `raddatabase` is omitted. Do not copy
obsolete database names from older examples: source availability differs between
5.2 and 5.3. Explicit start/end years are validated for order; TMY requires at
least ten source years when both bounds are given. The provider enforces actual
coverage and availability.

## PVGIS 6: every published operation

The versioned base URL is
`https://photovoltaic-geographic-information-system.ec.europa.eu/api/v6`.
All parameters retain their OpenAPI spelling, including `peak-power`.

| Path | Python method | Supported HTTP methods |
| --- | --- | --- |
| `/performance/broadband` | `performance` | GET, POST |
| `/performance/broadband-multiple-surfaces` | `multiple_surface_performance` | GET, POST |
| `/power/broadband` | `power` | GET, POST |
| `/power/broadband-multiple-surfaces` | `multiple_surface_power` | GET, POST |
| `/power/surface/optimisation` | `optimize_surface` | GET, POST |
| `/solar-position/overview` | `solar_position` | GET, POST |
| `/meteorological/typical-meteorological-year` | `typical_year` | GET |
| `/meteorological/degree-days` | `degree_days` | GET |
| `/topography/horizon-profile` | `horizon` | GET, POST |
| `/topography/elevation` | `elevation` | GET |
| `/coverage/available-sources-in-selected-location` | `available_sources` | GET |
| `/coverage/location-within-selected-source` | `location_in_source` | GET |
| `/coverage/layers` | `coverage_layers` | GET |
| `/coverage/layers/{name}` | `coverage_layer(name)` | GET |
| `/coverage/map` | `coverage_map` | GET |
| `/reference/citation` | `citation` | GET |
| `/reference/publications` | `publications` | GET |
| `/reference/conventions-in-pvgis` | `conventions` | GET |
| `/reference/license` | `license` | GET |
| `/features` | `features` | GET |

```python
from energy_data_retrieval.sources.pvgis import PVGIS6Client, describe_endpoint, endpoints

with HTTPClient(PVGIS_HOSTS) as http:
    api = PVGIS6Client(http)
    availability = api.available_sources(28.4775, -16.3294)
    result = api.power(
        28.4775,
        -16.3294,
        start_time="2020-06-01T00:00:00",
        end_time="2020-06-02T00:00:00",
        surface_tilt=25,
        surface_orientation=180,
        verbose=1,
        **{"peak-power": 1},
    )
    conventions = api.conventions()

frame = result.table(columns=("timestamps", "power", "global_inclined_irradiance"))
print(result.json()["technology"])
print(endpoints("6"))
print(describe_endpoint("/power/broadband")["parameters"])
```

`verbose=1` retains power timestamps and intermediate quantities. Some default
responses contain only the requested array. The complete payload remains
available through `json()` even when a subset of columns is selected for a table.
Version 6 advertises global land plus 25 km offshore and 2014–2025 temporal
coverage in the reviewed release; use the coverage endpoints and inspect the
returned source metadata for the actual request.

Multiple-surface requests require equally long lists of orientation, tilt and
peak power. Defaults for omitted arrays have one element, so provide all three
when requesting two or more surfaces:

```python
# Inside a live HTTPClient context:
result = api.multiple_surface_power(
    28.4775,
    -16.3294,
    surface_orientation=[90, 270],
    surface_tilt=[25, 25],
    start_time="2020-06-01T00:00:00",
    end_time="2020-06-02T00:00:00",
    **{"peak-power": [1, 1]},
)
```

### Custom horizon files and native outputs

```python
# Inside a live HTTPClient context, with your own existing JSON/CSV horizon:
result = api.horizon(
    28.4775,
    -16.3294,
    horizon_file=Path("horizon.json"),
    angle_output_units="Degrees",
)
```

A JSON horizon contains `horizon_height` (at least four values), optional
`azimuth` of equal length, and `units` (`degrees` or `radians`, default degrees).
A CSV horizon contains comma-separated height values in degrees. Files are
limited to 1 MiB. Supplying `horizon_file` chooses the corresponding POST variant;
all other parameters go into its form body. Uploaded content is represented in
provenance by its hash and byte count. Plain `horizon_profile` strings select the
GET representation instead. Uploading is explicit; no local files are searched.

`request(path, parameters={...}, method="POST")` also exposes the native POST
operation where the horizon upload is optional. Python lists become repeated
query/form fields. `None` omits an optional parameter and therefore invokes the
provider's default; it is not a request to clear that default.

The connector preserves JSON, GeoJSON, CSV, EPW, PNG, ZIP, HTML and BibTeX response
bytes. Choose native format parameters such as `csv="power.csv"`,
`epw="weather.epw"`, or supported plot flags. Consult `describe_endpoint` for the
specific operation. Provider format precedence still applies; do not request
several competing formats. `text()` decodes UTF-8 outputs, `json()` validates JSON,
and `save(path)` writes any format with a separate provenance manifest. HTML,
ZIP and image outputs are stored without execution or extraction.

## Units, clocks and interpretation

| Quantity | PVGIS 5 | PVGIS 6 |
| --- | --- | --- |
| Input coordinates | Decimal degrees | Decimal degrees; output coordinates can be radians |
| Surface azimuth input | `aspect`: south 0°, west +90°, east −90° | `surface_orientation`: north 0°, east 90°, south 180° |
| Grid-connected rated power | `peakpower`, kW | `peak-power`, kWp, scalar or one per surface |
| Off-grid rated power/storage | W / Wh | Use the version 5 `SHScalc` endpoint |
| Output angles | Read each native field definition | Many default to radians; `angle_output_units` is available where documented |
| Hourly timestamps | Retain source-minute offsets and source UTC/localtime semantics | Respect `timezone` and returned offsets; default UTC |
| TMY | A composite of selected source months | A composite with native method/weighting metadata |

Degree-day thresholds are specified in °C by the v6 contract even when another
output temperature unit is selected. A period label does not imply that a full
month/year was requested. Keep the exact request interval with each result.
Never treat monthly energy as instantaneous power or infer a degradation rate
from PVGIS's aggregate loss input. Source model/module assumptions are part of
the result, not observations of the actual installation.

## Provenance, resource limits and verification

The existing shared transport enforces HTTPS host allowlisting, no redirects,
finite timeouts, bounded response size, rate spacing and retries. The new public
binary/calculation path additionally handles repeated parameters and multipart
uploads. It retries transient 429/5xx failures including PVGIS 529 overload,
respects bounded `Retry-After`, and reports HTTP status plus the provider request
ID when available. Default spacing is 0.25 seconds, below PVGIS 5's documented
30 requests/second/IP ceiling. Avoid parallel bulk requests; provider capacity
and fair-use rules still apply. No credentials are accepted on this path.

Binary/calculation responses deliberately bypass the shared cache. `save`
records the exact response hash, byte count, endpoint, method, parameters,
retrieval time, media type and provider request ID. `load_response(path)` checks
size and hash before offline use. Checksums detect accidental changes, not
cryptographic authenticity of the provider.

The packaged v6 request contract includes its upstream OpenAPI URL, SHA-256 and
review date. It is loaded locally, never downloaded on import. Regenerate it only
after reviewing provider changes:

```bash
uv run python scripts/prepare_pvgis_contract.py downloaded-openapi.json \
  data-retrieval/src/energy_data_retrieval/sources/pvgis/v6_contract.json \
  --verified-at YYYY-MM-DD
```

Offline tests cover every listed GET/POST route, multipart body placement,
repeated query values, zero/null preservation, invalid inputs, error/retry paths,
byte limits and native output preservation. Real public captures underpin the
gallery; CI does not require live availability. During the 31 October 2026 smoke
check, the surface optimisation endpoint succeeded with `SHGO`; the provider's
then-default `L-BFGS-B` returned HTTP 400 for the short demonstration request.
The connector exposes the method choice and preserves provider errors without
silently switching optimisation algorithms.

## Provider documentation and attribution

- [PVGIS 5 non-interactive API](https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis/using-pvgis-5/api-non-interactive-service_en)
- [PVGIS 6 API documentation](https://photovoltaic-geographic-information-system.ec.europa.eu/api/v6/docs)
- [PVGIS 6 OpenAPI contract](https://photovoltaic-geographic-information-system.ec.europa.eu/api/v6/openapi.json)
- [PVGIS release notes](https://photovoltaic-geographic-information-system.ec.europa.eu/api/release-notes)

The European Commission Joint Research Centre supplies these services. Retain
provider attribution and check current data reuse terms. The v6 software license
metadata is not a substitute for dataset-specific terms. These connector calls
implement retrieval; they do not reimplement the JRC's numerical models. The
repository's primary thesis citation and individual source references remain
separate.
