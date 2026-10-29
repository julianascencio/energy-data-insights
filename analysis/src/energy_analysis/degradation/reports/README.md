# Degradation reports

`generate_report(result, native_land_mask, manifest, output)` writes an offline
`index.html` with embedded scientific figures, mechanism/class PNG and SVG maps,
coverage, parameters, footprint-weighted statistics and complete source attribution.
It consumes completed model results and the retrieved CRU land-support mask; it
never retrieves data, computes degradation rates or fits coefficients.

The analysis pipeline writes reports inside its staged output directory and publishes
only when the complete run succeeds. A standalone call requires a new report directory.
Map rectangles are sample-centred coarse footprints, not land polygons. Each mechanism
panel has its own colour scale; class zero is masked, never plotted as the lowest band.
