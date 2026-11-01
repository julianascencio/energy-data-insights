Global BESS OEM product database
================================

Explore 75 product configurations and families from 27 suppliers, backed by
50 primary sources. Filter manufacturer, chemistry, architecture and source status;
compare qualified specifications, inspect per-field evidence and export CSV.

Return to the :doc:`BESS projects <bess-database-viewer>`,
:doc:`PV database <database-viewer>` or
:doc:`Database gallery <auto_examples/database/index>`.

.. raw:: html

   <link rel="stylesheet" href="_static/database-viewer.css">
   <div id="bess-oem-database" data-database="bess_oem" data-base="datasets/bess_oem/">
     <p id="db-status" role="status" aria-live="polite">Loading database catalogue…</p>
     <button id="db-retry" type="button" hidden>Retry loading</button>
     <noscript>Enable JavaScript to use the viewer. Parquet downloads and runnable Python examples are linked below.</noscript>
     <div id="db-workspace" hidden>
       <div class="db-heading"><span class="db-eyebrow">ASVA · BESS OEM EXPLORER</span><p id="db-version"></p></div>
       <div class="db-controls">
         <label>Table<select id="db-table"></select></label>
         <label class="db-wide">Search all metadata<input id="db-search" type="search" placeholder="Manufacturer, model, chemistry, cooling, source…"></label>
         <label>Filter column<select id="db-filter-field"></select></label>
         <label>Exact value<select id="db-filter-value"></select></label>
         <label>Numeric field<select id="db-metric"></select></label>
         <label>Minimum<input id="db-min" type="number" step="any" placeholder="No minimum"></label>
         <label>Maximum<input id="db-max" type="number" step="any" placeholder="No maximum"></label>
         <label>Numeric availability<select id="db-missing"><option value="all">All records</option><option value="known">Reported only</option><option value="missing">Unknown only</option></select></label>
       </div>
       <div class="db-actions"><button id="db-reset" type="button">Reset filters</button><button id="db-export" type="button">Export filtered CSV</button><a id="db-parquet" href="datasets/bess_oem/systems.parquet" download>Download full Parquet</a><a href="datasets/bess_oem/manifest.json">Snapshot manifest</a><a href="datasets/bess_oem/sources.json">Source registry</a><a href="datasets/bess_oem/schema.json">Schema</a></div>
       <p id="db-provenance" class="db-muted"></p>
       <div id="db-stats" class="db-stats" aria-live="polite"></div>
       <p class="db-muted">Counts describe researched configurations and families, not market share. Product units have different boundaries: inspect capacity_scope, energy_basis and energy_boundary. Active MW and apparent MVA are separate. Family ranges stay in extensions; preliminary and historical documents are labelled. Manufacturer claims are not independently validated performance or certifications.</p>
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

Read the :doc:`OEM database guide <_generated/guides/bess-oem-catalogue>` and
run the :doc:`OEM analysis example <auto_examples/database/plot_bess_oem_catalogue>`.
All 73 fields, including unknown values, are available through column selection.

.. code-block:: bash

   uv run python -m energy_data_retrieval.bess_oem_catalogue validate
   uv run python -m energy_data_retrieval.bess_oem_catalogue build --output artifacts/bess-oem-v1
   uv run python examples/database/plot_bess_oem_catalogue.py

Source terms travel with exports. JSONL is canonical; browser data is generated
from the exact Parquet snapshot and checked by SHA-256. Dates record research
activity, not product launch, delivery availability or physical verification.
