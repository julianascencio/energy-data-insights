"""NEPRA review boundary, source identity, privacy and native-unit tests."""

from __future__ import annotations

import hashlib

import pytest

from energy_data_retrieval.pv_catalogue.nepra import stage_nepra_review

URL = "https://nepra.org.pk/licensing/Generation%20Distributed%20Generation.php"


def block(
    name: str = "Example Energy Limited - two campuses",
    licence: str = "SGC/100/2024",
    detail: str = "1000 x 500 W Mono Crystalline PV",
    kind: str = "Solar",
    capacity: str = "0.500 MW",
    extra: str = "",
) -> str:
    return f"""<h6>{name}</h6><table>
    <tr><td>Plant Detail</td><td><span>{detail}</span></td></tr>
    <tr><td>Plant Type</td><td>{kind}</td></tr>
    <tr><td>Gross\n Capacity</td><td>{capacity}</td></tr>
    <tr><td>Licence No.</td><td>{licence}</td></tr>
    <tr><td>Licence Details</td><td><a href="Licences/example.pdf">View</a></td></tr>
    {extra}</table>"""


def stage(html: str, *, url: str = URL) -> dict:
    data = html.encode()
    return stage_nepra_review(data, sha256=hashlib.sha256(data).hexdigest(), source_url=url)


def test_review_only_preserves_native_units_and_portfolio_scope() -> None:
    result = stage(block(capacity="1.5120 MWp"))
    assert result["accepted_canonical_records"] == 0
    row = result["candidates"][0]
    assert row["native_fields"]["Gross Capacity"] == "1.5120 MWp"
    assert row["explicit_pv_description"]
    assert "project_or_portfolio_scope_unreviewed" in row["review_reasons"]
    assert "gross_capacity_not_assigned_ac_or_dc" in row["review_reasons"]
    assert "capacity_ac_mw" not in row and "capacity_dc_mw" not in row
    assert "entity_type" not in row and "record_id" not in row


def test_generic_solar_is_not_proof_of_pv_and_thermal_is_excluded() -> None:
    result = stage(block(detail="", licence="SGC/101/2024") + block(kind="Thermal", detail="Gas"))
    assert len(result["candidates"]) == 1
    assert not result["candidates"][0]["explicit_pv_description"]
    assert "generic_solar_not_explicit_pv" in result["candidates"][0]["review_reasons"]
    assert result["excluded_counts"]["non_solar_block"] == 1


def test_omitted_html_cell_and_row_end_tags_preserve_native_columns() -> None:
    html = block().replace("</td>", "").replace("</tr>", "")
    row = stage(html)["candidates"][0]
    assert row["native_fields"]["Licence No."] == "SGC/100/2024"
    assert row["native_fields"]["Gross Capacity"] == "0.500 MW"


def test_same_company_licences_are_not_merged_and_duplicates_are_held() -> None:
    result = stage(block() + block(licence="SGC/101/2024") + block())
    assert len(result["candidates"]) == 3
    assert "duplicate_source_licence_number" in result["candidates"][0]["review_reasons"]
    assert "duplicate_source_licence_number" not in result["candidates"][1]["review_reasons"]


def test_transfer_link_is_evidence_not_current_owner_or_status() -> None:
    extra = (
        '<tr><td>2024 licence transfer decision</td><td><a href="decision.pdf">View</a></td></tr>'
    )
    row = stage(block(extra=extra))["candidates"][0]
    assert row["documents"][1]["url"] == "https://nepra.org.pk/licensing/decision.pdf"
    assert "licence_not_current_operation_or_ownership" in row["review_reasons"]
    assert "owners" not in row and "status" not in row


def test_noncorporate_headings_and_contact_fields_are_not_exported() -> None:
    html = block(name="Mr Private Person", extra="<tr><td>Phone</td><td>12345678</td></tr>")
    html += block(extra='<tr><td>Phone</td><td><a href="contact/87654321">87654321</a></td></tr>')
    result = stage(html)
    assert result["excluded_counts"]["noncorporate_heading_omitted"] == 1
    assert "Private Person" not in str(result)
    assert "12345678" not in str(result) and "87654321" not in str(result)


def test_untrusted_document_links_are_omitted() -> None:
    html = block(
        extra='<tr><td>Other</td><td><a href="https://elsewhere.test/a.pdf">View</a></td></tr>'
    )
    assert len(stage(html)["candidates"][0]["documents"]) == 1


def test_malformed_capacity_and_licence_notation_are_not_repaired() -> None:
    row = stage(block(capacity="02:00 MW", licence="SGC/173/202 3"))["candidates"][0]
    assert row["native_fields"]["Gross Capacity"] == "02:00 MW"
    assert row["native_fields"]["Licence No."] == "SGC/173/202 3"
    assert "unparsed_capacity_notation" in row["review_reasons"]
    assert "licence_notation_requires_review" in row["review_reasons"]


def test_checksum_source_host_and_size_are_enforced() -> None:
    data = block().encode()
    with pytest.raises(ValueError):
        stage_nepra_review(data, sha256="0" * 64, source_url=URL)
    with pytest.raises(ValueError, match="URL or size"):
        stage(block(), url="https://elsewhere.test/directory")
    large = b" " * 2_000_001
    with pytest.raises(ValueError, match="URL or size"):
        stage_nepra_review(large, sha256=hashlib.sha256(large).hexdigest(), source_url=URL)


@pytest.mark.parametrize(
    "html",
    [
        "<h6>Access denied</h6>",
        block().replace("Plant Type", "Renamed Kind"),
        block().replace("</table>", ""),
        block().replace("</table>", "</table><table></table>"),
        block(extra="<tr><td>Plant Type</td><td>Solar</td></tr>"),
    ],
)
def test_schema_changes_and_access_pages_fail_closed(html: str) -> None:
    with pytest.raises(ValueError):
        stage(html)
