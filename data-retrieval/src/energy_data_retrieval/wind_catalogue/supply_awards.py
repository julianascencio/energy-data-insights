"""Stage reviewed OEM award announcements without importing installed fleets."""

from __future__ import annotations

import hashlib
from datetime import date
from typing import Any

REFERENCE_IDS = ("windey_aysha_award_20260819",)


def review_supply_award(
    review: dict[str, Any], original: bytes, project: dict[str, Any]
) -> dict[str, Any]:
    """Return a dated, provenance-qualified event for an explicitly matched project.

    A model mentioned in an award article is a nomination observation. It cannot
    select a regional configuration, populate installed equipment IDs, or replace
    an earlier lender envelope. Callers retain earlier dated observations.
    """
    if hashlib.sha256(original).hexdigest() != review.get("sha256"):
        raise ValueError("Original award checksum mismatch")
    required = ("source_id", "locator", "manufacturer", "identity_basis", "published_at")
    if any(not isinstance(review.get(k), str) or not review[k].strip() for k in required):
        raise ValueError("Award needs source, locator, date, manufacturer and identity basis")
    date.fromisoformat(review["published_at"])
    if project.get("entity_type") != "projects" or project.get("record_id") != review.get(
        "project_record_id"
    ):
        raise ValueError("Explicit existing project identity required")
    if review.get("event") != "turbine_supply_award":
        raise ValueError("Only reviewed turbine supply awards are supported")
    if review.get("configuration_status") != "unresolved":
        raise ValueError("Award article alone cannot establish exact installed configuration")
    model = review.get("model_mentioned")
    if model is not None and (not isinstance(model, str) or not model.strip()):
        raise ValueError("Model mention must be a name or null")
    return {
        "source_id": review["source_id"],
        "published_at": review["published_at"],
        "locator": review["locator"],
        "event": review["event"],
        "manufacturer": review["manufacturer"],
        "model_mentioned": model,
        "identity_basis": review["identity_basis"],
        "configuration_status": "unresolved",
        "equipment_record_id": None,
        "installed_turbine_count": None,
        "basis": "OEM award announcement; not installation or independently validated performance",
    }
