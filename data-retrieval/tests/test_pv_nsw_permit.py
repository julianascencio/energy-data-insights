import hashlib

import pytest

from energy_data_retrieval.pv_catalogue.nsw import read_nsw_project_page


def document(identifier="SSD-5355", extra="", date="15/07/2013"):
    return (
        "<h1>Example Solar Farm</h1><script>Project Details</script>"
        "<div>Submissions</div><p>PRIVATE SUBMITTER private@example.test</p>"
        "<h2>Project Details</h2><div>Application Number</div>"
        f"<div>{identifier}</div><div>Assessment Type</div>"
        "<div>State Significant Development</div><div>Development Type</div>"
        "<div>Electricity Generation - Solar</div><div>Local Government Areas</div>"
        "<div>Example Council</div><div>Decision</div><div>Approved</div>"
        f"<div>Determination Date</div><div>{date}</div>{extra}"
        "<h2>Contact Planner</h2><p>SECRET CONTACT secret@example.test</p>"
        "<h2>Related Projects</h2><p>Other application</p>"
    ).encode()


def read(data):
    return read_nsw_project_page(data, sha256=hashlib.sha256(data).hexdigest())


def test_departmental_fields_without_personal_material():
    row = read(document())
    assert row["application_id"] == "SSD-5355"
    assert row["determination_date"] == "2013-07-15"
    assert "PRIVATE" not in str(row) and "SECRET" not in str(row)
    assert "example.test" not in str(row)
    assert "capacity_ac_mw" not in row and "technology" not in row
    assert row["review_status"].startswith("Unaccepted")


@pytest.mark.parametrize("identifier", ["SSD-5355-MOD-1", "SSD-5355-Mod-2"])
def test_modifications_are_not_plant_identities(identifier):
    assert read(document(identifier))["is_modification"]


@pytest.mark.parametrize("identifier", ["MP10_0123", "MP_10_0123"])
def test_legacy_identifier_is_retained(identifier):
    assert read(document(identifier))["application_id"] == identifier


def test_checksum_fail_closed():
    with pytest.raises(ValueError, match="checksum"):
        read_nsw_project_page(document(), sha256="0" * 64)


def test_missing_contact_boundary_fails_closed():
    with pytest.raises(ValueError):
        read(document().replace(b"Contact Planner", b"Other heading"))


def test_duplicate_application_field_rejected():
    with pytest.raises(ValueError, match="Duplicate"):
        read(document(extra="<div>Application Number</div><div>SSD-9999</div>"))


def test_unrecognized_field_drift_is_not_silently_mapped():
    with pytest.raises(ValueError, match="malformed"):
        read(document(extra="<div>Unexpected field</div><div>value</div>"))


def test_impossible_date_rejected():
    with pytest.raises(ValueError):
        read(document(date="31/02/2026"))


def test_multiple_headings_are_ambiguous():
    with pytest.raises(ValueError, match="Ambiguous"):
        read(document() + b"<h1>Second project</h1>")


def test_duplicate_details_section_rejected():
    with pytest.raises(ValueError, match="Ambiguous"):
        read(document() + b"<h2>Project Details</h2>")


@pytest.mark.parametrize("identifier", ["unknown", "5355", "SSD-5355-MOD", "PPS-123"])
def test_unrecognized_identifier_is_not_repaired(identifier):
    with pytest.raises(ValueError, match="identifier"):
        read(document(identifier))


def test_unknown_identity_field_is_required():
    with pytest.raises(ValueError):
        read(document().replace(b"Local Government Areas", b"Other geography"))


def test_epbc_reference_is_preserved_without_approval_inference():
    row = read(document(extra="<div>EPBC ID Number</div><div>2022/09444</div>"))
    assert row["epbc_referral_id"] == "2022/09444"
    assert "environmental_approval" not in row


def test_invalid_epbc_reference_rejected():
    with pytest.raises(ValueError, match="EPBC"):
        read(document(extra="<div>EPBC ID Number</div><div>private text</div>"))
