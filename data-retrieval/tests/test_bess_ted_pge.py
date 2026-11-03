"""Synthetic eForms-shaped fixtures: no downloaded notice or personal contacts."""

import pytest

from energy_data_retrieval.bess_catalogue.ted_pge import parse_pge_notice


def notice() -> bytes:
    lots = []
    for i, n in enumerate([5, 6, 6, 5], 1):
        names = ", ".join(f"MEE Example {i}-{j}" for j in range(n))
        lots.append(
            f"<ProcurementProjectLot><ID>LOT-000{i}</ID><ProcurementProject>"
            f"<Name>Synthetic - {names}</Name>"
            "<ItemClassificationCode>31440000</ItemClassificationCode>"
            '<PlannedPeriod><DurationMeasure unitCode="MONTH">28</DurationMeasure></PlannedPeriod>'
            "</ProcurementProject></ProcurementProjectLot>"
        )
    return (
        '<ContractNotice xmlns="urn:oasis:names:specification:ubl:schema:xsd:ContractNotice-2">'
        "<ID>5e67cf82-9d8c-4e4f-ad98-d8c202232abd</ID><VersionID>01</VersionID>"
        "<IssueDate>2026-10-16Z</IssueDate><ProcurementProject>"
        "<ID>POST/EOD/EOD/BM/00319/2026</ID></ProcurementProject>"
        "<Contact><Name>DO NOT EXPORT</Name></Contact>" + "".join(lots) + "</ContractNotice>"
    ).encode()


def test_candidates_keep_distinct_sites_and_privacy_boundary():
    rows = parse_pge_notice(notice())
    assert len(rows) == 22
    assert len({r["source_site_name"] for r in rows}) == 22
    assert rows[-1]["lot_id"] == "LOT-0004"
    assert rows[-1]["site_position_in_lot"] == 5
    assert rows[0]["required_delivery_months"] == 28
    assert "DO NOT EXPORT" not in str(rows)
    assert all("power_mw" not in r and "chemistry" not in r for r in rows)


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"<VersionID>01", b"<VersionID>02"),
        (b"31440000", b"45200000"),
        (b'unitCode="MONTH"', b'unitCode="DAY"'),
        (b"Example 2-0", b"Example 1-0"),
        (b"LOT-0004", b"LOT-0003"),
        (b", MEE Example 1-4", b""),
        (b"2026-10-16Z", b"2026-10-17Z"),
    ],
)
def test_changed_scope_or_duplicate_requires_review(old, new):
    with pytest.raises(ValueError):
        parse_pge_notice(notice().replace(old, new, 1))


def test_entity_declarations_are_not_accepted():
    with pytest.raises(ValueError, match="DTD/entity"):
        parse_pge_notice(b'<!DOCTYPE x [<!ENTITY x "test">]>' + notice())
