"""Sphinx documentation, built from the installed uv workspace without live data."""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "docs/_ext"))

from project_docs import prepare_sources  # noqa: E402

project = "Energy Data Insights"
author = "Energy Data Insights contributors"
copyright = "2026, Energy Data Insights contributors"
release = tomllib.loads((ROOT / "pyproject.toml").read_text())["project"]["version"]
version = release

extensions = [
    "project_docs",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "myst_parser",
    "sphinxcontrib.mermaid",
    "sphinx_design",
    "sphinx_gallery.gen_gallery",
]
exclude_patterns = ["_build", "_ext", ".DS_Store", *prepare_sources(ROOT)]
source_suffix = {".rst": "restructuredtext", ".md": "markdown"}
master_doc = "index"
autodoc_typehints = "description"
autodoc_member_order = "bysource"
napoleon_google_docstring = True
napoleon_numpy_docstring = True
myst_enable_extensions = ["colon_fence", "dollarmath"]
myst_heading_anchors = 4
myst_fence_as_directive = ["mermaid"]

html_theme = "pydata_sphinx_theme"
templates_path = ["_templates"]
html_title = project
html_static_path = ["_static"]
html_css_files = ["energy.css"]
html_show_sourcelink = False
html_baseurl = "https://julianascencio.github.io/energy-data-insights/"
html_theme_options = {
    "github_url": "https://github.com/julianascencio/energy-data-insights",
    "navbar_align": "left",
    "show_prev_next": False,
    "show_toc_level": 2,
    "navigation_depth": 3,
    "header_links_before_dropdown": 5,
    "logo": {"text": "Energy Data Insights"},
}
sphinx_gallery_conf = {
    "examples_dirs": str(ROOT / "examples"),
    "gallery_dirs": "auto_examples",
    "filename_pattern": r"/plot_",
    "download_all_examples": False,
    "remove_config_comments": True,
    "abort_on_example_error": True,
    "subsection_order": [
        "../examples/methods",
        "../examples/connectors",
        "../examples/analysis",
    ],
    "nested_sections": True,
    "within_subsection_order": "FileNameSortKey",
    "reference_url": {},
    "capture_repr": (),
    "copyfile_regex": (
        r"(?:kgpv_worldwide|kgpv_canary|weather_risk|country_risk)_.*"
        r"\.(csv|json|geojson|tif)$"
    ),
}
