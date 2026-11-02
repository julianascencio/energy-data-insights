"""Synthetic financing records: no real project observations."""

import pytest

from energy_data_retrieval.bess_catalogue.adb_iati import stage_adb_battery_activities


def sample(identifier="XM-DAC-46004-1", title="Battery project"):
    return f"""<iati-activity><iati-identifier>{identifier}</iati-identifier>
    <title><narrative>{title}</narrative></title><activity-status code="2"/>
    <location><point><pos>41 63</pos></point></location>
    <contact-info><email>private@example.org</email></contact-info></iati-activity>"""


def wrap(body):
    return f'<iati-activities version="2.03">{body}</iati-activities>'.encode()


def test_financing_rows_remain_separate_without_coordinates_or_operating_inference():
    rows = stage_adb_battery_activities(wrap(sample() + sample("XM-DAC-46004-2")))
    assert len(rows) == 2
    assert rows[0]["activity_status_code"] == "2"
    assert "operational" not in str(rows)
    assert "private@example" not in str(rows)
    assert "coordinates" not in rows[0]


def test_nonbattery_not_accepted():
    assert stage_adb_battery_activities(wrap(sample(title="Pumped hydro"))) == []


@pytest.mark.parametrize("body", [sample() + sample(), sample("OTHER-1")])
def test_invalid_identity_rejected(body):
    with pytest.raises(ValueError):
        stage_adb_battery_activities(wrap(body))


def test_dtd_rejected():
    with pytest.raises(ValueError):
        stage_adb_battery_activities(b'<!DOCTYPE x><iati-activities version="2.03"/>')
