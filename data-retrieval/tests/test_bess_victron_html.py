"""Synthetic tables test model scope and electrical units, not source copies."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.victron_html import parse_victron_manual_html

URL = (
    "https://www.victronenergy.com/media/pg/MultiPlus_12V_500-1200VA_120Vac/en/technical-data.html"
)


def table():
    return """
    <table><tr><th>MultiPlus</th><th>12/500/20 - 120V</th>
    <th>12/800/35 - 120V</th><th>12/1200/50 - 120V</th></tr>
    <tr><td>Cont. output power at 25°C <sup>(2)</sup></td>
    <td>500VA</td><td>800VA</td><td>1200VA</td></tr>
    <tr><td>Cont. output power at 25°C</td><td>430W</td><td>700W</td><td>1000W</td></tr>
    <tr><td>Peak power</td><td>900W</td><td>1600W</td><td>2400W</td></tr>
    <tr><td>Maximum efficiency</td><td>90%</td><td>92%</td><td>93%</td></tr>
    <tr><td>Transfer switch</td><td colspan="3">16A</td></tr></table>
    """


def parse(html):
    return parse_victron_manual_html(html.encode(), source_url=URL)


def test_active_apparent_and_model_identity_stay_distinct():
    rows = parse(table())
    assert len(rows) == 3
    assert rows[1]["model_header"] == "12/800/35 - 120V"
    obs = rows[1]["observations"]
    assert [o["reported_value"] for o in obs[:2]] == ["800VA", "700W"]
    assert obs[-1]["shared_colspan"] is True
    assert obs[0]["shared_colspan"] is False
    assert "record_id" not in rows[0] and "power_capacity_mw" not in rows[0]
    assert rows[0]["review_required"] is True


@pytest.mark.parametrize(
    "old,new",
    [
        ('colspan="3"', 'colspan="2"'),
        ('colspan="3"', 'rowspan="3"'),
        ('colspan="3"', ""),
        ("<td>700W</td>", "<td></td>"),
        ("12/800/35 - 120V", "12/800/35 - 230V"),
        ("800VA", "800W"),
        ("Maximum efficiency", "Changed efficiency"),
    ],
)
def test_layout_and_units_drift_fail_closed(old, new):
    with pytest.raises(ValueError):
        parse(table().replace(old, new))


def test_duplicate_table_and_label_require_review():
    with pytest.raises(ValueError, match="one exact"):
        parse(table() + table())
    with pytest.raises(ValueError, match="Duplicate"):
        parse(table().replace("Peak power", "Maximum efficiency"))


def test_unknown_endpoint_rejected():
    with pytest.raises(ValueError, match="URL"):
        parse_victron_manual_html(table().encode(), source_url="https://example.com/manual")
