Development and publishing
==========================

.. toctree::
   :maxdepth: 1

   _generated/contributing
   _generated/guides/validation
   _generated/guides/performance
   _generated/guides/releases

Build the documentation
-----------------------

.. code-block:: bash

   uv sync --locked --all-packages --group imagery --group docs --python 3.13
   uv run --no-sync sphinx-build -W --keep-going -b html docs docs/_build/html
   uv run --no-sync python scripts/check_docs_links.py docs/_build/html
   python -m http.server 8000 --directory docs/_build/html

Open http://localhost:8000. The build executes every gallery example and treats
Sphinx warnings as errors. It needs installed dependencies but no live provider
requests or credentials. Theme assets and search are bundled with the site;
MathJax and Mermaid load from their standard CDNs to render equations and diagrams.

Edit existing Markdown guides in ``docs/`` and the package READMEs directly.
The build creates ignored copies under ``docs/_generated/``, rewrites their
relative links, and generates API pages from public modules. Do not edit those
copies.

Add executable examples as ``plot_*.py`` in the section that matches their purpose:

* ``examples/methods/``: focused tutorials for reusable calculations.
* ``examples/connectors/``: provider requests, parsing and data access.
* ``examples/analysis/``: applied workflows combining inputs, methods and outputs.
* ``examples/database/``: Parquet queries, catalogue statistics and data coverage.

The gallery has two category levels: **main sections**, then **topic subsections**.
``examples/index.rst`` links to the four main sections. Each section's
``index.rst`` links to its ``topic_*.rst`` pages; each topic links to its examples
through a thumbnail mini-gallery and a hidden toctree. These authored pages are
copied by Sphinx-Gallery using ``copyfile_regex`` in ``docs/conf.py``.
The sidebar and breadcrumbs use the same hierarchy.

When adding an example, register it in exactly one topic's mini-gallery and
toctree. For a new topic, add its card and toctree entry to the section index.
Keep category nesting to those two levels; individual examples are the leaves.
``tests/test_gallery_navigation.py`` checks that every runnable example is
reachable exactly once, with matching thumbnails and links. The category pages
contain navigation, while the example pages contain code and outputs.

Keep Python scripts and their support files at their established paths
(generation samples live in ``examples/connectors/data/``). Update download
links and provenance paths and verify the clean documentation build. Clearly
label synthetic inputs, use deterministic seeds where needed, and avoid network
calls during gallery builds. Existing example URLs, notebooks and download
bundles retain their paths, including redirects for the original flat gallery.

The Database viewer uses local JavaScript and generated JSON projections of the
published Parquet files. ``project_docs`` builds both together after a successful
HTML build, including local builds. Do not edit or commit the derived datasets.
Run ``node --test tests/js/test_database_viewer.mjs`` for browser calculation tests;
Python parity and missing-data tests live in ``analysis/tests/test_pv_database.py``.

GitHub Pages
------------

The ``Documentation`` workflow builds and checks the site on pull requests.
Only pushes to ``main`` and manual runs on ``main`` upload and deploy the Pages
artifact. Pull requests receive read-only repository permissions, never deployment
permissions. Concurrent pull-request builds cannot cancel production deployments.

The repository must use **Settings → Pages → Build and deployment → Source →
GitHub Actions**. Then merge a documentation change or run **Actions → Documentation
→ Run workflow** on ``main``. The public site is
https://julianascencio.github.io/energy-data-insights/.

If deployment reports that Pages is not enabled or returns a 404 from the Pages
API, check that setting first. No PyPI account or PyPI verification is needed
for documentation deployment. PyPI publishing remains a separate workflow.
