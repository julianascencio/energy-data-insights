Worldwide BESS project database
===============================

Search battery energy storage projects, filter country/status/chemistry, compare
reported MW and MWh, inspect field-level sources and export selected rows.
The dashboard reports the current snapshot’s coverage and capacity totals.
U.S. and UK inventory subsets dominate the coverage; counts are not a census
or a ranking of the world's installed capacity.

Browse the :doc:`BESS OEM products <bess-oem-database-viewer>`,
:doc:`PV database <database-viewer>` or
:doc:`Database gallery <auto_examples/database/index>`.

.. raw:: html

   <link rel="stylesheet" href="_static/vendor/leaflet/leaflet.css">
   <link rel="stylesheet" href="_static/database-viewer.css">
   <div id="bess-database" data-database="bess" data-base="datasets/bess/">
     <p id="db-status" role="status" aria-live="polite">Loading database catalogue…</p>
     <button id="db-retry" type="button" hidden>Retry loading</button>
     <noscript>Enable JavaScript to use the viewer. Parquet downloads and runnable Python examples are linked below.</noscript>
     <div id="db-workspace" hidden>
       <div class="db-heading"><div><span class="db-eyebrow">ASVA / ENERGY DATA INSIGHTS</span><h2 id="db-title">BESS project intelligence</h2><p>Explore battery storage worldwide. Follow the evidence.</p></div><span class="db-snapshot-badge">Published snapshot</span></div>
       <div id="db-stats" class="db-stats" aria-label="Filtered catalogue statistics" aria-live="polite"></div>
       <p class="db-muted db-capacity-note">Totals follow all active filters, across every page. MW is battery power; MWh is stored energy. Unknown values are excluded. Project phases may overlap, and statuses, dates and rating bases may differ.</p>
       <div class="db-controls db-primary-controls">
         <label>Table<select id="db-table"></select></label>
         <label class="db-wide">Search all metadata<input id="db-search" type="search" placeholder="Search projects, countries, chemistry, owners, sources…"></label>
         <button id="db-reset" type="button">Reset filters</button>
       </div>
       <details class="db-panel db-filter-panel"><summary>Refine results <span>Country, status, chemistry, capacity &amp; availability</span></summary><div class="db-controls">
         <label>Filter column<select id="db-filter-field"></select></label>
         <label>Exact value<select id="db-filter-value"></select></label>
         <label>Numeric field<select id="db-metric"></select></label>
         <label>Minimum<input id="db-min" type="number" step="any" placeholder="No minimum"></label>
         <label>Maximum<input id="db-max" type="number" step="any" placeholder="No maximum"></label>
         <label>Numeric availability<select id="db-missing"><option value="all">All records</option><option value="known">Reported only</option><option value="missing">Unknown only</option></select></label>
       </div><p id="db-metric-summary" class="db-muted"></p></details>
       <div id="db-visuals" class="db-visuals">
       <section id="db-map-panel" class="db-panel db-map-panel" aria-labelledby="db-map-title" hidden>
         <div class="db-panel-heading"><div><span class="db-eyebrow">GEOGRAPHIC COVERAGE</span><h2 id="db-map-title">Worldwide BESS locations</h2></div><div class="db-actions"><button id="db-map-world" type="button">World view</button><button id="db-map-fit" type="button">Fit locations</button></div></div>
         <p id="db-map-caption" class="db-muted" aria-live="polite"></p>
         <div id="db-map" role="region" aria-label="Interactive project map. Use arrow keys to pan, plus and minus to zoom, or tab to project markers."></div>
         <p class="db-muted db-map-note"><span class="db-map-legend"></span> Reported locations · Numbered markers group nearby projects. Overview boundaries; location accuracy is shown in project details. The map does not filter the table.</p>
       </section>
       <section class="db-panel db-chart-panel" aria-labelledby="db-chart-title">
         <span class="db-eyebrow">CATALOGUE BREAKDOWN</span>
         <h2 id="db-chart-title">Compare groups</h2>
         <div class="db-controls"><label>Group by<select id="db-group"></select></label><label>Measure<select id="db-aggregation"><option value="count">Record count</option><option value="mean">Mean of numeric field</option><option value="sum">Sum of reported values</option></select></label></div>
         <p id="db-chart-caption"></p><div id="db-chart"></div>
       </section>
       </div>
       <section class="db-panel db-records-panel" aria-label="Filtered records">
         <div class="db-panel-heading"><h2>Explore records</h2><div class="db-actions"><button id="db-export" type="button">Export filtered CSV</button><a id="db-parquet" href="datasets/bess/projects.parquet" download>Full Parquet ↗</a></div></div>
         <details class="db-column-panel"><summary>Visible columns &amp; schema</summary><p>All schema columns are available, including fields with no reported values. Click a column heading to sort.</p><div class="db-actions"><button id="db-default-columns" type="button">Default columns</button><button id="db-all-columns" type="button">All columns</button></div><div id="db-columns" class="db-columns"></div></details>
         <div class="db-actions"><button id="db-prev" type="button">Previous</button><span id="db-page" aria-live="polite"></span><button id="db-next" type="button">Next</button><label>Rows per page <select id="db-page-size"><option>25</option><option>50</option><option>100</option></select></label></div>
         <div class="db-table-wrap" tabindex="0" role="region" aria-label="Scrollable results"><table id="db-results"><caption>Filtered records — select Details for all fields and source evidence</caption><thead></thead><tbody></tbody></table></div>
       </section>
       <details class="db-panel db-snapshot-panel"><summary>Snapshot &amp; provenance</summary><p id="db-version"></p><p id="db-provenance" class="db-muted"></p><div class="db-actions"><a href="datasets/bess/manifest.json">Snapshot manifest</a><a href="datasets/bess/sources.json">Source registry</a><a href="datasets/bess/schema.json">Schema</a></div><p class="db-muted">Counts describe this catalogue, not market share. Unknown values are excluded from numeric statistics. MW and MWh remain separate. Ratings may have unspecified electrical or usable-energy bases. Status is dated source evidence, not live availability. Inspect capacity_scope, power_basis, energy_basis and quality_status before comparing projects.</p></details>
       <dialog id="db-detail" aria-labelledby="db-detail-title"><div class="db-actions"><h2 id="db-detail-title">Record details</h2><button id="db-close" type="button">Close</button><button id="db-export-record" type="button">Download record JSON</button></div><div id="db-detail-content"></div></dialog>
     </div>
   </div>
   <script type="module" src="_static/database-viewer.mjs"></script>

Reproduce and extend
--------------------

The dashboard shows compact KPIs for matching projects, **reported power (MW)**,
**reported energy (MWh)**, countries, mapped projects and energy-data coverage.
Both capacity totals include **all matching rows**, across every table page,
independently of the selected numeric field. Missing ratings remain unknown:
an all-unknown selection displays **Unknown**, and a reported zero stays zero.
These are catalogue sums across mixed statuses, dates, capacity scopes and
rating bases; they are not a deduplicated estimate of operating global capacity.
Use the status and rating-basis filters and inspect source evidence before analysis.

The world map uses source-reported, finite latitude/longitude pairs within
geographic bounds. Missing locations are never replaced by country or city
centroids; those records remain in the table and capacity totals. Search and
filters update the map, KPIs and records together. Map panning and table
pagination do not change the totals. The unfiltered catalogue opens in **World
view**; **Fit locations** zooms to the matching projects. Both map controls
preserve the filters. Numbered markers group nearby projects; open a group to browse every
record, including projects at identical coordinates.

Project popups show MW, MWh, rating bases, capacity scope, dated status and
location accuracy, with access to the full record and source evidence. The
bundled Leaflet 1.9.4 map reuses the same public-domain Natural Earth 5.1.1
country outlines (1:110m) as the solar viewer. It needs no external map tiles,
geocoding, CDN or API key. These boundaries are an overview, not site-level
imagery. If the map cannot load, the table, totals and exports remain usable.

Read the :doc:`BESS database guide <_generated/guides/bess-catalogue>` for scope,
conflicts, dates and download links. The
:doc:`BESS statistics example <auto_examples/database/plot_bess_projects>`
rebuilds the same Parquet snapshot offline and reports country coverage,
missing fields, dated statuses and source-qualified capacity comparisons.

.. code-block:: bash

   uv run python -m energy_data_retrieval.bess_catalogue validate
   uv run python -m energy_data_retrieval.bess_catalogue build --output artifacts/bess-v1
   uv run python examples/database/plot_bess_projects.py

All 60 schema fields are selectable, including currently unknown values.
Source URLs, field evidence and UTC creation/update/verification timestamps are
available in record details. Null is unknown; it is never silently converted to
zero. Each browser projection is bound to its exact Parquet file by SHA-256.
Source terms apply to exports; no blanket open license for source material is
asserted. No original articles, photographs or source spreadsheets are bundled.
