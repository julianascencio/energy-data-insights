"""Build documentation from the repository's existing guides and public modules."""

from __future__ import annotations

import os
import re
import shutil
from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TYPE_CHECKING
from urllib.parse import urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

if TYPE_CHECKING:
    from sphinx.application import Sphinx

REPOSITORY = "https://github.com/julianascencio/energy-data-insights"

# Only the original flat gallery pages need redirects. New examples live solely
# in their section, so future additions cannot accidentally claim a legacy URL.
LEGACY_EXAMPLES = {
    "methods": ("plot_ccya", "plot_daily_profiles", "plot_kgpv"),
    "connectors": (
        "plot_cds_plan",
        "plot_generation_aemo",
        "plot_generation_eia",
        "plot_generation_entsoe",
        "plot_generation_ree",
    ),
    "analysis": ("plot_kgpv_worldwide", "plot_soiling_snow_risk"),
}


def _legacy_gallery_pages(app: Sphinx) -> Iterator[tuple[str, dict[str, str], str]]:
    """Keep published example links valid after moving them into sections."""
    assert app.builder is not None
    for section, names in LEGACY_EXAMPLES.items():
        for name in names:
            old_page = f"auto_examples/{name}"
            new_page = f"auto_examples/{section}/{name}"
            yield (
                old_page,
                {
                    "section": section.title(),
                    "redirect_url": app.builder.get_relative_uri(old_page, new_page),
                    "canonical_url": (
                        f"{app.config.html_baseurl.rstrip('/')}/"
                        f"{app.builder.get_target_uri(new_page)}"
                    ),
                },
                "gallery_redirect.html",
            )

    old_page = "auto_examples/connectors/plot_pv_catalogue"
    new_page = "auto_examples/database/plot_pv_catalogue"
    yield (
        old_page,
        {
            "section": "Database",
            "redirect_url": app.builder.get_relative_uri(old_page, new_page),
            "canonical_url": (
                f"{app.config.html_baseurl.rstrip('/')}/{app.builder.get_target_uri(new_page)}"
            ),
        },
        "gallery_redirect.html",
    )


def _publish_pv_database(app: Sphinx, exception: Exception | None) -> None:
    """Publish one validated Parquet snapshot and its matching browser projections."""
    if exception is not None or app.builder is None or app.builder.format != "html":
        return
    from energy_analysis.pv_database import export_viewer_data
    from energy_data_retrieval.pv_catalogue import build_parquet

    root = Path(app.srcdir).parent
    destination = Path(app.outdir) / "datasets/pv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temporary:
        snapshot = Path(temporary) / "snapshot"
        build_parquet(root / "catalogues/pv", snapshot)
        export_viewer_data(snapshot)
        # Only generated files are copied. Works for clean and incremental builds;
        # canonical JSONL records and immutable user snapshots are never changed.
        shutil.copytree(snapshot, destination, dirs_exist_ok=True)


def _publish_bess_database(app: Sphinx, exception: Exception | None) -> None:
    """Publish the independent BESS schema through the shared database viewer."""
    if exception is not None or app.builder is None or app.builder.format != "html":
        return
    from energy_analysis.pv_database import export_viewer_data
    from energy_data_retrieval.bess_catalogue import build_parquet

    root = Path(app.srcdir).parent
    destination = Path(app.outdir) / "datasets/bess"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temporary:
        snapshot = Path(temporary) / "snapshot"
        build_parquet(root / "catalogues/bess", snapshot)
        export_viewer_data(snapshot)
        shutil.copytree(snapshot, destination, dirs_exist_ok=True)


def setup(app: Sphinx) -> dict[str, bool]:
    """Add lightweight HTML redirects without duplicate gallery source pages."""
    app.connect("html-collect-pages", _legacy_gallery_pages)
    app.connect("build-finished", _publish_pv_database)
    app.connect("build-finished", _publish_bess_database)
    app.connect("build-finished", _publish_bess_oem_database)
    return {"parallel_read_safe": True, "parallel_write_safe": True}


def _publish_bess_oem_database(app: Sphinx, exception: Exception | None) -> None:
    """Publish product configurations separately from installed project capacity."""
    if exception is not None or app.builder is None or app.builder.format != "html":
        return
    from energy_analysis.pv_database import export_viewer_data
    from energy_data_retrieval.bess_oem_catalogue import build_parquet

    root = Path(app.srcdir).parent
    destination = Path(app.outdir) / "datasets/bess_oem"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=destination.parent) as temporary:
        snapshot = Path(temporary) / "snapshot"
        build_parquet(root / "catalogues/bess_oem", snapshot)
        export_viewer_data(snapshot)
        shutil.copytree(snapshot, destination, dirs_exist_ok=True)


def _generation_assets(root: Path) -> None:
    """Copy small attributed samples and bundle runnable gallery downloads."""
    examples = root / "examples/connectors"
    gallery = root / "docs/auto_examples/connectors"
    samples = sorted((examples / "data").glob("generation_*"))
    if not samples:
        return
    destination = gallery / "data"
    destination.mkdir(parents=True, exist_ok=True)
    for sample in samples:
        shutil.copyfile(sample, destination / sample.name)
    scripts = sorted(examples.glob("plot_generation_*.py"))
    with ZipFile(gallery / "generation_examples.zip", "w", compression=ZIP_DEFLATED) as bundle:
        for path in [*scripts, *samples]:
            bundle.write(path, arcname=path.relative_to(examples))


def _pvgis_assets(root: Path) -> None:
    """Bundle complete PVGIS captures with their provenance and runnable examples."""
    examples = root / "examples/connectors"
    gallery = root / "docs/auto_examples/connectors"
    destination = gallery / "data"
    destination.mkdir(parents=True, exist_ok=True)
    samples = sorted((examples / "data").glob("pvgis_*.json"))
    for sample in samples:
        shutil.copyfile(sample, destination / sample.name)
    with ZipFile(gallery / "pvgis_examples.zip", "w", compression=ZIP_DEFLATED) as bundle:
        for path in [*sorted(examples.glob("plot_pvgis_*.py")), *samples]:
            bundle.write(path, arcname=path.relative_to(examples))


def _terrain_assets(root: Path) -> None:
    """Bundle native terrain crops, provenance and the runnable offline map."""
    examples = root / "examples/connectors"
    gallery = root / "docs/auto_examples/connectors"
    destination = gallery / "data"
    destination.mkdir(parents=True, exist_ok=True)
    samples = sorted((examples / "data").glob("terrain_*"))
    for sample in samples:
        shutil.copyfile(sample, destination / sample.name)
    with ZipFile(gallery / "terrain_examples.zip", "w", compression=ZIP_DEFLATED) as bundle:
        for path in [examples / "plot_terrain_sources.py", *samples]:
            bundle.write(path, arcname=path.relative_to(examples))


def _imagery_assets(root: Path) -> None:
    """Bundle native satellite crops, complete STAC receipts and offline usage."""
    examples = root / "examples/connectors"
    gallery = root / "docs/auto_examples/connectors"
    destination = gallery / "data"
    destination.mkdir(parents=True, exist_ok=True)
    samples = sorted((examples / "data").glob("imagery_*"))
    for sample in samples:
        shutil.copyfile(sample, destination / sample.name)
    with ZipFile(
        gallery / "satellite_imagery_examples.zip", "w", compression=ZIP_DEFLATED
    ) as bundle:
        for path in [examples / "plot_satellite_imagery.py", *samples]:
            bundle.write(path, arcname=path.relative_to(examples))


def _candelaria_assets(root: Path) -> None:
    """Keep the Icor farm example runnable with its real attributed inputs."""
    examples = root / "examples/connectors"
    gallery = root / "docs/auto_examples/connectors"
    destination = gallery / "data"
    destination.mkdir(parents=True, exist_ok=True)
    samples = sorted((examples / "data").glob("candelaria_*"))
    for sample in samples:
        shutil.copyfile(sample, destination / sample.name)
    with ZipFile(gallery / "candelaria_solar_farm.zip", "w", compression=ZIP_DEFLATED) as bundle:
        for path in [examples / "plot_candelaria_solar_farm.py", *samples]:
            bundle.write(path, arcname=path.relative_to(examples))


def _module_counting_assets(root: Path) -> None:
    """Bundle the runnable counting example, exact imagery and computed review exports."""
    import json
    from tempfile import TemporaryDirectory

    from energy_analysis.module_counting import count_rendered_site
    from energy_analysis.module_counting.reports import export_counting_study

    examples = root / "examples"
    source = examples / "connectors/data"
    gallery = root / "docs/auto_examples/analysis"
    destination = gallery / "data"
    destination.mkdir(parents=True, exist_ok=True)
    samples = sorted(source.glob("candelaria_*"))
    for sample in samples:
        shutil.copyfile(sample, destination / sample.name)
    site = json.loads((source / "candelaria_site.json").read_text())
    study = count_rendered_site(source / "candelaria_pnoa.png", site["footprint"])
    with TemporaryDirectory() as temporary:
        exports = export_counting_study(study, Path(temporary) / "results")
        with ZipFile(
            gallery / "candelaria_module_counting.zip", "w", compression=ZIP_DEFLATED
        ) as bundle:
            script = examples / "analysis/plot_candelaria_module_counting.py"
            bundle.write(script, arcname=script.name)
            original = examples / "connectors/plot_candelaria_solar_farm.py"
            bundle.write(original, arcname=original.name)
            bundle.writestr(
                "README.txt",
                "Automatic PV module counting — Planta Icor\n\n"
                "Use the current energy-data-insights workspace:\n"
                "https://github.com/julianascencio/energy-data-insights\n"
                "From its root: uv sync --locked --all-packages\n"
                "Then: uv run --no-sync python "
                "/path/to/extracted/plot_candelaria_module_counting.py\n\n"
                "The counting example supports Python 3.12/3.13 and runs offline.\n"
                "results/ contains candidate CSV, GeoJSON and provenance JSON.\n"
                "Counts are experimental; review flags and exclusions are not ground truth.\n"
                "data/candelaria_README.txt preserves all source credits and licences.\n"
                "The included earlier plot_candelaria_solar_farm.py imagery tutorial needs\n"
                "Python 3.13 and the optional imagery workspace group.\n",
            )
            for sample in samples:
                bundle.write(sample, arcname=f"data/{sample.name}")
            for output in sorted(exports.iterdir()):
                bundle.write(output, arcname=f"results/{output.name}")


def _chile_module_assets(root: Path) -> None:
    """Ship both offline Chile audits, exact inputs and explicit unresolved results."""
    from tempfile import TemporaryDirectory

    from energy_analysis.module_counting.chile import export_chile_audit

    source = root / "examples/analysis/data/chile_modules"
    gallery = root / "docs/auto_examples/analysis"
    shutil.copytree(source, gallery / "data/chile_modules", dirs_exist_ok=True)
    with TemporaryDirectory() as temporary:
        exports = export_chile_audit(source, Path(temporary) / "results")
        with ZipFile(
            gallery / "chile_module_counting.zip", "w", compression=ZIP_DEFLATED
        ) as bundle:
            for name in (
                "plot_chile_largest_module_counting.py",
                "plot_chile_smallest_module_counting.py",
            ):
                bundle.write(root / "examples/analysis" / name, arcname=name)
            for path in sorted(source.iterdir()):
                bundle.write(path, arcname=f"data/chile_modules/{path.name}")
            for path in sorted(exports.iterdir()):
                bundle.write(path, arcname=f"results/{path.name}")
            bundle.write(root / "docs/chile-module-counting.md", arcname="EVIDENCE.md")
            bundle.writestr(
                "README.txt",
                "Chile module-count audits — CEME1 and Concón\n\n"
                "Use https://github.com/julianascencio/energy-data-insights\n"
                "From the repository root: uv sync --locked --all-packages\n"
                "Then: uv run --no-sync python "
                "/path/to/extracted/plot_chile_largest_module_counting.py\n"
                "And: uv run --no-sync python "
                "/path/to/extracted/plot_chile_smallest_module_counting.py\n"
                "Python 3.12/3.13; both scripts run offline.\n"
                "Read EVIDENCE.md and data/chile_modules/README.txt "
                "for attribution and limitations.\n"
                "The 882,720 reference is an engineering inventory, not an image count.\n"
                "Both whole-plant image counts remain unresolved.\n",
            )


def _rengo_module_assets(root: Path) -> None:
    """Bundle the near-Rengo pilot and its complete, scoped visual audit."""
    from tempfile import TemporaryDirectory

    from energy_analysis.module_counting.rengo import export_rengo_study

    source = root / "examples/analysis/data/rengo_modules"
    gallery = root / "docs/auto_examples/analysis"
    shutil.copytree(source, gallery / "data/rengo_modules", dirs_exist_ok=True)
    with TemporaryDirectory() as temporary:
        exports = export_rengo_study(source, Path(temporary) / "results")
        with ZipFile(
            gallery / "rengo_module_counting.zip", "w", compression=ZIP_DEFLATED
        ) as bundle:
            script = root / "examples/analysis/plot_rengo_module_counting.py"
            bundle.write(script, arcname=script.name)
            bundle.write(root / "docs/rengo-module-counting.md", arcname="EVIDENCE.md")
            for path in sorted(source.iterdir()):
                bundle.write(path, arcname=f"data/rengo_modules/{path.name}")
            for path in sorted(exports.iterdir()):
                bundle.write(path, arcname=f"results/{path.name}")
            bundle.writestr(
                "README.txt",
                "El Mirlo near Rengo — experimental module candidates\n\n"
                "Use https://github.com/julianascencio/energy-data-insights\n"
                "From its root: uv sync --locked --all-packages\n"
                "Then: uv run --no-sync python "
                "/path/to/extracted/plot_rengo_module_counting.py\n"
                "Python 3.12/3.13; no network calls are required.\n"
                "Read EVIDENCE.md and data/rengo_modules/README.txt.\n"
                "Both initial and corrected AI visual annotations are included.\n"
                "The small same-image audit is not independent ground truth.\n"
                "The count covers a partial block, not the whole plant.\n",
            )


def _rengo_3d_assets(root: Path) -> None:
    """Build an offline viewer and complete reproducibility bundle from pinned inputs."""
    from tempfile import TemporaryDirectory

    from energy_analysis.site_3d import export_site_scene
    from energy_analysis.site_3d.rengo import build_rengo_scene

    examples = root / "examples/analysis"
    gallery = root / "docs/auto_examples/analysis"
    study = build_rengo_scene(examples / "data/rengo_modules", examples / "data/rengo_3d")
    for name in ("rengo_modules", "rengo_3d"):
        shutil.copytree(examples / "data" / name, gallery / "data" / name, dirs_exist_ok=True)
    with TemporaryDirectory() as temporary:
        exports = export_site_scene(
            study["scene"],
            Path(temporary) / "results",
            title="El Mirlo · southern inspection block",
            provenance={
                "terrain": study["terrain_source"],
                "configuration": study["configuration"],
                "counting": study["counting"]["manifest"],
            },
            attribution=study["terrain_source"]["notice"],
            evidence_note=study["configuration"]["assumptions_note"],
        )
        shutil.copyfile(exports / "viewer.html", root / "docs/_static/rengo_site_3d.html")
        with ZipFile(gallery / "rengo_site_3d.zip", "w", compression=ZIP_DEFLATED) as bundle:
            bundle.write(examples / "plot_rengo_site_3d.py", arcname="plot_rengo_site_3d.py")
            bundle.write(root / "docs/pv-site-3d.md", arcname="METHOD.md")
            bundle.write(
                root / "scripts/prepare_rengo_3d.py",
                arcname="repository_scripts/prepare_rengo_3d.py",
            )
            for name in ("rengo_modules", "rengo_3d"):
                for path in sorted((examples / "data" / name).iterdir()):
                    bundle.write(path, arcname=f"data/{name}/{path.name}")
            for path in sorted(exports.iterdir()):
                bundle.write(path, arcname=f"results/{path.name}")
            bundle.writestr(
                "README.txt",
                "El Mirlo 3D continuation — candidate surfaces and assumed mounting\n\n"
                "Open results/viewer.html directly in a WebGL-capable browser.\n"
                "Import results/site.obj with metre units and Z up; "
                "retain site.mtl and scene.json.\n"
                "For Python reproduction use https://github.com/julianascencio/energy-data-insights\n"
                "From its root: uv sync --locked --all-packages\n"
                "Then: uv run --no-sync python /path/to/extracted/plot_rengo_site_3d.py\n"
                "Python 3.12/3.13; no live calls. Read METHOD.md and both data READMEs.\n"
                "The recapture script under repository_scripts is a source copy to run from\n"
                "the repository, not a standalone capture utility.\n"
                "This is a partial block, not the whole plant, and not an as-built survey.\n"
                "The source imagery's existing attribution/terms remain in data/rengo_modules.\n",
            )


def _climate_assets(root: Path) -> None:
    """Bundle source samples and existing regional context for offline execution."""
    examples = root / "examples/analysis"
    gallery = root / "docs/auto_examples/analysis"
    gallery.mkdir(parents=True, exist_ok=True)
    samples = [
        *sorted(examples.glob("climate_*")),
        *sorted(examples.glob("plot_climate_*.py")),
        *sorted(examples.glob("kgpv_canary_*.tif")),
        examples / "kgpv_canary_provenance.json",
        examples / "kgpv_chile_mainland.geojson",
    ]
    with ZipFile(gallery / "climate_examples.zip", "w", compression=ZIP_DEFLATED) as bundle:
        for path in samples:
            bundle.write(path, arcname=path.name)


def _site_and_degradation_assets(root: Path) -> None:
    """Keep both new tutorials runnable after extracting their complete bundles."""
    examples = root / "examples/analysis"
    gallery = root / "docs/auto_examples/analysis"
    gallery.mkdir(parents=True, exist_ok=True)
    groups = {
        "degradation_examples.zip": [
            *sorted(examples.glob("degradation_*.csv")),
            *sorted(examples.glob("degradation_*.json")),
            examples / "climate_world_boundaries.geojson",
            examples / "plot_degradation_rates.py",
        ],
        "site_climate_examples.zip": [
            *sorted(examples.glob("site_climate_*.csv")),
            examples / "site_climate_provenance.json",
            examples / "climate_jrc_model.json",
            examples / "climate_PVCZ_LICENSE.txt",
            examples / "plot_site_climate_profile.py",
        ],
    }
    for name, paths in groups.items():
        with ZipFile(gallery / name, "w", compression=ZIP_DEFLATED) as bundle:
            for path in paths:
                bundle.write(path, arcname=path.name)


def prepare_sources(root: Path) -> list[str]:
    """Reuse the Markdown source of truth, translating its relative links for Sphinx."""
    docs = root / "docs"
    mapping = {path: docs / "_generated/guides" / path.name for path in docs.glob("*.md")}
    mapping.update(
        {
            root / "data-retrieval/README.md": docs / "_generated/packages/retrieval.md",
            root / "methods/README.md": docs / "_generated/packages/methods.md",
            root / "analysis/README.md": docs / "_generated/packages/analysis.md",
            root / "analysis/examples/ccya/README.md": docs / "_generated/studies/ccya.md",
            root / "analysis/src/energy_analysis/degradation/README.md": (
                docs / "_generated/studies/degradation.md"
            ),
            root / "data-retrieval/src/energy_data_retrieval/sources/cds/README.md": (
                docs / "_generated/guides/cds.md"
            ),
            root / "CONTRIBUTING.md": docs / "_generated/contributing.md",
        }
    )
    for source, target in mapping.items():

        def replace_link(match: re.Match[str], source: Path = source, target: Path = target) -> str:
            url = match.group(1)
            parsed = urlsplit(url)
            if parsed.scheme or parsed.netloc or not parsed.path:
                return match.group(0)
            resolved = (source.parent / parsed.path).resolve()
            suffix = f"#{parsed.fragment}" if parsed.fragment else ""
            if resolved in mapping:
                destination = Path(os.path.relpath(mapping[resolved], target.parent)).as_posix()
            else:
                destination = f"{REPOSITORY}/blob/main/{resolved.relative_to(root).as_posix()}"
            return f"]({destination}{suffix})"

        lines = []
        fence = ""
        for line in source.read_text(encoding="utf-8").splitlines(keepends=True):
            stripped = line.lstrip()
            if stripped.startswith(("```", "~~~")):
                marker = stripped[:3]
                fence = "" if fence == marker else fence if fence else marker
                lines.append(line)
            else:
                lines.append(line if fence else re.sub(r"\]\(([^\s)]+)\)", replace_link, line))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("".join(lines), encoding="utf-8")

    for folder, package in (
        ("data-retrieval", "energy_data_retrieval"),
        ("methods", "energy_methods"),
        ("analysis", "energy_analysis"),
    ):
        package_dir = root / folder / "src" / package
        modules = []
        for path in sorted(package_dir.rglob("*.py")):
            if path.stem.startswith("_") or path.stem.endswith("cli"):
                continue
            module = ".".join(path.relative_to(package_dir.parent).with_suffix("").parts)
            modules.append(module)
            page = docs / "_generated/api" / f"{module}.rst"
            page.parent.mkdir(parents=True, exist_ok=True)
            page.write_text(
                f"{module}\n{'=' * len(module)}\n\n"
                f".. automodule:: {module}\n"
                "   :members:\n   :undoc-members:\n   :show-inheritance:\n",
                encoding="utf-8",
            )
        index = docs / "_generated/api" / f"{package}.rst"
        index.write_text(
            f"{package}\n{'=' * len(package)}\n\n"
            ".. toctree::\n   :maxdepth: 1\n\n" + "".join(f"   {module}\n" for module in modules),
            encoding="utf-8",
        )
    _generation_assets(root)
    _pvgis_assets(root)
    _terrain_assets(root)
    _imagery_assets(root)
    _candelaria_assets(root)
    _module_counting_assets(root)
    _chile_module_assets(root)
    _rengo_module_assets(root)
    _rengo_3d_assets(root)
    _climate_assets(root)
    _site_and_degradation_assets(root)
    # Sphinx-Gallery hashes the script, not its catalogue inputs. This small
    # data-driven example must rerun when records, sources or the schema change.
    (docs / "auto_examples/database/plot_bess_projects.py.md5").unlink(missing_ok=True)
    (docs / "auto_examples/database/plot_bess_oem_catalogue.py.md5").unlink(missing_ok=True)
    return [path.name for path in docs.glob("*.md")]
