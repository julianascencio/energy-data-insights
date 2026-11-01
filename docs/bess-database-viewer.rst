Worldwide BESS project database
===============================

Search battery energy storage projects, filter country/status/chemistry, compare
reported MW and MWh, inspect field-level sources and export selected rows.
This catalogue covers 1,113 project and plant records in 27 countries.
U.S. and UK inventory subsets dominate the coverage; counts are not a census
or a ranking of the world's installed capacity.

Browse the :doc:`BESS OEM products <bess-oem-database-viewer>`,
:doc:`PV database <database-viewer>` or
:doc:`Database gallery <auto_examples/database/index>`.

.. raw:: html

   <link rel="stylesheet" href="_static/database-viewer.css">
   <div id="bess-database" data-database="bess" data-base="datasets/bess/">
     <p id="db-status" role="status" aria-live="polite">Loading database catalogue…</p>
     <button id="db-retry" type="button" hidden>Retry loading</button>
     <noscript>Enable JavaScript to use the viewer. Parquet downloads and runnable Python examples are linked below.</noscript>
     <div id="db-workspace" hidden>
       <div class="db-heading"><span class="db-eyebrow">ASVA · BESS PROJECT EXPLORER</span><p id="db-version"></p></div>
       <div class="db-controls">
         <label>Table<select id="db-table"></select></label>
         <label class="db-wide">Search all metadata<input id="db-search" type="search" placeholder="Project, country, chemistry, owner, source…"></label>
         <label>Filter column<select id="db-filter-field"></select></label>
         <label>Exact value<select id="db-filter-value"></select></label>
         <label>Numeric field<select id="db-metric"></select></label>
         <label>Minimum<input id="db-min" type="number" step="any" placeholder="No minimum"></label>
         <label>Maximum<input id="db-max" type="number" step="any" placeholder="No maximum"></label>
         <label>Numeric availability<select id="db-missing"><option value="all">All records</option><option value="known">Reported only</option><option value="missing">Unknown only</option></select></label>
       </div>
       <div class="db-actions"><button id="db-reset" type="button">Reset filters</button><button id="db-export" type="button">Export filtered CSV</button><a id="db-parquet" href="datasets/bess/projects.parquet" download>Download full Parquet</a><a href="datasets/bess/manifest.json">Snapshot manifest</a><a href="datasets/bess/sources.json">Source registry</a><a href="datasets/bess/schema.json">Schema</a></div>
       <p id="db-provenance" class="db-muted"></p>
       <div id="db-stats" class="db-stats" aria-live="polite"></div>
       <p class="db-muted">Counts describe this catalogue, not market share. Unknown values are excluded from numeric statistics. MW is battery power; MWh is stored energy. Ratings may have unspecified electrical or usable-energy bases. Status is dated source evidence, not live availability. Sums include reported values across mixed statuses and dates; inspect capacity_scope and quality_status before comparing projects.</p>
       <details class="db-panel"><summary>Choose visible columns and inspect the schema</summary><p>All schema columns are available, including fields with no reported values. Click a column heading to sort.</p><div class="db-actions"><button id="db-default-columns" type="button">Default columns</button><button id="db-all-columns" type="button">All columns</button></div><div id="db-columns" class="db-columns"></div></details>
       <section class="db-panel" aria-labelledby="db-chart-title">
         <h2 id="db-chart-title">Compare groups</h2>
         <div class="db-controls"><label>Group by<select id="db-group"></select></label><label>Measure<select id="db-aggregation"><option value="count">Record count</option><option value="mean">Mean of numeric field</option><option value="sum">Sum of reported values</option></select></label></div>
         <p id="db-chart-caption"></p><div id="db-chart"></div>
       </section>
       <section class="db-panel" aria-label="Filtered records">
         <div class="db-actions"><button id="db-prev" type="button">Previous</button><span id="db-page" aria-live="polite"></span><button id="db-next" type="button">Next</button><label>Rows per page <select id="db-page-size"><option>25</option><option>50</option><option>100</option></select></label></div>
         <div class="db-table-wrap" tabindex="0" role="region" aria-label="Scrollable results"><table id="db-results"><caption>Filtered records — select Details for all fields and source evidence</caption><thead></thead><tbody></tbody></table></div>
       </section>
       <dialog id="db-detail" aria-labelledby="db-detail-title"><div class="db-actions"><h2 id="db-detail-title">Record details</h2><button id="db-close" type="button">Close</button><button id="db-export-record" type="button">Download record JSON</button></div><div id="db-detail-content"></div></dialog>
     </div>
   </div>
   <script type="module" src="_static/database-viewer.mjs"></script>

Reproduce and extend
--------------------

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
