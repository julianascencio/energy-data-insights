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

   uv sync --locked --all-packages --extra imagery --group docs --python 3.13
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

Each section has a ``README.rst`` introduction and a generated gallery page.
The gallery and sidebar use the order Methods, Connectors, Analysis, configured
in ``docs/conf.py``. Keep support files beside their example (generation samples
live in ``examples/connectors/data/``), update download links and provenance paths,
and verify the clean documentation build. Clearly label synthetic inputs, use
deterministic seeds where needed, and avoid network calls during gallery builds.
The documentation extension retains redirects for the original flat example URLs.

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
