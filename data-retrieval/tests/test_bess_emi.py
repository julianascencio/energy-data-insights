import pytest

from energy_data_retrieval.bess_catalogue.emi import parse_emi_batteries

HEADER = (
    b"PlantName,TechnologyCode,PointOfConnectionCode,UnitCode,NameplateMegawatts,"
    b"EffectiveStartDate,EffectiveEndDate\n"
)
ROW = b"Synthetic,BAT,POC,UNIT,0,2026-01-01,9999-01-01\n"


def test_preserves_observation_dates_and_zero_without_inventing_status():
    rows = parse_emi_batteries(HEADER + ROW + ROW.replace(b"BAT", b"HYD"))
    assert len(rows) == 1
    assert rows[0]["NameplateMegawatts"] == "0"
    assert "status" not in rows[0]


def test_dated_revisions_are_not_merged():
    assert len(parse_emi_batteries(HEADER + ROW + ROW.replace(b"2026", b"2025"))) == 2
    with pytest.raises(ValueError, match="Duplicate"):
        parse_emi_batteries(HEADER + ROW + ROW)


@pytest.mark.parametrize("bad", [b"NaN", b"-1", b"inf"])
def test_rejects_invalid_power(bad):
    with pytest.raises(ValueError):
        parse_emi_batteries(HEADER + ROW.replace(b",0,", b"," + bad + b","))


def test_rejects_header_drift():
    with pytest.raises(ValueError, match="header"):
        parse_emi_batteries(b"Other\n")
