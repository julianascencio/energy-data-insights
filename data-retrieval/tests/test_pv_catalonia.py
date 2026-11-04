"""Boundary, privacy and drift checks for the Catalonia review adapter."""

import hashlib
import json

import pytest

from energy_data_retrieval.pv_catalogue.catalonia import (
    GEOGRAPHY_FIELDS,
    PLANT_FIELDS,
    stage_catalonia_review,
)


def stage(rows, *, meta_patch=None, expected=None):
    meta = {
        "id": "ggx8-jkp4",
        "provenance": "official",
        "name": "Plantes solars fotovoltaiques a Catalunya",
        "rowsUpdatedAt": 1790585291,
        "columns": [
            {"fieldName": field}
            for field in ("sol_licitud", "nom", *PLANT_FIELDS, *GEOGRAPHY_FIELDS)
        ],
    }
    meta.update(meta_patch or {})
    content = json.dumps(rows).encode()
    metadata = json.dumps(meta).encode()
    return stage_catalonia_review(
        content,
        metadata,
        sha256=hashlib.sha256(content).hexdigest(),
        metadata_sha256=hashlib.sha256(metadata).hexdigest(),
        expected_rows=len(rows) if expected is None else expected,
    )


def row(**kwargs):
    return {
        "sol_licitud": "FUE-1",
        "nom": "PSFV Example",
        "pot_ncia_mw": "5",
        "superf_cie_ha": "8",
        "municipi": "Town A",
        "sol_licitant": "PRIVATE",
        **kwargs,
    }


def test_municipal_rows_do_not_multiply_capacity_or_projects():
    result = stage([row(), row(municipi="Town B"), row()])
    assert result["observations"] == 3
    assert result["grouped_candidates"] == 1
    assert result["canonical_accepted"] == 0
    candidate = result["candidates"][0]
    assert candidate["native_plant_fields"]["pot_ncia_mw"] == ["5"]
    assert len(candidate["geographies"]) == 2
    assert candidate["source_rows"] == [1, 2, 3]
    assert "PRIVATE" not in json.dumps(result)
    assert "sol_licitant" not in json.dumps(result)


def test_shared_ids_and_reapplications_are_flagged():
    result = stage([row(), row(nom="PSFV Other"), row(sol_licitud="FUE-2")])
    assert result["grouped_candidates"] == 3
    flags = result["candidates"][0]["review_flags"]
    assert "application_shared_by_multiple_names" in flags
    assert "name_has_multiple_applications" in flags


def test_conflicting_scalars_are_preserved_for_review():
    candidate = stage([row(), row(pot_ncia_mw="6")])["candidates"][0]
    assert candidate["native_plant_fields"]["pot_ncia_mw"] == ["5", "6"]
    assert "conflicting_pot_ncia_mw" in candidate["review_flags"]


def test_missing_id_zero_and_expansion_are_not_accepted():
    candidate = stage([row(sol_licitud="", nom="Ampliació PSFV BESS", pot_ncia_mw="0")])[
        "candidates"
    ][0]
    assert {
        "missing_application_id",
        "zero_capacity_requires_technology_scope_review",
        "expansion_storage_or_phase_scope",
    } <= set(candidate["review_flags"])


@pytest.mark.parametrize("value", ["-1", "nan", "inf"])
def test_invalid_measurements_fail_closed(value):
    with pytest.raises(ValueError, match="Invalid Catalonia"):
        stage([row(pot_ncia_mw=value)])


@pytest.mark.parametrize(
    "patch",
    [{"id": "other"}, {"provenance": "community"}, {"name": "Solar thermal"}, {"columns": []}],
)
def test_source_or_schema_drift_fails_closed(patch):
    with pytest.raises(ValueError):
        stage([row()], meta_patch=patch)


def test_truncated_export_fails_closed():
    with pytest.raises(ValueError, match="Truncated"):
        stage([row()], expected=2)


def test_changed_bytes_fail_checksum():
    with pytest.raises(ValueError, match="checksum"):
        stage_catalonia_review(
            b"[]", b"{}", sha256="0" * 64, metadata_sha256="0" * 64, expected_rows=1
        )
