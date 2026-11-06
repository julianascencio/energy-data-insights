"""Synthetic MaStR identity, classification and rating-boundary regression tests."""

import xml.etree.ElementTree as ET

import pytest

from energy_data_retrieval.bess_catalogue.mastr import stage_mastr_storage


def xml(path, root, tag, rows):
    tree = ET.Element(root)
    for row in rows:
        child = ET.SubElement(tree, tag)
        for key, value in row.items():
            ET.SubElement(child, key).text = str(value)
    ET.ElementTree(tree).write(path)
    return path


def unit(**changes):
    return (
        dict(
            EinheitMastrNummer="SEE000000000001",
            SpeMastrNummer="SSE000000000001",
            LokationMaStRNummer="SEL000000000001",
            Land="84",
            Technologie="524",
            EinheitBetriebsstatus="35",
            NameStromerzeugungseinheit="Synthetic plant",
            Nettonennleistung="1000",
            Bruttoleistung="1200",
            ZugeordnenteWirkleistungWechselrichter="1400",
            Inbetriebnahmedatum="2021-01-01",
        )
        | changes
    )


def stage(tmp_path, units=None, storage=None, **kwargs):
    units = [unit()] if units is None else units
    storage = (
        [
            dict(
                MaStRNummer="SSE000000000001",
                NutzbareSpeicherkapazitaet="2400",
                VerknuepfteEinheitenMaStRNummern="SEE000000000001",
            )
        ]
        if storage is None
        else storage
    )
    a = xml(tmp_path / "units.xml", "EinheitenStromSpeicher", "EinheitStromSpeicher", units)
    b = xml(tmp_path / "storage.xml", "AnlagenStromSpeicher", "AnlageStromSpeicher", storage)
    c = xml(
        tmp_path / "values.xml",
        "Katalogwerte",
        "Katalogwert",
        [dict(Id="524", Wert="Batterie"), dict(Id="35", Wert="In Betrieb")],
    )
    return stage_mastr_storage([a], [b], c, snapshot_date="2026-11-06", **kwargs)


def test_reciprocal_join_preserves_units_and_date_boundary(tmp_path):
    r = stage(tmp_path)[0]
    assert (r["net_power_mw"], r["usable_energy_mwh"]) == (1, 2.4)
    assert (r["gross_power_kw"], r["inverter_active_power_kw"]) == (1200, 1400)
    assert r["commissioning_date_reported"] == "2021-01-01"
    assert "commercial_operation_date" not in r
    assert not r["review_flags"]


def test_shared_storage_energy_is_not_allocated(tmp_path):
    r = stage(
        tmp_path,
        storage=[
            dict(
                MaStRNummer="SSE000000000001",
                NutzbareSpeicherkapazitaet="2400",
                VerknuepfteEinheitenMaStRNummern="SEE000000000001,SEE000000000002",
            )
        ],
    )[0]
    assert r["usable_energy_mwh"] is None
    assert "missing_or_nonexclusive_reciprocal_storage_link" in r["review_flags"]


def test_small_sibling_still_flags_shared_site(tmp_path):
    rows = stage(
        tmp_path,
        units=[unit(), unit(EinheitMastrNummer="SEE000000000002", Nettonennleistung="100")],
    )
    assert len(rows) == 1
    assert "shared_battery_location_in_supplied_partitions" in rows[0]["review_flags"]


def test_nonbattery_and_implausible_date_are_review_only(tmp_path):
    r = stage(tmp_path, units=[unit(Technologie="1537", Inbetriebnahmedatum="1923-01-01")])[0]
    assert "not_battery" in r["review_flags"]
    assert "commissioning_date_requires_review" in r["review_flags"]


def test_missing_energy_does_not_become_zero(tmp_path):
    r = stage(tmp_path, storage=[])[0]
    assert r["usable_energy_mwh"] is None


@pytest.mark.parametrize("rating", ["nan", "inf", "-1"])
def test_bad_ratings_fail(tmp_path, rating):
    with pytest.raises(ValueError, match="finite nonnegative"):
        stage(tmp_path, units=[unit(Nettonennleistung=rating)])


def test_duplicate_unit_ids_fail(tmp_path):
    with pytest.raises(ValueError, match="Duplicate unit"):
        stage(tmp_path, units=[unit(), unit()])


def test_duplicate_storage_ids_fail(tmp_path):
    with pytest.raises(ValueError, match="Duplicate storage"):
        stage(tmp_path, storage=[dict(MaStRNummer="SSE000000000001")] * 2)


def test_invalid_unit_identity_fails(tmp_path):
    with pytest.raises(ValueError, match="Invalid SEE"):
        stage(tmp_path, units=[unit(EinheitMastrNummer="not-an-id")])
