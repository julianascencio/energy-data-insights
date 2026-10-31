# Chile: largest and smallest registered solar-plant module audits

Two Analysis examples extend the [Icor counter](pv-module-counting.md):

- [CEME1: largest-site inventory and imagery audit](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_chile_largest_module_counting.html).
- [Concón: smallest registered operating solar entry](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_chile_smallest_module_counting.html).

**Neither establishes an automatic whole-plant image count.** These are real-data
transferability tests with explicit unresolved results, not successful repetitions
of the Icor count. The gallery ZIP contains both scripts, exact static maps,
metadata, registry selection and machine-readable audit exports.

| Measurement | CEME1 | PMGD PFV Concón |
| --- | ---: | ---: |
| CEN site ID | 2010 | 2082 |
| CEN `potencia_maxima`, MW | 412.9326 | 0.1 |
| Documented DC nameplate, MWp | 480.19 | 0.118 |
| Published module inventory | 882,720 | Not established |
| Image module count | Unresolved: insufficient sampling | Unresolved: no usable frame grid |
| Whole-plant image count | Not established | Not established |

## Selection and inventory evidence

The 2026-10-31 [CEN registry](https://api-infotecnica.coordinador.cl/v1/centrales-sin-filtrar/extended/)
has 1,384 records. Filter `tipo_central_nombre == Solares`,
`estado == EN_OPERACION` and finite positive `potencia_maxima`; sort by power
and ID. This leaves 757 entries. Coordinates do not affect ranking. Missing,
zero and negative power values are excluded. Ties remain in the ranking; the
pinned endpoints are unique in this snapshot. The CSV projects **all records**
onto seven selection fields; the original response hash is also retained.

This ranks the registry's operating **solar category**, including solar thermal;
both extrema are independently confirmed photovoltaic. It is not a census of
private, off-grid or net-billing systems, or a minimum by surveyed ground area.
Separate projects are not combined. Registry maximum power is not assumed MWp.

[Generadora Metropolitana](https://www.generadora.cl/instalaciones/centrales/nueva-renca/)
also identifies CEME1 as Chile's largest PV plant. The
[CEN-hosted engineering report](https://www.coordinador.cl/wp-content/uploads/2025/12/EE-EN-2024-0488-R1_Potencia_Maxima_PFV_CEME1.pdf),
section 3.2 and Table 3.1 (pp. 15–16), records 178,560 modules rated 540 W and
704,160 rated 545 W: **882,720 total**, also consistent with 29,424 strings × 30
modules. The rating sum is 480.1896 MWp, rounded to 480.19 in the report. This is
an inventory cross-check, **not image recognition**; it never enters detection.

For Concón, the [commissioning form](https://cartas.coordinador.cl/download_anexos/6823eb7535635710e101e8d7/0)
links the PMGD to Abastible and installer Sunbelt. The
[installer's page](https://sunbelt.cl/proyectos/planta-de-gas-concon/)
reports 118 kWp with a Huawei string inverter and supplies photographs but no
verified module total. Personal contact fields are not republished.

## What the imagery supports

Three attributed **static Esri World Imagery exports** are used, not calibrated
bands or a newly open-licensed imagery dataset. Requests use EPSG:4326 and
matching degree/pixel aspect ratios to prevent automatic extent expansion.
Image hashes are checked before analysis. Every plot visibly credits the source.

At the CEME1 probe, metadata report 2025-08-28 acquisition and 0.34 m source
resolution, but **1.2 m service sampling**, with maximum map level 17. The
delivered detail viewport samples about 1.33 m north–south. The report's 1.134 m
module edge occupies less than one effective sample. The counter needs at least
three pixels per pitch and rejects the image before confusing array strips with
modules. Finer export requests failed; a level-19 tile returned a “map data not
yet available” placeholder. Neither failed response is counted or bundled.

The Concón probe reports 2026-07-02, 0.34 m source resolution and 0.3 m service
sampling. Strong glare obscures frames. The actual counter, using explicit
table-size/orientation parameters, finds no usable grid; three colour thresholds
return `None`. This is not zero panels or evidence of missing or faulty modules.

Metadata concern one probe, not guaranteed uniform coverage across a mosaic.
CEME1's diagnostic viewport is partial, with
[OSM way 1063236315](https://www.openstreetmap.org/way/1063236315) as context.
Concón uses a manually selected inspection rectangle. Neither is a verified
as-built boundary. No full-site extrapolation is made.

## Reproduce and export

```bash
uv sync --locked --all-packages
uv run --no-sync python examples/analysis/plot_chile_largest_module_counting.py
uv run --no-sync python examples/analysis/plot_chile_smallest_module_counting.py
```

```python
from energy_analysis.module_counting.chile import export_chile_audit

export_chile_audit(
    "examples/analysis/data/chile_modules",
    "/tmp/chile-module-audit",  # fresh directory
)
```

The export contains the eligible ranking and `count_audit.json`. Published
inventory, image candidates and whole-plant counts are separate fields. Unknown
counts serialize as `null`; no fake per-module CSV/GeoJSON is manufactured.
The complete gallery ZIP includes these outputs and runs offline on Python 3.12/3.13.

`scripts/refresh_chile_module_inputs.py` explicitly downloads the current registry
and saved image/metadata requests into a fresh directory. Changed bytes require
new visual review, ranking and hashes; refreshing never replaces the study silently.

## Remaining work and reuse

A defensible count needs licensed, georeferenced full-site imagery with visible
module frames and reviewed boundaries. Large sites need bounded tiles, seam
de-duplication, missing-coverage checks and held-out manual labels. Concón also
needs an as-built module schedule. Upsampling or generative detail cannot replace
missing optical measurements. Installer photos do not show every module unobscured.

The code license does **not** relicense the map images. They remain © 2026 Esri
and its licensors (Esri, Vantor, Earthstar Geographics and the GIS User Community),
all rights reserved, displayed as research-report illustrations under
[Esri's static-map terms](https://doc.arcgis.com/en/arcgis-online/reference/static-maps.htm).
Retain attribution and check provider terms for other uses. OSM geometry is
© OpenStreetMap contributors, ODbL-1.0. Registry facts are attributed to CEN;
no blanket license for its reports is asserted. Reports and installer photos
are linked, not redistributed in the bundle.
