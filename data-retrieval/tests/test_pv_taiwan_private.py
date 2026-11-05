"""Synthetic inventory guards; no publisher document copied into fixtures."""

import hashlib

import pytest

from energy_data_retrieval.pv_catalogue.taiwan_private import (
    CAPTION,
    HEADERS,
    read_taiwan_private_pv,
)


def document(rows=None, caption=CAPTION, headers=HEADERS):
    rows = rows or (
        '<tr><td rowspan="2">Synthetic corporation</td><td rowspan="2">PV I</td>'
        '<td>Locality A</td><td>1,000.25</td><td rowspan="2">113</td></tr>'
        "<tr><td>Locality B</td><td>200.00</td></tr>"
    )
    return (
        f"<table><caption>{caption}</caption><tr>"
        + "".join(f"<th>{h}</th>" for h in headers)
        + "</tr>"
        + rows
        + '<tr><td colspan="3">合 計</td><td>1,200</td><td> </td></tr></table>'
    ).encode()


def read(data, **kwargs):
    return read_taiwan_private_pv(data, sha256=hashlib.sha256(data).hexdigest(), **kwargs)


def test_rowspan_origin_and_partition_do_not_create_plants():
    data = document()
    first = read(data, limit=1)
    second = read(data, after_row=first["next_after_row"], limit=1)
    row = second["candidates"][0]
    assert row["company_native"] == "Synthetic corporation"
    assert row["cell_origin_rows"] == [1, 1, 2, 2, 1]
    assert row["installed_kw_native"] == "200.00"
    assert row["commercial_year_roc_native"] == "113"
    assert "record_id" not in row and "status" not in row and "capacity_ac_mw" not in row
    assert first["remaining_rows"] == 1 and second["remaining_rows"] == 0
    assert second["accepted_records"] == 0


@pytest.mark.parametrize(
    "change", ["checksum", "classification", "columns", "span", "power", "year", "footer"]
)
def test_fail_closed_on_changed_or_ambiguous_source(change):
    data = document()
    if change == "checksum":
        with pytest.raises(ValueError, match="checksum"):
            read_taiwan_private_pv(data, sha256="0" * 64)
        return
    data = data.replace(
        {
            "classification": CAPTION.encode(),
            "columns": "商轉年度".encode(),
            "span": b'rowspan="2"',
            "power": b"1,000.25",
            "year": b"113",
            "footer": "合 計".encode(),
        }[change],
        {
            "classification": b"Wind",
            "columns": b"Personal contact",
            "span": b'rowspan="0"',
            "power": b"1,00.25",
            "year": b"Unknown",
            "footer": b"Other",
        }[change],
    )
    with pytest.raises(ValueError):
        read(data)


@pytest.mark.parametrize(
    "options", [{"limit": 0}, {"limit": 201}, {"after_row": -1}, {"after_row": 3}]
)
def test_partition_bounds(options):
    with pytest.raises(ValueError):
        read(document(), **options)


def test_duplicate_named_blocks_remain_separate_candidates():
    result = read(document())
    assert len(result["candidates"]) == 2
    assert (
        result["candidates"][0]["plant_name_native"] == result["candidates"][1]["plant_name_native"]
    )


def test_unfinished_span_is_not_carried_to_footer():
    with pytest.raises(ValueError, match="rowspan"):
        read(document().replace(b'rowspan="2"', b'rowspan="3"'))
