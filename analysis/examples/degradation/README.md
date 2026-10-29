# Global 2016–2018 degradation scenario

`global_2016_2018.toml` is an executable coarse global sampling study, with a
companion calibration JSON. See the [workflow](../../src/energy_analysis/degradation/README.md)
for retrieval, offline computation, equations, attribution and interpretation.

A live run on 29 October 2026 retrieved 213 location-years through the existing
CRU TS and Open-Meteo providers: **1,867,584 hourly location records** at 71
CRU-supported land centres. All three years use explicit ERA5; the 15° grid is
a sampling choice, not native climate resolution. The model used the committed
parameters, including the explicit A_N=1 and one-cycle-per-day assumptions.

The strict completeness gate mapped **63 centres** and masked **8 at 75°N**.
The source returned 56,152 negative calculated TOA values (all with zero GHI) and
one positive-GHI/zero-TOA hour at an already affected Arctic centre. Raw records
were retained; the analysis marked these UV inputs unavailable, without clipping
or filling. Complete-cell total rates ranged from **0.018881 to 1.101266 %/year**.
These are scenario outputs, not measured degradation or original-thesis validation.

The generated bundle contains normalized hourly inputs and sidecars, CRU source
archive and land masks, input/run manifests, annual stresses, NetCDF/GeoJSON maps,
cell tables, calibration and offline PNG/SVG/HTML reports. Acquired data and
rendered artifacts are deliberately excluded from Git. The CLI reproduces the
workflow using saved inputs; a new live download may reflect provider revisions.
