"""Fail-closed staging and unit tests using synthetic portfolio rows."""

import hashlib
from pathlib import Path

import pytest

from energy_data_retrieval.pv_catalogue.izmir import HEADERS, read_izmir_csv


def stage(tmp_path: Path, body: str, header: tuple = HEADERS) -> list[dict]:
    import csv
    import io

    buffer = io.StringIO()
    csv.writer(buffer, delimiter=";", lineterminator="\n").writerow(header)
    data = (buffer.getvalue() + body).encode()
    path = tmp_path / "portfolio.csv"
    path.write_bytes(data)
    return read_izmir_csv(path, sha256=hashlib.sha256(data).hexdigest())


def test_units_and_no_lifecycle_or_ac_inference(tmp_path):
    row = stage(tmp_path, "Synthetic site;40;450;15;24000;2025 planned\n")[0]
    assert row["capacity_unspecified_mw"] == 0.015
    assert row["expected_annual_generation_mwh"] == 24
    assert row["module_count"] == 40
    assert row["identity_review_required"]
    assert "status" not in row and "capacity_ac_mw" not in row
    assert row["native_status_note"] == "2025 planned"


def test_missing_panel_values_preserved(tmp_path):
    row = stage(tmp_path, "Synthetic site;-;-;15;24000;unknown\n")[0]
    assert row["module_count"] is None and row["reported_module_power_w"] is None


@pytest.mark.parametrize(
    "body",
    [
        "X;1;450;15;24000;x\nX;1;450;15;24000;x\n",
        "X;1.5;450;15;24000;x\n",
        "X;1;450;-15;24000;x\n",
        "X;1;450;nan;24000;x\n",
        "X;1;450;15;24000;x;extra\n",
    ],
)
def test_reject_bad_rows(tmp_path, body):
    with pytest.raises(ValueError):
        stage(tmp_path, body)


def test_header_and_checksum(tmp_path):
    with pytest.raises(ValueError):
        stage(tmp_path, "X;1;450;15;24000;x\n", header=("wrong", *HEADERS[1:]))
    path = tmp_path / "bad.csv"
    path.write_text("anything")
    with pytest.raises(ValueError, match="checksum"):
        read_izmir_csv(path, sha256="0" * 64)
