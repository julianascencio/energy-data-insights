Installation
============

From source
-----------

Python 3.12 and 3.13 are tested. Install uv 0.13.4 or later and run:

.. code-block:: bash

   git clone https://github.com/julianascencio/energy-data-insights.git
   cd energy-data-insights
   uv sync --locked --all-packages
   uv run --no-sync energy-retrieve --help

The workspace installs ``energy-data-retrieval``, ``energy-methods`` and
``energy-analysis`` together, using the checked-in lockfile.

Optional providers
------------------

For direct Copernicus Climate Data Store access:

.. code-block:: bash

   uv sync --locked --all-packages --extra cds

See the :doc:`CDS guide <_generated/guides/cds>` for credentials and dataset terms.
Request planning works without a token. Actual downloads need the optional
SDK, an external token and accepted dataset terms. Never commit credentials.

The separate native Earthmover ERA5 source uses the ``era5-native`` extra; see
the :doc:`provider guide <_generated/packages/retrieval>` for its access contract.

PyPI releases
-------------

Once the corresponding releases have been published, use:

.. code-block:: bash

   python -m pip install energy-data-retrieval
   python -m pip install energy-methods
   python -m pip install energy-analysis

Installing ``energy-analysis`` also installs its two sibling dependencies.
Availability depends on completed releases; this page does not imply that
the initial PyPI publication has already happened.
See :doc:`release tags and Trusted Publishing <_generated/guides/releases>`.
