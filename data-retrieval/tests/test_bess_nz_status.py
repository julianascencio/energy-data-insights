"""Synthetic EA layout fixtures; no publisher documents embedded."""

import pytest

from energy_data_retrieval.bess_catalogue.nz_status import HEADERS, parse_ea_status_html


def fixture():
    rows = [HEADERS] + [
        [f"Test {n}", "Owner/Brand", "100MW/200MWh (2 hours storage)", "Grid connected", status]
        for n, status in enumerate(
            ["Commissioned in May 2025"] * 3 + ["Under construction", "Commissioning", "Committed"]
        )
    ]
    return (
        "29 September 2026 Status of BESS developments<table>"
        + "".join("<tr>" + "".join(f"<td>{v}</td>" for v in r) + "</tr>" for r in rows)
        + "</table>"
    ).encode()


def test_ratings_and_historical_status_stay_distinct():
    rows = parse_ea_status_html(fixture())
    assert (rows[0]["power_mw"], rows[0]["energy_mwh"]) == (100, 200)
    assert rows[0]["owner_native"] == "Owner/Brand"
    assert rows[0]["status_native"] == "Commissioned in May 2025"
    assert rows[-1]["status_native"] == "Committed"
    assert all("commercial_operation_date" not in row for row in rows)


@pytest.mark.parametrize(
    "old,new",
    [
        (b"29 September 2026", b"30 September 2026"),
        (b"BESS name/location", b"Plant name"),
        (b"100MW/200MWh", b"100MWh/200MW"),
        (b"Test 1", b"Test 0"),
        (b"Commissioning", b"Operational"),
        (b"100MW", b"0MW"),
    ],
)
def test_unreviewed_release_or_rows_rejected(old, new):
    with pytest.raises(ValueError):
        parse_ea_status_html(fixture().replace(old, new))
