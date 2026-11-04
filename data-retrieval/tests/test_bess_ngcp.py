"""Synthetic service rows test classification; no bulletin content fixture."""

import pytest

from energy_data_retrieval.bess_catalogue.ngcp import (
    BATTERY_NAMES,
    SEPTEMBER_NAMES,
    SEPTEMBER_URL,
    SOURCE_URL,
    parse_ngcp_batteries,
)


def fixture():
    text = (
        "01 April 2026 AS OF MARCH 2026\n"
        "Currently not providing their contracted Firm AS capacity\n"
        "BSS-Black Start Service\nSynthetic Hydro Plant BSS 2026-999 RC\n"
    )
    for i, name in enumerate(BATTERY_NAMES):
        if i == 13:
            text += "\fLIST OF AS CERTIFIED PLANTS WITH NO ASPA\n"
        text += name + (" ***" if i == 2 else "") + " RR, CR"
        text += " 2026-001 RC\n" if i < 13 else "\n"
    return text


def parse(text):
    return parse_ngcp_batteries(text.encode(), source_url=SOURCE_URL)


def test_service_is_not_technology_or_operation():
    rows = parse(fixture())
    assert len(rows) == 21
    assert rows[2]["not_providing_contracted_firm_capacity"]
    assert rows[13]["erc_case"] is None
    assert rows[13]["section"] == "certified_no_aspa"
    assert "page 2" in rows[13]["locator"]
    assert all("status" not in r and "power_capacity_mw" not in r for r in rows)


@pytest.mark.parametrize(
    "change",
    [
        lambda t: t.replace("01 April", "02 April"),
        lambda t: t.replace("BSS-Black Start Service", "BSS-Battery"),
        lambda t: t.replace(BATTERY_NAMES[0], "Unreviewed BESS"),
        lambda t: t + BATTERY_NAMES[0] + " RR, CR\n",
        lambda t: t.replace(" RR, CR", " RR, DR"),
        lambda t: t.replace(" 2026-001 RC", "", 1),
        lambda t: t + "Unreviewed Battery Energy Storage System RR\n",
    ],
)
def test_changed_partition_or_semantics_fails(change):
    with pytest.raises(ValueError):
        parse(change(fixture()))


def test_september_changed_contract_and_hybrid_scope():
    header = (
        "28 September 2026 AS OF SEPTEMBER 2026\n"
        "With filed Motion for Termination of the ASPA\nBSS-Black Start Service\n"
    )
    contracted = set(BATTERY_NAMES[:13]) | {
        "Lumban Battery Energy Storage System",
        "Sangali Battery Energy Storage System",
    }
    text = header
    for name in SEPTEMBER_NAMES:
        if name in contracted:
            text += name + " RR 2026-001 RC\n"
    text += "LIST OF AS CERTIFIED PLANTS WITH NO ASPA\n"
    for name in SEPTEMBER_NAMES:
        if name not in contracted:
            text += name + " CR\n"
    rows = parse_ngcp_batteries(text.encode(), source_url=SEPTEMBER_URL)
    assert len(rows) == 22
    assert all(r["reporting_date"] == "2026-09-28" for r in rows)
    assert any("w/ BESS Unit 2" in r["plant_name"] for r in rows)
    assert not any(r["plant_name"] == "Gamu BESS" for r in rows)
    with pytest.raises(ValueError):
        parse_ngcp_batteries(text.encode(), source_url=SOURCE_URL)
