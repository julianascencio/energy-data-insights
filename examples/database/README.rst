Database
========

Explore the PV equipment and project database, then reproduce its statistics
from the same typed Parquet snapshots. Coverage grows with reviewed records;
these figures describe the catalogue, not global market shares.

.. button-ref:: /database-viewer
   :color: primary

   Open the interactive database viewer

The viewer includes all five tables: modules, inverters, trackers, combiner boxes
and projects. Search, filter, choose columns, inspect sources, compare groups,
and export filtered rows. It refreshes on every successful documentation build.

Download Python scripts or notebooks below. From the repository root, install
``uv sync --locked --all-packages --group docs`` and run, for example,
``uv run python examples/database/plot_database_statistics.py``. Each example
rebuilds its own temporary Parquet snapshot from committed records, offline.
For downloaded examples, run them from a repository checkout so the canonical
``catalogues/pv`` records are available.

See the :doc:`database guide </_generated/guides/pv-catalogue>` for provenance,
column definitions, snapshot downloads and update rules.
