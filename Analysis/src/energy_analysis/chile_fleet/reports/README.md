# Chile fleet reports

Report generation belongs to its analysis:
`Analysis/src/energy_analysis/chile_fleet/reports/`. Reusable numerical methods
remain in `methods/`; data acquisition remains in `Data-retrieval/`.

## Generate from saved outputs

```bash
uv run --no-sync energy-chile report --run artifacts/demo/results
```

Or call Python directly:

```python
from pathlib import Path
from energy_analysis.chile_fleet.reports import generate_reports

manifest = generate_reports(Path("artifacts/demo/results"))
print(manifest["output_path"])
```

The default destination is the saved analysis's `reports/` directory. A custom
`output_path` is supported; an existing destination is never overwritten, and
report files cannot be placed inside the source's `hourly/`, `models/` or `tdp/`
data folders. Both completed model runs and frozen-reference comparisons work.

## Outputs

| File | Purpose |
| --- | --- |
| `index.html` | Responsive fleet dashboard with search, comparison filters and sortable metrics |
| `sites/site-NNNNNN.html` | Separate site evidence pages; opaque filenames never use site names or IDs |
| `data.json` | Original site summaries, fleet summary and source manifest |
| `website_article.md` | Unpublished website article draft from the supplied results |
| `linkedin_post.md` | Unpublished LinkedIn draft from the supplied results |
| `references.json`, `references.bib`, `references.md` | Complete citation catalogue, thesis first |
| `manifest.json` | Source and output SHA-256 hashes, report identity and interpretation |

Open `index.html` directly. HTML, SVG, CSS and JavaScript are embedded; the report
does not fetch a font, chart library, analytics script or data service. Reference
links open official online sources only when followed. Keep the output directory
together to preserve links between the dashboard, site pages and downloads.

## Scientific and performance behavior

- Reports read saved results without retrieving data, fitting models, changing
  expected generation or recomputing operational classifications.
- Fleet totals include only comparable records; insufficient records stay visible.
  Matched actual and reference values preserve reported zeros and missing data.
- Saved site summaries are checked against saved fleet totals, and available
  source-output hashes are verified. Source files are hashed again before the
  staged report directory is published to detect concurrent changes.
- Hourly evidence is loaded one site at a time. The entry page embeds only site
  summaries. Longer site histories use matched daily, monthly or yearly sums rather than
  embedding the full fleet history; sums preserve energy, and all-missing bins
  stay blank. Charts use the report window. TDPs use their original saved history.
- The report retains held-out metrics, final-fit metadata, weather statistics,
  hourly candidate states and available TDP qualifications. Frozen comparisons
  explicitly show that these details are unavailable when they were not saved.
- TDP P90 means the empirical hourly 90th percentile, not annual P90 energy.
  IEC-informed screens do not confirm operating causes, faults or recoverable loss.
- Explicit synthetic metadata is shown on every page and publication draft.
  Passing `synthetic=False` cannot suppress known synthetic provenance. Unspecified
  inputs are described as user-supplied outputs, not validated field measurements.
- Source text is escaped for HTML, site filenames are generated independently
  of labels, and source-manifest paths cannot escape the analysis directory.
- Publication text remains a draft. Generation does not publish or send anything.

The main scholarly citation is Julián Andrés Ascencio Vásquez's 2021 doctoral
dissertation, *Modelling and worldwide assessment of performance and aging of
photovoltaic modules and systems*, University of Ljubljana. The complete catalogue
is taken from `energy_methods.references`; background and optional sources retain
their explicit roles so citation does not imply implementation or data use.
