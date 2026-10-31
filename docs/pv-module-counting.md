# Automatic module counting from aerial imagery

[Open the annotated Icor counting example and complete download](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_candelaria_module_counting.html).

The PNOA/IGN image from the [Candelaria example](satellite-imagery.md) resolves
regular, module-sized frames. The new counter finds **seven tables and 3,030
candidate modules** inside the supplied OSM polygon: **2,946 regular candidates**
and **84 requiring review**. Six further grid positions fail the colour check
and are excluded. Exclusion does **not** prove a module is absent or defective.
These are experimental image-derived counts, not a verified engineering inventory.

| Table, north to south | Detected grid | Counted candidates | Excluded positions |
| --- | --- | ---: | ---: |
| 1 | 26 columns, 11 rows | 286 | 0 |
| 2 | 31 columns, 11 rows | 341 | 0 |
| 3 | 35 columns, 11 rows | 383 | 2 |
| 4 | 46 columns, 11 rows | 506 | 0 |
| 5 | 46 columns, 11 rows | 505 | 1 |
| 6 | 46 columns, 11 rows | 504 | 2 |
| 7 | 46 columns, 11 rows | 505 | 1 |

The method detects these table locations and grid counts automatically; they
are not hand-entered parameters. The known site polygon supplies the search
area. It may cover only part of Planta Icor, so the count must not be treated
as the inventory of the entire catalogue-listed 2,000 kW installation.

## Run and export

From the workspace, install the standard packages (the counting step supports
Python 3.12/3.13 and needs no new dependencies or live provider connection):

```bash
uv sync --locked --all-packages
uv run --no-sync python examples/analysis/plot_candelaria_module_counting.py
```

Or use the analysis API with the captured image and original receipt:

```python
import json
from pathlib import Path
from energy_analysis.module_counting import count_rendered_site
from energy_analysis.module_counting.reports import export_counting_study

data = Path("examples/connectors/data")
site = json.loads((data / "candelaria_site.json").read_text())
study = count_rendered_site(data / "candelaria_pnoa.png", site["footprint"])
print(study.result.estimated_modules, study.result.review_candidates)
export_counting_study(study, "/tmp/icor-module-count")  # fresh output directory
```

The complete gallery download includes the script, original input files and
computed `results/module_candidates.csv`, `results/module_candidates.geojson`
and `results/count_summary.json`. All 3,036 grid positions remain in the exports,
with candidate/review/excluded status, reasons, table/row/column identifiers,
image coordinates and geographic polygons. The summary retains source metadata,
the input SHA-256, parameters, scope and software versions. IDs belong to this
image-processing run; they are not stable plant asset identifiers.

For another RGB image, use `energy_methods.pv_module_counting.count_regular_pv_modules`
with an explicit boolean site mask and `ModuleCountingConfig`. Uint8 RGB or
floating-point RGB in 0..1 is accepted. Table area, colour, orientation, frame
prominence and pitch gates are explicit. Images/cell counts have allocation limits.
No resolved grid returns `estimated_modules=None`, rather than claiming no PV exists.

## What is measured, and what remains uncertain?

1. **Table detection:** blue/grey colour screening, small morphological operations
   and connected components. This is a site-tuned heuristic, not a trained model
   that recognizes all PV technologies or roofs.
2. **Grid detection:** robust fitting of each table's upper edge, shear-corrected
   brightness profiles and SciPy peak detection. Adjacent detected frame lines
   define candidate cells; the method does not fill an ideal grid with assumed modules.
3. **Review:** irregular spacing at seams and weak colour support are flagged.
   Cells outside the site mask or with insufficient colour evidence are excluded.
   Module frames, mounting structures and other repeated patterns can be confused.
4. **Ground scale:** rendered sampling is approximately 0.268 m east–west and
   0.260 m north–south per output pixel. Median detected frame pitch corresponds
   to roughly 1.61 by 1.04 m on the ground. These are plausibility checks; they
   do not establish the source's native resolution or physical module dimensions.
5. **Sensitivity:** nine threshold/prominence combinations produce 3,030–3,032
   candidates. This narrow range is **not a confidence interval or an accuracy
   claim**. Shared errors can persist across every parameter choice.

Independent synthetic tests cover a known inventory, missing modules, noise,
small row shear, clipped images, scope masks and unresolved inputs. The real-site
test verifies reproducibility and provenance; no operator inventory or independent
module annotation has been supplied. To measure precision, recall and count error,
review labelled modules against the image and an as-built inventory, including
seams, shadows, boundaries and omitted tables. Do not infer power, faults or
degradation from the count alone. The 10 m Sentinel-2 image is unsuitable for
individual-module counting. Increasing WMS width does not create native detail.

## Method and data credit

The colour-segmentation approach is informed by Grimaccia, Leva and Niccolai
(2017), [PV plant digital mapping for modules’ defects detection by unmanned
aerial vehicles](https://doi.org/10.1049/iet-rpg.2016.1041). This repository's
RGB screening, frame-profile counter and review rules are its own experimental
implementation, not a reproduction of the paper's HSV/UAV workflow.
[SciPy `find_peaks`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html)
provides the peak detector. Data credit remains PNOA/IGN and © OpenStreetMap
contributors (ODbL), with Cabildo/ITER providing the original site catalogue.
See the [source-imagery guide](satellite-imagery.md) for acquisition, licences
and the distinction between native satellite imagery and rendered aerial views.
