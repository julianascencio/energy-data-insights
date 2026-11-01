"""Synthetic PIB fixtures: preserve conflicting source text and reject drift."""

import pytest

from energy_data_retrieval.bess_catalogue.pib import parse_pib_bess_html


def table(*, power="2", total="2", unit="MW", description="Solar 99 MW; battery 3 MW"):
    return (
        "<table><tr><th>Sl. No.</th><th>Details of BESS Deployment</th>"
        "<th>State</th><th>Capacity</th></tr>"
        f"<tr><th>{unit}</th><th>MWh</th></tr>"
        f"<tr><td>1.</td><td>{description}</td><td>Test State</td>"
        f"<td>{power}</td><td>1,200</td></tr>"
        f"<tr><td></td><td>Total</td><td>{total}</td><td>1,200</td></tr></table>"
    )


def test_reported_columns_do_not_overwrite_description_or_infer_battery_power():
    row = parse_pib_bess_html(table().encode())[0]
    assert row["reported_power_mw"] == 2
    assert row["reported_energy_mwh"] == 1200
    assert "battery 3 MW" in row["reported_description"]
    assert row["review_required"] is True
    assert "status" not in row and "record_id" not in row


def test_nested_mobile_copy_is_deduplicated():
    html = table() + "<table><tr><td>Print copy" + table() + "</td></tr></table>"
    assert len(parse_pib_bess_html(html.encode())) == 1


def test_conflicting_copies_fail():
    with pytest.raises(ValueError, match="Conflicting"):
        parse_pib_bess_html((table() + table(power="3", total="3")).encode())


@pytest.mark.parametrize(
    ("html", "error"),
    [
        (table(unit="MVA"), "units"),
        (table(total="3"), "totals"),
        (table(power="-2", total="-2"), "capacity"),
        (table(power="NaN"), "capacity"),
        (table(power="1,2", total="12"), "capacity"),
        (table(power="1,,200", total="1200"), "capacity"),
        (table().replace("1.</td>", "2.</td>"), "row number"),
        (table().replace("Details of BESS Deployment", "Other assets"), "header"),
    ],
)
def test_source_drift_fails_closed(html, error):
    with pytest.raises(ValueError, match=error):
        parse_pib_bess_html(html.encode())


def test_reported_zero_is_retained():
    assert parse_pib_bess_html(table(power="0", total="0").encode())[0]["reported_power_mw"] == 0
