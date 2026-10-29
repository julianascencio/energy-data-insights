Quickstart
==========

Run these commands from a source checkout after :doc:`installation`.
The first two workflows use synthetic data and require no provider accounts.

Generate a fleet dashboard
--------------------------

.. code-block:: bash

   uv run --no-sync energy-chile demo --output artifacts/demo --reports

Open ``artifacts/demo/results/reports/index.html``. The pipeline preserves
training/holdout boundaries, comparison coverage, input provenance and the
synthetic label. It does not download Chilean production data.

Run the applied CCYA case
-------------------------

.. code-block:: bash

   uv run --no-sync energy-ccya demo --output artifacts/ccya-demo

This follows the thesis case-study structure: 50 years, seven illustrative
paths, four degradation assumptions and 25/50-year comparisons. The
:doc:`applied case guide <_generated/studies/ccya>` explains the output files,
original data-access limits and the real-data configuration.

Plan a CDS download offline
---------------------------

.. code-block:: python

   from datetime import date
   from energy_data_retrieval.sources.cds.era5 import era5_requests

   requests = era5_requests(
       date(2020, 1, 1), date(2020, 2, 29),
       variables=["2m_temperature", "surface_solar_radiation_downwards"],
       area=(29.0, -17.0, 28.0, -16.0),  # north, west, south, east
   )
   print(len(requests))  # two monthly requests; nothing downloaded

Use the :doc:`provider guide <_generated/packages/retrieval>` for actual retrieval.
Downloads retain native units and timestamps; preparing analysis inputs is an
explicit step, especially for accumulated radiation and climate-model calendars.

Next steps
----------

* :doc:`user-guide`: provider contracts and scientific assumptions.
* :doc:`auto_examples/index`: executable, downloadable Python examples.
* :doc:`api`: function signatures and source-linked reference pages.
