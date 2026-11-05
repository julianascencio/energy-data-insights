Global Hydropower Database
==========================

Explore attributed historical plant records worldwide. The first WRI baseline is not a current operating census. Pumped storage remains unknown unless verified.

.. raw:: html

   <link rel="stylesheet" href="_static/vendor/leaflet/leaflet.css">
   <link rel="stylesheet" href="_static/database-viewer.css">
   <div id="hydro-database" data-database="hydro" data-base="datasets/hydro/">
     <p id="db-status" role="status" aria-live="polite">Loading database catalogue…</p>
     <button id="db-retry" type="button" hidden>Retry loading</button>
     <noscript>Enable JavaScript to use the viewer. Parquet downloads and runnable Python examples are linked below.</noscript>
     <div id="db-workspace" hidden>
       <div class="db-heading"><div><span class="db-eyebrow">ASVA / ENERGY DATA INSIGHTS</span><h2 id="db-title">Hydropower Plants</h2><p>Explore the global catalogue. Follow the evidence.</p></div><span class="db-snapshot-badge">Published snapshot</span></div>
       <div id="db-stats" class="db-stats" aria-label="Filtered catalogue statistics" aria-live="polite"></div>
       <p class="db-muted db-capacity-note">Generating and pumping MW remain separate by lifecycle and technology. Historical, aggregate and unresolved scopes are excluded. Unknown is not zero.</p>
       <div class="db-controls db-primary-controls">
         <label>Table<select id="db-table"></select></label>
         <label class="db-wide">Search all metadata<input id="db-search" type="search" placeholder="Search projects, countries, owners, sources…"></label>
         <button id="db-reset" type="button">Reset filters</button>
       </div>
       <details class="db-panel db-filter-panel"><summary>Refine results <span>Category, capacity range &amp; data availability</span></summary><div class="db-controls">
         <label>Filter column<select id="db-filter-field"></select></label>
         <label>Exact value<select id="db-filter-value"></select></label>
         <label>Numeric field<select id="db-metric"></select></label>
         <label>Minimum<input id="db-min" type="number" step="any" placeholder="No minimum"></label>
         <label>Maximum<input id="db-max" type="number" step="any" placeholder="No maximum"></label>
         <label>Numeric availability<select id="db-missing"><option value="all">All records</option><option value="known">Reported only</option><option value="missing">Unknown only</option></select></label>
       </div><p id="db-metric-summary" class="db-muted"></p></details>
       <div id="db-visuals" class="db-visuals">
       <section id="db-map-panel" class="db-panel db-map-panel" aria-labelledby="db-map-title" hidden>
         <div class="db-panel-heading"><div><span class="db-eyebrow">GEOGRAPHIC COVERAGE</span><h2 id="db-map-title">Project locations</h2></div><button id="db-map-fit" type="button">Fit locations</button></div>
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
         <div class="db-panel-heading"><h2>Explore records</h2><div class="db-actions"><button id="db-export" type="button">Export filtered CSV</button><a id="db-parquet" href="datasets/hydro/projects.parquet" download>Full Parquet ↗</a></div></div>
         <details class="db-column-panel"><summary>Visible columns &amp; schema</summary><p>All schema columns are available, including fields with no reported values. Click a column heading to sort.</p><div class="db-actions"><button id="db-default-columns" type="button">Default columns</button><button id="db-all-columns" type="button">All columns</button></div><div id="db-columns" class="db-columns"></div></details>
         <div class="db-actions"><button id="db-prev" type="button">Previous</button><span id="db-page" aria-live="polite"></span><button id="db-next" type="button">Next</button><label>Rows per page <select id="db-page-size"><option>25</option><option>50</option><option>100</option></select></label></div>
         <div class="db-table-wrap" tabindex="0" role="region" aria-label="Scrollable results"><table id="db-results"><caption>Filtered records — select Details for all fields and source evidence</caption><thead></thead><tbody></tbody></table></div>
       </section>
       <details class="db-panel db-snapshot-panel"><summary>Snapshot &amp; provenance</summary><p id="db-version"></p><p id="db-provenance" class="db-muted"></p><div class="db-actions"><a href="datasets/hydro/manifest.json">Snapshot manifest</a><a href="datasets/hydro/sources.json">Source registry</a><a href="datasets/hydro/schema.json">Schema</a></div><p class="db-muted">Counts describe this catalogue, not market share. Unknown values are excluded from numeric statistics. Historical inventory capacity is not current operating capacity. Equipment ratings are not deployment evidence.</p></details>
       <dialog id="db-detail" aria-labelledby="db-detail-title"><div class="db-actions"><h2 id="db-detail-title">Record details</h2><button id="db-close" type="button">Close</button><button id="db-export-record" type="button">Download record JSON</button></div><div id="db-detail-content"></div></dialog>
     </div>
   </div>
   <script type="module" src="_static/database-viewer.mjs"></script>

Reproduce and interpret
-----------------------

See the :doc:`evidence guide <_generated/guides/hydro-catalogue>` and
:doc:`runnable gallery <auto_examples/database/plot_hydro_catalogue>`.

.. code-block:: bash

   uv run python -m energy_data_retrieval.hydro_catalogue validate
   uv run python -m energy_data_retrieval.hydro_catalogue build --output artifacts/hydro-v1
   uv run python examples/database/plot_hydro_catalogue.py

The viewer publishes after merge and a successful Pages deployment.
