Interactive PV database
=======================

For batteries, open the :doc:`worldwide BESS projects viewer <bess-database-viewer>`.

Explore the published Parquet snapshot: all records, metadata, evidence and dates.
The browser loads one table at a time using a JSON projection generated directly
from the downloadable Parquet file; no external service or API key is required.

.. raw:: html

   <link rel="stylesheet" href="_static/database-viewer.css">
   <div id="pv-database" data-base="datasets/pv/">
     <p id="db-status" role="status" aria-live="polite">Loading database catalogue…</p>
     <button id="db-retry" type="button" hidden>Retry loading</button>
     <noscript>Enable JavaScript to use the viewer. Parquet downloads and runnable Python examples are linked below.</noscript>
     <div id="db-workspace" hidden>
       <div class="db-heading"><span class="db-eyebrow">ASVA · PV DATA EXPLORER</span><p id="db-version"></p></div>
       <div class="db-controls">
         <label>Table<select id="db-table"></select></label>
         <label class="db-wide">Search all metadata<input id="db-search" type="search" placeholder="Manufacturer, model, country, source…"></label>
         <label>Filter column<select id="db-filter-field"></select></label>
         <label>Exact value<select id="db-filter-value"></select></label>
         <label>Numeric field<select id="db-metric"></select></label>
         <label>Minimum<input id="db-min" type="number" step="any" placeholder="No minimum"></label>
         <label>Maximum<input id="db-max" type="number" step="any" placeholder="No maximum"></label>
         <label>Numeric availability<select id="db-missing"><option value="all">All records</option><option value="known">Reported only</option><option value="missing">Unknown only</option></select></label>
       </div>
       <div class="db-actions"><button id="db-reset" type="button">Reset filters</button><button id="db-export" type="button">Export filtered CSV</button><a id="db-parquet" href="datasets/pv/modules.parquet" download>Download full Parquet</a><a href="datasets/pv/manifest.json">Snapshot manifest</a><a href="datasets/pv/sources.json">Source registry</a><a href="datasets/pv/schema.json">Schema</a></div>
       <p id="db-provenance" class="db-muted"></p>
       <div id="db-stats" class="db-stats" aria-live="polite"></div>
       <p class="db-muted">Counts describe this catalogue, not market share. Unknown values are excluded from numeric statistics. AC, DC and unspecified capacity are separate fields. Sums include reported values only; they do not resolve phase overlap or mixed operating status.</p>
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

The :doc:`Database gallery <auto_examples/database/index>` contains runnable
examples for database inventory, field completeness, country coverage, separate
AC/DC capacity statistics and equipment queries. The
:doc:`database guide <_generated/guides/pv-catalogue>` explains provenance and
licensing. Dataset source licenses apply to exports, including CSVs.

The viewer is rebuilt on every documentation build, including future database
updates. It contains every row; pagination limits display only. Browser files
carry the exact source Parquet checksum and are verified before display. Null
fields display as **Unknown**; false and zero are retained. Each record exposes
source links, field-level evidence, UTC creation/update/verification dates and
nested extension metadata. CSV exports include the selected columns and all
matching rows, with empty cells for nulls and formula-like strings escaped for
spreadsheet safety. Record JSON and Parquet retain the original values.

The browser does not parse arbitrary uploaded Parquet files or run SQL. For full
Python analysis, download the Parquet files or rebuild them locally:

.. code-block:: bash

   uv sync --locked --all-packages --group docs
   uv run python -m energy_data_retrieval.pv_catalogue build --output artifacts/pv-analysis
   uv run python examples/database/plot_database_statistics.py
   uv run python examples/database/plot_project_coverage.py

.. code-block:: python

   from pathlib import Path
   from energy_analysis.pv_database import field_profile, grouped_statistics

   snapshot = Path("artifacts/pv-analysis")
   print(field_profile(snapshot / "modules.parquet"))
   print(grouped_statistics(snapshot / "projects.parquet", "country_code", "capacity_dc_mw"))

For local viewing, build the documentation and serve it over HTTP; browsers
restrict local ``file://`` fetches:

.. code-block:: bash

   uv run sphinx-build -b html docs docs/_build/html
   uv run python -m http.server 8000 --directory docs/_build/html

Open ``http://localhost:8000/database-viewer.html``. The entire generated site is
self-contained for this viewer; no CDN scripts, remote queries or uploads are used.
