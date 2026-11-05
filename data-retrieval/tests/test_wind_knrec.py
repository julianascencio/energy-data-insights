"""Synthetic certification registry fixtures."""

import hashlib

import pytest

from energy_data_retrieval.wind_catalogue.knrec import certification_rows


def test_raw_modes_and_class_preserved():
    cells = ["1", "WT-test", "2018.01.01", "Applicant", "Model", "3.45/3.6 MW"] + [""] * 8
    raw = ("<table><tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr></table>").encode()
    assert certification_rows(raw, sha256=hashlib.sha256(raw).hexdigest())["WT-test"] == cells
    with pytest.raises(ValueError, match="checksum"):
        certification_rows(raw, sha256="bad")
    duplicate = raw + raw
    with pytest.raises(ValueError, match="duplicate"):
        certification_rows(duplicate, sha256=hashlib.sha256(duplicate).hexdigest())


def test_empty_register_rejected():
    raw = b"<html>Maintenance</html>"
    with pytest.raises(ValueError, match="No certification"):
        certification_rows(raw, sha256=hashlib.sha256(raw).hexdigest())
