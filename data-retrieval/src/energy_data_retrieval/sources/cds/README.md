# Copernicus Climate Data Store API

This source uses the **official `cdsapi` Python client** for direct CDS access.
`cds-retrieve` accepts a dataset slug and the selection JSON from its download
form. `cds-era5` builds sequential monthly requests for ERA5 single-level hourly
data or monthly averaged reanalysis. CDS validates dataset-specific fields,
availability, request limits and permissions.

The adapter saves **native files**, including any ZIP returned by CDS. It does
not extract archives, select nearest grid cells, convert units, shift timestamps
or feed the files directly into a scientific method. It complements the separate
Open-Meteo and Earthmover adapters; no fallback between sources is automatic.

## Install and authenticate

From the repository root:

```bash
uv sync --locked --all-packages --extra cds
```

For an installed package, use `pip install 'energy-data-retrieval[cds]'`.
Planning, discovery and verified reuse of completed files do not require the SDK.

Create a CDS account and follow the [official setup instructions](https://cds.climate.copernicus.eu/how-to-api).
Put your personal access token in `CDSAPI_KEY` using your environment/secret manager,
or create `~/.cdsapirc` **outside this repository**:

```yaml
url: https://cds.climate.copernicus.eu/api
key: <PERSONAL-ACCESS-TOKEN>
```

The current key is a personal access token, not the old `UID:API-key` format.
The official SDK also supports `CDSAPI_RC` for a different local configuration
file. This adapter fixes the endpoint to the CDS HTTPS API and enables TLS
verification. It does not use `CDSAPI_URL` to redirect requests to another service.
ADS/CAMS and CEMS have separate endpoints and are outside this connector's scope.

Accept each dataset's terms manually on its CDS download page before retrieving
it. The code never accepts terms on your behalf. Credentials do not belong in
request JSON, command arguments, notebooks or Git. SDK diagnostic callbacks are
suppressed because they can contain credentials or signed download URLs; failures
give a local error directing you to check the selection, account and CDS job page.

## ERA5 example: Canary Islands

Inspect the request without credentials, network access or job submission:

```bash
uv run energy-retrieve cds-era5 \
  --start 2024-02-01 --end 2024-02-29 \
  --variables 2m_temperature surface_solar_radiation_downwards \
  --area 29 -17 28 -16 --plan-only
```

Download the same small-area selection:

```bash
uv run energy-retrieve cds-era5 \
  --start 2024-02-01 --end 2024-02-29 \
  --variables 2m_temperature surface_solar_radiation_downwards \
  --area 29 -17 28 -16 --output data/cds-era5
```

`--area` is **north, west, south, east**, matching CDS. This differs from the
west/south/east/north `--bbox` used by some other repository commands. Coordinates
use degrees and longitude −180…180; split areas crossing the dateline explicitly.
Dates are inclusive source labels, and hourly requests include all 24 UTC hours
for each selected day. Actual Gregorian days are generated, including leap days.
The helper performs one request per intersecting month, with no parallel jobs.
Large areas or many variables may still exceed CDS service limits; narrow those
selections or use explicit generic requests.

For monthly means, supply whole calendar months and add `--monthly-means`:

```bash
uv run energy-retrieve cds-era5 \
  --start 2024-01-01 --end 2024-12-31 --monthly-means \
  --variables 2m_temperature surface_solar_radiation_downwards \
  --area 29 -17 28 -16 --data-format netcdf --output data/cds-monthly
```

This selects `reanalysis-era5-single-levels-monthly-means`, product
`monthly_averaged_reanalysis`, with the CDS `00:00` selection. It is not a series
of midnight observations. ERA5-Land has different products and accumulation
semantics; use its exact catalogue request through `cds-retrieve` instead.

## Any CDS catalogue selection

Use the CDS dataset page's **Show API request code**. Save only the `request`
dictionary as JSON (double quotes; no Python code or credentials), then run:

```bash
uv run energy-retrieve cds-retrieve \
  --dataset reanalysis-era5-single-levels \
  --request data-retrieval/examples/cds-era5-request.json --plan-only

uv run energy-retrieve cds-retrieve \
  --dataset reanalysis-era5-single-levels \
  --request data-retrieval/examples/cds-era5-request.json --output data/cds-custom
```

The generic command sends **one exact selection**; it does not invent field
names, split requests, infer calendars or claim all catalogue datasets have been
tested. It can carry catalogue-specific pressure-level, ERA5-Land or climate
projection requests after you provide their correct dataset IDs and selections.
The native dataset page is retained in provenance. Cite that dataset's specific
DOI and documentation in downstream analyses; the CDS access citation alone does
not replace them.

## Python API

```python
from pathlib import Path

from energy_data_retrieval.sources.cds import CDSClient, CDSRequest

request = CDSRequest(
    "reanalysis-era5-single-levels",
    {
        "product_type": ["reanalysis"],
        "variable": ["2m_temperature"],
        "year": ["2024"],
        "month": ["02"],
        "day": ["01"],
        "time": ["12:00"],
        "area": [29, -17, 28, -16],
        "data_format": "grib",
        "download_format": "unarchived",
    },
)
artifact = CDSClient(maximum_download_bytes=256 * 1024**2).download(request, Path("data/cds"))
print(artifact.path, artifact.sha256, artifact.reused)
```

## Outputs, limits and restart behaviour

Each selection lives in `<output>/<dataset>/<request-sha256>/`, containing the
native `download.*` file and `manifest.json`. The manifest includes the exact
selection, endpoint, retrieval time, SDK version, dataset link, reference IDs,
byte count and artifact SHA-256. Signed URLs and SDK response objects are not
stored. The content signature determines the suffix: `.grib`, classic NetCDF
`.nc`, HDF5/NetCDF4-container `.h5`, `.zip`, `.gz`, or `.bin` for other formats.
Signature detection identifies a container; it does not validate scientific
contents. Even `download_format=unarchived` may yield an archive for multiple files.

Results publish as a complete directory after transfer and hashing. Exceptions
remove temporary files; a hard process kill can leave an unpublished `.cds-*`
directory for manual inspection. Repeating the same selection reuses the file
only after verifying its request, size and SHA-256. Corrupt or incomplete existing
results fail instead of silently overwriting. Completed months survive a later
failure. Remote jobs are not checkpointed or reattached after interruption;
rerunning an unfinished selection may submit a new CDS job.

`--maximum-download-mib` defaults to 1024 per result: advertised size is checked
before downloading and actual size afterwards. This is not a custom streaming
quota; the SDK owns transfer. `--timeout-seconds` defaults to 60 per network
request and `--attempts` to 3. **A network timeout is not a queue deadline**:
CDS processing can take much longer. The planner limits selections to 1,200 months
and 64 variables; generic JSON is limited to 1 MiB.

A request hash does not pin CDS's changing upstream data. ERA5T can be revised.
Use a new output root to acquire a fresh vintage while retaining prior evidence.
Location discovery lists the two ERA5 products as unverified candidates; neither
discovery nor the Open-Meteo sample probe submits CDS jobs or reads CDS credentials.

## Scientific interpretation and references

Native temperature is commonly in kelvin; accumulated radiation is commonly in
J/m². Do not relabel radiation as W/m² or divide every product by 3,600: hourly,
monthly averaged and ERA5-Land accumulations have different conventions. Inspect
the variables, units, dimensions and time bounds using the [ERA5 data documentation](https://confluence.ecmwf.int/pages/viewpage.action?pageId=185085702).
For interval-start weather output, explicitly acquire any extra endpoint required
by the chosen transformation. No endpoint is automatically added here.

The repository thesis remains the primary reference. Source-specific citations
are maintained in `methods/src/energy_methods/references.json`:
`copernicus_cds_api`, `hersbach_2020_era5`, `era5_single_levels`
([DOI](https://doi.org/10.24381/cds.adbb2d47)), and
`era5_single_levels_monthly` ([DOI](https://doi.org/10.24381/cds.f17050d7)).
Tests use synthetic SDK responses; no live authenticated download is claimed.
