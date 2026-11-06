"""Awards cannot silently import installed regional configurations or counts."""

import copy
import hashlib
import json
from pathlib import Path

import pytest

from energy_data_retrieval.wind_catalogue.supply_awards import review_supply_award


def inputs():
    review = json.loads(
        (Path(__file__).parent / "fixtures/wind/supply_award_synthetic.json").read_text()
    )
    review["sha256"] = hashlib.sha256(b"synthetic original").hexdigest()
    project = {"entity_type": "projects", "record_id": "synthetic-project", "status": "announced"}
    return review, project


def test_award_preserves_project_and_does_not_parse_model_or_link_foreign_configuration():
    review, project = inputs()
    before = copy.deepcopy(project)
    review.update(equipment_record_id="foreign-60hz", installed_turbine_count=39)
    result = review_supply_award(review, b"synthetic original", project)
    assert project == before
    assert result["equipment_record_id"] is None
    assert result["installed_turbine_count"] is None
    assert "rotor_diameter_m" not in result and "rated_power_kw" not in result
    assert result["model_mentioned"] == "Model 200-7700"
    assert result == review_supply_award(review, b"synthetic original", project)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("sha256", "0" * 64),
        ("locator", ""),
        ("identity_basis", None),
        ("project_record_id", "other-project"),
        ("published_at", "2026-02-30"),
        ("event", "commissioned"),
        ("configuration_status", "installed"),
        ("model_mentioned", []),
    ],
)
def test_award_rejects_bad_provenance_identity_and_installation_claims(field, value):
    review, project = inputs()
    review[field] = value
    with pytest.raises(ValueError):
        review_supply_award(review, b"synthetic original", project)
