# A clearer pilot near Rengo: El Mirlo

[Open the annotated gallery and offline download](https://julianascencio.github.io/energy-data-insights/auto_examples/analysis/plot_rengo_module_counting.html).

El Mirlo (CEN ID 2253) is approximately 5.1 km from the rounded Rengo centre
(-70.858, -34.405), in Malloa. Six nearby operating registry entries were screened:
Rengo Solar, Lo Miguel, Rinconada, Pueblo Hundido, El Mirlo and Rosario.
El Mirlo was selected for visible individual frame lines in both directions.
The [developer's project page](https://mirlo.centralpmgd.cl/) confirms its identity
and location. Its project power and the current CEN maximum-power field describe
different quantities; neither is converted to a module count.

## Result and scope

The new counter finds **2,055 image candidates in a southern inspection block**,
across 22 resolved table components. The original counter with its defaults
returns **None (unresolved)** on the same image and scope. Neither is a complete
plant inventory. Rejected cells and tables remain in the exports.

The small same-image visual audit has 72 reference centres in three deliberately
clear strips (four scoring rectangles), plus two negative regions. A one-to-one
match within two delivered pixels gives:

| Method | Matched | Missed | Extra detections | Local recall |
|---|---:|---:|---:|---:|
| Original defaults | 0 | 72 | 0 | 0% |
| Orientation and lattice | 51 | 21 | 0 | 70.8% |

The references were interpreted by a **single AI assistant**, with approximate
centre clicks and row guides. They are not independent human annotations,
field ground truth, a random sample or held-out validation. The first comparison
exposed seam-versus-centre misclicks in two regions; these were corrected by
re-inspecting unannotated pixel enlargements. The initial and corrected files
are both retained. Parameter development used the same image. Consequently,
zero extra detections in these small regions is **not a claim of 100% field
precision**. The remaining candidates have not been individually validated.

This establishes useful candidate extraction and a review workflow. Improving
recall and establishing inventory accuracy require independent labels over
complete tables, shadowed regions and additional sites, ideally with an as-built
schedule or a sufficiently detailed UAV orthophoto.

## What changed in the method

`energy_methods.pv_lattice_counting.count_lattice_pv_modules` adds:

1. Normalised colour screening without a minimum absolute brightness gate.
2. Principal-axis estimation and per-component image rectification, allowing
   arbitrary table orientation rather than only nearly horizontal tables.
3. Long-axis autocorrelation to check the repeating frame pitch independently
   of the observed brightness peaks.
4. Two-row support: three visible transverse frame lines are sufficient.
5. Per-cell spacing, original-pixel colour, local frame contrast, scope and
   source-resolution checks. Missing frame lines and irregular gaps are excluded;
   the algorithm does not fill a lattice from known dimensions or module totals.

This is a deterministic experimental method using NumPy/SciPy, not a pretrained
SAM/YOLO model or an implementation of a published detector. The geometric
module-detection literature, including [Cardoso et al. (2024)](https://doi.org/10.1016/j.apenergy.2024.123242),
provides background. That paper uses high-resolution UAV/3D data; its reported
accuracy does not apply to this basemap pilot. Repeated cell patterns can still
be confused with module frames, which is why the raw-pixel views and independent
validation limits matter. Synthetic tests establish software behaviour under
rotation, noise and missing modules, not real-site accuracy.

## Imagery and provenance

The Esri World Imagery source probe at (-70.8615, -34.4515) reports WV03,
**2024-01-14**, Vivid Advanced / Vantor, **0.31 m source resolution** and
0.30 m service sampling. This is a point metadata query, not a guarantee of
uniform acquisition across the image. The captured detail is 900 × 600 pixels,
bounds (-70.8627, -34.4523, -70.8603, -34.4507), EPSG:4326.

Delivered sampling is approximately 0.245 × 0.296 m. This oversampling adds no
optical detail. A conservative source/delivered ratio of 1.265 is applied to the
three-source-pixel minimum frame pitch. No image sharpening or synthetic imagery
is used. Exact export/query requests, retrieval times, SHA-256 checksums,
parameters, visual annotations and the inspection polygon are committed.

The inspection polygon is manually selected, not a surveyed plant boundary.
GeoJSON positions use the rendered image's georeference and half-pixel offset;
they are not surveyed module positions. Imagery remains © Esri and its licensors;
see the fixture README for attribution and the static-map terms.

## Reproduce and inspect

```bash
uv sync --locked --all-packages
uv run --no-sync python examples/analysis/plot_rengo_module_counting.py
```

```python
from energy_analysis.module_counting.rengo import export_rengo_study

export_rengo_study(
    "examples/analysis/data/rengo_modules",
    "rengo-audit",
)
```

The gallery download includes the script, exact local inputs, both annotation
versions, the guide and computed CSV/GeoJSON/JSON exports. It runs offline using
the repository's installed packages, on Python 3.12 or 3.13. The gallery also
reports the effect of frame-prominence values 0.012, 0.015 and 0.018 without
selecting whichever count looks most desirable.
