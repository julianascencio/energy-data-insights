"""Keep required attribution and generated citation formats consistent offline."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from dataclasses import FrozenInstanceError
from importlib import import_module
from importlib.resources import files
from pathlib import Path

import pytest

from energy_methods.references import (
    PRIMARY_REFERENCE_ID,
    REFERENCES,
    citation_cff,
    get_references,
    references_bibtex,
    references_markdown,
)


def test_preferred_citation_is_verified_thesis_with_no_fabricated_doi() -> None:
    thesis = REFERENCES[0]
    assert thesis.id == PRIMARY_REFERENCE_ID
    assert thesis.authors == ("Ascencio Vásquez, Julián Andrés",)
    assert thesis.year == 2021
    assert thesis.doi is None
    assert thesis.institution == "University of Ljubljana, Faculty of Electrical Engineering"
    preferred = citation_cff()["preferred-citation"]
    assert isinstance(preferred, dict)
    assert preferred["type"] == "thesis"
    assert "doi" not in preferred
    assert preferred["authors"] == [
        {"family-names": "Ascencio Vásquez", "given-names": "Julián Andrés"}
    ]


def test_reference_selection_preserves_thesis_order_and_rejects_unknown_ids() -> None:
    selected = get_references(["ke_2017_lightgbm", "ascencio_vasquez_2021_tdp"])
    assert [reference.id for reference in selected] == [
        PRIMARY_REFERENCE_ID,
        "ascencio_vasquez_2021_tdp",
        "ke_2017_lightgbm",
    ]
    assert get_references([]) == (REFERENCES[0],)
    with pytest.raises(ValueError, match="Unknown reference IDs"):
        get_references(["invented_paper"])
    with pytest.raises(FrozenInstanceError):
        selected[0].__setattr__("year", 2023)
    copy = selected[0].as_dict()
    copy["year"] = 2023
    assert selected[0].year == 2021


def test_catalogue_is_packaged_unique_and_maps_to_real_repository_components() -> None:
    root = Path(__file__).resolve().parents[2]
    raw = json.loads(files("energy_methods").joinpath("references.json").read_text("utf-8"))
    assert len(raw) == len(REFERENCES)
    ids = [reference.id for reference in REFERENCES]
    assert len(ids) == len(set(ids))
    for reference in REFERENCES:
        assert re.fullmatch(r"[a-z0-9_]+", reference.id)
        assert reference.title and reference.authors and reference.note and reference.used_by
        assert reference.url.startswith("https://")
        assert all((root / path).exists() for path in reference.used_by)
        if reference.doi:
            assert re.fullmatch(r"10\.\d{4,9}/\S+", reference.doi)
    assert {reference.role for reference in REFERENCES} >= {
        "primary",
        "implemented",
        "software",
        "standard",
        "data",
        "background",
    }


def test_exports_contain_each_key_once_and_keep_attribution_boundaries() -> None:
    bibtex = references_bibtex()
    markdown = references_markdown()
    for reference in REFERENCES:
        assert bibtex.count("{" + reference.id + ",\n") == 1
        assert markdown.count("### " + reference.id + "\n") == 1
    assert "causes remain unconfirmed" in markdown.lower()
    assert "Role:** background" in markdown
    assert "No thesis DOI has been verified" in markdown


def test_committed_citation_exports_have_no_drift() -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [sys.executable, "scripts/check_citations.py"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads((root / "CITATION.cff").read_text("utf-8")) == citation_cff()


def test_method_paper_dois_remain_covered_by_catalogue() -> None:
    root = Path(__file__).resolve().parents[2]
    known = {reference.doi.lower() for reference in REFERENCES if reference.doi}
    paths = [root / "methods/README.md", *(root / "methods/src/energy_methods").glob("*.py")]
    for path in paths:
        for doi in re.findall(r"10\.\d{4,9}/[A-Za-z0-9.]+", path.read_text("utf-8")):
            assert doi.rstrip(".").lower() in known, f"Uncredited method DOI in {path.name}: {doi}"


@pytest.mark.parametrize(
    "module",
    [
        "tdp",
        "acceptance_band",
        "poa",
        "lightgbm",
        "physics",
        "status",
        "kgpv",
        "mapping",
        "climatology",
    ],
)
def test_method_reference_ids_resolve_and_include_primary_thesis(module: str) -> None:
    reference_ids = import_module(f"energy_methods.{module}").REFERENCE_IDS
    selected = get_references(reference_ids)
    assert selected[0].id == PRIMARY_REFERENCE_ID
    assert {reference.id for reference in selected} == set(reference_ids)
