Database
========

Explore the PV equipment database and worldwide PV/BESS project databases, then reproduce its statistics
from the same typed Parquet snapshots. Coverage grows with reviewed records;
these figures describe the catalogue, not global market shares.

.. button-ref:: /database-viewer
   :color: primary

   Open the interactive database viewer

.. button-ref:: /bess-database-viewer
   :color: primary

   Open worldwide BESS projects

The PV viewer includes all five tables: modules, inverters, trackers, combiner boxes
and projects. Search, filter, choose columns, inspect sources, compare groups,
and export filtered rows. It refreshes on every successful documentation build.

Download Python scripts or notebooks below. From the repository root, install
``uv sync --locked --all-packages --group docs`` and run, for example,
``uv run python examples/database/plot_database_statistics.py``. Each example
rebuilds its own temporary Parquet snapshot from committed records, offline.
For downloaded examples, run them from a repository checkout so the canonical
``catalogues/pv`` and ``catalogues/bess`` records are available.

The BESS viewer starts with 37 projects across 22 countries and a separate
60-field schema. Battery power (MW), stored energy (MWh), capacity scope,
chemistry, status dates and source conflicts are visible independently.

See the :doc:`database guide </_generated/guides/pv-catalogue>` for provenance,
column definitions, snapshot downloads and update rules.

.. button-ref:: /bess-oem-database-viewer
   :color: primary
   :outline:

   Explore BESS OEM products
