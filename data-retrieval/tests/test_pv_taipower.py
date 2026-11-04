"""Synthetic CSV tests for Taipower identity, scope and privacy guards."""

import csv
import hashlib
import io

import pytest

from energy_data_retrieval.pv_catalogue.taipower import HEADERS, read_taipower_sites


def row(station="1", site="1", name="甲太陽光電發電站/Example Solar Power Station", **changes):
    values = [
        station,
        "太陽能/Solar",
        name,
        site,
        "roof",
        "MODULE-123",
        "100.5",
        "",
        "PRIVATE ADDRESS",
        "試運轉",
        "",
    ]
    for key, value in changes.items():
        values[int(key)] = value
    return values


def parse(rows, **kwargs):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(HEADERS)
    writer.writerows(rows)
    content = stream.getvalue().encode("utf-8-sig")
    return read_taipower_sites(content, sha256=hashlib.sha256(content).hexdigest(), **kwargs)


def test_groups_all_sites_without_capacity_sum_or_status_inference():
    result = parse([row(), row("-", "2", **{"6": "200", "9": "取得電業執照"})])
    group = result["candidates"][0]
    assert len(group["sites"]) == 2
    assert group["station_id"] == 1
    assert group["sites"][0]["installed_capacity_kw_native"] == 100.5
    assert group["sites"][0]["application_status_native"] == "試運轉"
    assert result["accepted_records"] == 0
    assert "PRIVATE ADDRESS" not in str(result)
    assert "capacity_ac_mw" not in str(result) and "capacity_dc_mw" not in str(result)


def test_cursor_retains_complete_groups_and_requires_same_revision_id():
    rows = [row("2", "2", "乙光電"), row(), row("-", "3")]
    first = parse(rows, limit=1)
    assert len(first["candidates"][0]["sites"]) == 2
    assert first["remaining_after_partition"] == 1
    second = parse(rows, after_station_id=1)
    assert second["candidates"][0]["station_id"] == 2
    with pytest.raises(ValueError, match="absent"):
        parse(rows, after_station_id=3)


def test_exact_technology_and_pv_name_required():
    result = parse([row(**{"1": "太陽能"}), row("2", "2")])
    assert result["counts"]["non_pv_rows"] == 1
    with pytest.raises(ValueError, match="insufficient"):
        parse([row(name="Generic Solar")])


@pytest.mark.parametrize(
    "rows",
    [[row(), row()], [row("-", "1")], [row(), row("1", "2", "乙光電")], [row(), row("2", "2")]],
)
def test_identity_collisions_and_orphan_groups_rejected(rows):
    with pytest.raises(ValueError):
        parse(rows)


@pytest.mark.parametrize("power", ["nan", "inf", "-1", "100kW", "", "1,000"])
def test_capacity_scope_is_not_repaired(power):
    with pytest.raises(ValueError, match="capacity"):
        parse([row(**{"6": power})])


def test_reject_wind_count_in_pv_and_changed_row_width():
    with pytest.raises(ValueError, match="wind-count"):
        parse([row(**{"7": "1"})])
    with pytest.raises(ValueError, match="width"):
        parse([row()[:-1]])


@pytest.mark.parametrize(
    "kwargs",
    [
        {"limit": 0},
        {"limit": True},
        {"limit": 1001},
        {"after_station_id": True},
        {"after_station_id": 0},
    ],
)
def test_invalid_partition_arguments(kwargs):
    with pytest.raises(ValueError):
        parse([row()], **kwargs)


def test_checksum_schema_blank_and_empty_partition():
    with pytest.raises(ValueError, match="checksum"):
        read_taipower_sites(b"x", sha256="0" * 64)
    with pytest.raises(ValueError, match="schema"):
        read_taipower_sites(b"x", sha256=hashlib.sha256(b"x").hexdigest())
    result = parse([row(), [""] * len(HEADERS)], after_station_id=1)
    assert result["counts"]["blank_rows"] == 1
    assert not result["candidates"] and result["next_after_station_id"] == 1
