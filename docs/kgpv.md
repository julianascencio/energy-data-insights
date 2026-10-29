# GPCC + CRU TS to a KGPV climate map

Retrieval and provider decoding live in `data-retrieval/sources/gpcc` and
`data-retrieval/sources/cru_ts` (under `src/energy_data_retrieval`). Reusable
climatologies, KGPV classification and mapping utilities live in `methods/src/energy_methods`.
There is no country-specific logic or dependency from retrieval to methods.

The **2021 doctoral thesis of Julián Andrés Ascencio Vásquez remains the primary
scientific citation**. The specific classification is from Ascencio-Vásquez,
Brecl and Topič (2019), [open-access paper](https://repozitorij.uni-lj.si/IzpisGradiva.php?id=112635&lang=eng),
Fig. A1, Section 3 and Table 4. See the [complete bibliography](references.md).
This implementation produces climate zones, not simulated PV yields.

## Providers and version pins

| Source | Pin and coverage | Retrieval | Processing |
| --- | --- | --- | --- |
| GPCC | Monthly v2025; 1891 onward; 0.25°, 0.5°, 1°, 2.5° | DWD HTTPS archives, five-year packages through 2020, 2021–2024 package, monthly files from 2025 | CF-decoded monthly precipitation totals in mm; `precip` by default; `precip_infill` only with explicit opt-in |
| CRU TS | v4.10 / `cruts.2604091129.v4.10`; 1901–2025; 0.5° | UEA HTTPS decadal archives, final 2021–2025 package | All ten native variables; TMP → `temperature_c` in degC, PRE → `precipitation_mm` in mm; PET remains mm/day |

Official pages: [GPCC](https://opendata.dwd.de/climate_environment/GPCC/html/gpcc_precipitation_analysis_monthly_v2025_doi_download.html)
and [CRU TS](https://crudata.uea.ac.uk/cru/data/hrg/cru_ts_4.10/).
These are file archives, not REST point-observation APIs. Downloading a region
still transfers the enclosing global archive; the bbox limits decoded output.
UEA requests that users prefer CEDA and use its copy only if CEDA is unavailable
or has not yet published that release. The verified v4.10 release page did not
provide a CEDA/version DOI. No automatic fallback to a different version occurs.

Downloads reuse the shared bounded/retrying HTTP transport. Each raw file has a
SHA-256 checkpoint manifest. Limits default to 256 MiB compressed per file and
2 GiB expanded; parsing also limits selected values per batch. Downloads are
sequential. A global 0.5° GPCC five-year or CRU ten-year batch fits the default
value limits. At finer GPCC resolution, choose a smaller bbox. Native gauge and
error diagnostics remain in the archived input; the precipitation processor
does not apply undercatch corrections or treat gauge count as a quality filter.

CRU TS is ODbL with Database Contents License, attribution and share-alike.
Attribute **Climatic Research Unit, University of East Anglia** and Harris et al.
(2020). GPCC requires the resolution-specific dataset citation; each request and
manifest exposes its DOI. Source licenses are not replaced by a code license.

Both products also appear in `energy-retrieve discover --latitude ... --longitude ...
--grid-only --offline` as documented grid candidates. Discovery does not claim
a valid land cell or actual observations without reading the native grid.

## Command-line workflow

Install the locked workspace; no API credentials are needed:

```bash
uv sync --locked --all-packages

# Inspect exact URLs without downloading anything.
uv run energy-retrieve gpcc --start-year 1991 --end-year 2020 --plan-only
uv run energy-retrieve cru-ts --variable tmp --start-year 1991 --end-year 2020 --plan-only

# Example regional bbox for Chile (cell centres, not clipped polygons).
uv run energy-retrieve gpcc --start-year 1991 --end-year 2020 \
  --resolution 0.5 --bbox -76 -56 -66 -17 --output artifacts/kgpv/gpcc
uv run energy-retrieve cru-ts --variable tmp --start-year 1991 --end-year 2020 \
  --bbox -76 -56 -66 -17 --output artifacts/kgpv/cru

# Supply an independent GHI climatology over the SAME baseline, in kWh/m²/year.
uv run energy-kgpv \
  --temperature artifacts/kgpv/cru/processed/*.nc \
  --precipitation artifacts/kgpv/gpcc/processed/*.nc \
  --annual-ghi /path/to/annual_ghi.nc \
  --start-year 1991 --end-year 2020 --regrid --geojson \
  --output artifacts/kgpv/map
```

GHI is mandatory: **GPCC and CRU TS alone cannot produce KGPV**. The annual input
must contain `annual_ghi_kwh_m2(lat, lon)` with variable attributes `units="kWh m-2"`,
`baseline_start_year=1991`, `baseline_end_year=2020`, and preferably `source`.
It is the mean annual global horizontal **irradiation**, not mean irradiance
in W/m², not a single arbitrary year, and not plane-of-array irradiation.
For monthly energy totals, sum all twelve climatological months with
`skipna=False`; for average daily energy, first multiply by the appropriate
calendar-month day counts. Conversions and upstream missing-data coverage must
be verified by the caller. No irradiance provider is silently substituted.

`--regrid` explicitly bilinearly aligns continuous precipitation and GHI to the
CRU temperature grid. Without it, mismatched grids fail. Supply an input halo
around the target bbox if interpolation is needed at regional edges. Missing
neighbours can propagate NaNs. There is no extrapolation, cyclic-seam wrapping
or conservative precipitation regridding. Classification happens **after**
interpolation; do not interpolate class IDs linearly.

Outputs are `kgpv.nc`, optional bounded `kgpv.geojson`, two monthly climatology
NetCDFs including valid-year counts, and `manifest.json` with input SHA-256 hashes,
baseline, interpolation policy, method references and class areas. GeoJSON uses
regular grid cell polygons in EPSG:4326; it is limited to 100,000 features and
requires at least two regular cell centres per axis. NetCDF is the main global
output. Area summaries use spherical cell areas, not unweighted pixel counts.

## Scientific rules and explicit conventions

The original publication used 1990–2016. The commands above deliberately use
1991–2020 as an example; this produces an updated layer, not a reproduction of
the original published raster. A short baseline can be used for testing, but
must not be represented as a long-term climate normal.

`monthly_climatology` streams batches while retaining only twelve sums and
counts per grid cell. It gives each year's monthly mean/total equal weight.
Every month in the selected baseline must occur exactly once; missing or
repeated months fail. By default each cell needs every year for every month.
`--minimum-valid-years` relaxes cell coverage explicitly and keeps counts in
the outputs. Data gaps never become zero rain or fabricated temperature.

For each cell, the annual temperature is the arithmetic mean of twelve monthly
means; annual precipitation is the sum of twelve monthly mean totals.
Kottek et al. (2006), Eq. 2.1 defines `Pth = 2*Tannual + offset`, with offset:
0 if at least two thirds of annual rain falls in winter, 28 if at least two
thirds falls in summer, otherwise 14. Summer is April–September in the north,
October–March in the south; the equator uses the northern convention.

Apply Fig. A1 in this order:

1. **F Polar:** warmest month ≤10°C.
2. **B Desert:** annual precipitation ≤5×Pth.
3. **C Steppe:** annual precipitation ≤10×Pth, after excluding desert.
4. **A Tropical:** coldest month ≥18°C.
5. **D Temperate:** coldest month >−3°C.
6. **E Cold:** remaining cells.

The exact-18°C case closes the strict-inequality gap in KGPV Fig. A1 using
Kottek's inclusive tropical rule. Aridity comparisons allow only eight machine
epsilons scaled to the values, to avoid changing exact boundaries through
12-month sum round-off. This is not a physical uncertainty band. Irradiation
zones use fixed upper-inclusive boundaries L≤1130, M≤1560, H≤2070, K>2070
kWh/m²/year. The paper gives thresholds but not exact-edge ownership; that
ownership is an explicit implementation convention. Thresholds are never
recalculated from a local subset.

The 24 raw TP/I combinations are merged using the published Table 4:

| TP | L | M | H | K |
| --- | --- | --- | --- | --- |
| A | AH | AH | AH | AK |
| B | BH | BH | BH | BK |
| C | CH | CH | CH | CK |
| D | DL | DM | DH | DH |
| E | EL | EM | EM | EM |
| F | FL | FL | FL | FL |

Class ID zero means no data. IDs 1–12 are respectively AH, AK, BH, BK, CH, CK,
DL, DM, DH, EL, EM, FL. IDs are an internal encoding; raw/merged string labels
and NetCDF flag metadata are retained. Ocean/Antarctica exclusion comes from
input masks (CRU TS excludes Antarctica), not a rough latitude cutoff.
No new land/population re-ranking is performed when updating input datasets.

## Python APIs and validation

- Sources: `GPCCRequest`, `GPCCClient`, `CRUTSRequest`, `CRUTSClient`, and each
  source's `iter_monthly` generator.
- `energy_methods.climatology.monthly_climatology`: calendar aggregation and
  per-cell coverage gates, independent of any provider.
- `energy_methods.kgpv.classify_kgpv`: vectorized NumPy arrays shaped `(..., 12)`;
  `map_kgpv`: labelled grids with exact coordinate and baseline validation.
- `energy_methods.mapping`: `normalize_grid`, `regrid`, `cell_areas_km2`,
  `class_area_summary`, `write_geojson`; reusable outside KGPV.

Offline tests cover all 24 zone merges, precedence, exact thresholds,
hemispheres, NaNs, CF packing and fill values, monthly labels, download reuse,
coverage gates, an analytic interpolation plane, NetCDF/GeoJSON and the CLI
pipeline. Synthetic fixtures are not independent validation against the
published global map. Live GPCC January 2025 at 2.5° and CRU TS 2021–2025 TMP
files were decoded on 2026-10-29; this was a provider-format smoke check, not a
full global scientific benchmark. They were acquired with the environment's
proxy-aware downloader. A direct live request through the existing HTTP transport
was blocked by this execution environment; transport behavior is covered offline
with HTTP fixtures. Raw provider files are not committed.
