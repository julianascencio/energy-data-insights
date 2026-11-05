"""Synthetic dispatch intervals must not become duplicate plants or summed MW."""

import csv
import io

import pytest

from energy_data_retrieval.hydro_catalogue.nz import FIELDS, parse_inventory


def sample(**changes):
    row = dict.fromkeys(FIELDS, "null")
    row.update(
        PlantName="Synthetic",
        PointOfConnectionCode="ABC1101",
        UnitCode="ABC0",
        TechnologyCode="HYD",
        FuelCode="HYD",
        NameplateMegawatts="10",
        EffectiveStartDate="1899-12-31T12:30:00.000Z",
        EffectiveEndDate="9999-12-31T10:59:59.000Z",
    )
    row.update(changes)
    return row


def encode(rows):
    out = io.StringIO()
    writer = csv.DictWriter(out, fieldnames=FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode()


def test_preserves_distinct_connections_and_sentinels_without_summing():
    rows = parse_inventory(encode([sample(), sample(PointOfConnectionCode="ABC1102")]))
    assert len(rows) == 2
    assert rows[0]["row"] == 2
    assert rows[1]["raw"]["NameplateMegawatts"] == "10"
    assert rows[0]["raw"]["EffectiveStartDate"].startswith("1899")


@pytest.mark.parametrize(
    "changes",
    [
        dict(NameplateMegawatts="nan"),
        dict(NameplateMegawatts="-1"),
        dict(EffectiveEndDate="1800-01-01T00:00:00Z"),
        dict(UnitCode=""),
        dict(FuelCode="GAS"),
    ],
)
def test_rejects_invalid_hydro_observations(changes):
    with pytest.raises(ValueError):
        parse_inventory(encode([sample(**changes)]))


def test_rejects_duplicates_and_shifted_rows():
    with pytest.raises(ValueError, match="Duplicate"):
        parse_inventory(encode([sample(), sample()]))
    with pytest.raises(ValueError, match="columns"):
        parse_inventory(b"PlantName\nExample\n")
    with pytest.raises(ValueError, match="Malformed"):
        parse_inventory(encode([sample()]) + b"Too,few,cells\n")


def test_reviewed_dispatch_preserves_capacity_lifecycle_and_is_immutable():
    from energy_data_retrieval.hydro_catalogue.gppd import parse_gppd
    from energy_data_retrieval.hydro_catalogue.nz import enrich_reviewed

    old = parse_gppd(
        "country,name,gppd_idnr,primary_fuel,capacity_mw,latitude,longitude\n"
        "NZL,Synthetic,NZL1,Hydro,10,-40,170\n",
        source_id="wri",
        now="2026-01-01T00:00:00Z",
    )[0][0]
    item = {"row": 2, "raw": sample()}
    kw = dict(
        reviewed_record_id=old["record_id"], owner_source_id="owner", now="2026-11-05T00:00:00Z"
    )
    new = enrich_reviewed(old, item, **kw)
    assert enrich_reviewed(new, item, **kw) == new
    for field in ["created_at", "status", "aggregation_role", "historical_capacity_mw"]:
        assert new[field] == old[field]
    assert new.get("installed_capacity_mw") is None
    with pytest.raises(ValueError, match="identity"):
        enrich_reviewed(old, item, **{**kw, "reviewed_record_id": "wrong"})
    item["raw"]["PointOfConnectionCode"] = "OTHER"
    with pytest.raises(ValueError, match="history"):
        enrich_reviewed(new, item, **kw)
