"""Synthetic seven-column fixtures exercise units, identity and merged-cell scope."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.bslbatt import SOURCE_URLS, parse_station_table


def fixture(family="S314"):
    header = "ESS-GRID " + " ".join(f"{family}-{n}" for n in range(10, 17))
    return (
        header
        + "\nRated Voltage(V) 500 550 600 650 700 750 800"
        + "\nRated Capacity(Ah) 300\nCell Model(LFP-3.2V)(Ah) 300"
        + "\nRate Power(kWh) 150 165 180 195 210 225 240"
        + "\nCharge Upper Voltage(V) 550 600 650 700 750 800 850"
        + "\nDischarge Lower Voltage(V) 450 500 550 600 650 700 750"
        + "\nNumber of Series 10 11 12 13 14 15 16"
        + "\nRecommended Current(A) 150"
        + "\nMax. Charging Current(A) 150\nMax. Discharging Current(A) 150\n"
    ).encode()


def parse(content, family="S314"):
    return parse_station_table(content, family=family, source_url=SOURCE_URLS[family])


def test_column_identity_and_energy_not_power():
    rows = parse(fixture())
    assert len(rows) == 7
    assert rows[0]["model"] == "ESS-GRID S314-10"
    assert rows[-1]["model"] == "ESS-GRID S314-16"
    assert rows[-1]["reported_energy_kwh"] == 240
    assert all(row["active_power_kw"] is None for row in rows)
    assert all(row["recommended_current_a"] == 150 for row in rows)
    assert len(rows[0]["extracted_text_sha256"]) == 64


@pytest.mark.parametrize(
    ("old", "new"),
    [
        (b"Rate Power(kWh)", b"Rate Power(kW)"),
        (b"150 165 180 195 210 225 240", b"150 165 180 195 210 225"),
        (b"150 165 180 195 210 225 240", b"0 165 180 195 210 225 240"),
        (b"S314-10 S314-11", b"S314-11 S314-10"),
        (b"Recommended Current(A) 150", b"Recommended Current(A) 150 160"),
        (b"Number of Series 10 11 12 13 14 15 16", b"Number of Series 10 11 12 13 14 15 15"),
        (b"Cell Model(LFP-3.2V)(Ah) 300", b"Cell Model(LFP-3.2V)(Ah) 200"),
        (b"Discharge Lower Voltage(V) 450", b"Discharge Lower Voltage(V) 600"),
    ],
)
def test_changed_units_scope_and_invalid_values_fail_closed(old, new):
    with pytest.raises(ValueError):
        parse(fixture().replace(old, new))


def test_duplicate_tables_and_rows_rejected():
    with pytest.raises(ValueError, match="header"):
        parse(fixture() * 2)
    with pytest.raises(ValueError, match="duplicate row"):
        parse(fixture() + b"Rated Capacity(Ah) 300\n")


def test_s205_current_claims_remain_unresolved():
    rows = parse(fixture("S205"), "S205")
    assert all(row["current_review_required"] for row in rows)
    assert all("0.5C" in row["current_review_reason"] for row in rows)


def test_other_source_rejected():
    with pytest.raises(ValueError, match="official source"):
        parse_station_table(fixture(), family="S314", source_url="https://example.com/copy.pdf")
