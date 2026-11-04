"""Station-month identity, native units and calendar guards."""

import csv
import hashlib
import io

import pytest

from energy_data_retrieval.pv_catalogue.taipower import MONTHLY_HEADERS, read_taipower_monthly


def parse(rows, **kwargs):
    stream = io.StringIO(newline="")
    writer = csv.writer(stream)
    writer.writerow(MONTHLY_HEADERS)
    writer.writerows(rows)
    content = stream.getvalue().encode("utf-8-sig")
    return read_taipower_monthly(
        content,
        sha256=hashlib.sha256(content).hexdigest(),
        period_start=kwargs.pop("period_start", "2026-07"),
        period_end=kwargs.pop("period_end", "2026-09"),
        **kwargs,
    )


def row(month="07", name="甲太陽光電站", **changes):
    values = ["2026", month, name, "100.25", "12345", "3.97"]
    for key, value in changes.items():
        values[int(key)] = value
    return values


def test_native_station_month_values_and_capacity_changes_are_not_aggregated():
    x = parse([row(), row("08", **{"3": "116.5"})])
    assert x["source_rows"] == 2 and x["accepted_records"] == 0
    assert [r["installed_capacity_kw_native"] for r in x["candidates"]] == [100.25, 116.5]
    assert x["candidates"][0]["monthly_generation_kwh"] == 12345
    assert "capacity_ac_mw" not in str(x) and "annual_generation" not in str(x)


def test_exact_name_filter_cursor_and_complete_period_keys():
    rows = [row("08"), row(), row(name="乙光電")]
    first = parse(rows, station_names=["甲太陽光電站"], limit=1)
    assert first["remaining_after_partition"] == 1
    second = parse(rows, station_names=["甲太陽光電站"], after_key=first["next_after_key"])
    assert second["candidates"][0]["period"] == "2026-08"
    assert not parse(rows, period_start="2025-01", period_end="2025-12")["candidates"]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"period_start": "115-07"},
        {"period_end": "2026-13"},
        {"period_start": "2027-01"},
        {"limit": True},
        {"limit": 0},
        {"station_names": []},
        {"station_names": ["x", "x"]},
        {"station_names": [None]},
        {"after_key": ""},
    ],
)
def test_invalid_partition_arguments(kwargs):
    with pytest.raises(ValueError):
        parse([row()], **kwargs)


@pytest.mark.parametrize(
    "changes", [{"0": "115"}, {"1": "13"}, {"3": "-1"}, {"4": "nan"}, {"5": "inf"}]
)
def test_calendar_and_native_numeric_values_fail_closed(changes):
    with pytest.raises(ValueError):
        parse([row(**changes)])


def test_duplicate_unproven_station_and_unknown_crosswalk_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        parse([row(), row()])
    with pytest.raises(ValueError, match="explicitly PV"):
        parse([row(name="Solar")])
    with pytest.raises(ValueError, match="station absent"):
        parse([row()], station_names=["乙光電"])
    with pytest.raises(ValueError, match="cursor absent"):
        parse([row()], after_key="2026-01|甲太陽光電站")


def test_checksum_schema_extra_fields_and_record_width_guards():
    with pytest.raises(ValueError, match="checksum"):
        read_taipower_monthly(b"x", sha256="0" * 64, period_start="2026-01", period_end="2026-12")
    with pytest.raises(ValueError, match="schema"):
        read_taipower_monthly(
            b"x",
            sha256=hashlib.sha256(b"x").hexdigest(),
            period_start="2026-01",
            period_end="2026-12",
        )
    with pytest.raises(ValueError, match="width"):
        parse([[*row(), "PRIVATE ADDRESS"]])


def test_reviewed_duplicate_periods_are_all_held_without_choosing_values():
    rows = [row(), row(**{"4": "999"}), row("08")]
    x = parse(rows, reviewed_duplicate_keys=["2026-07|甲太陽光電站"])
    assert x["held_duplicate_period_groups"] == 1
    assert len(x["held_duplicate_observations"]) == 2
    assert [r["monthly_generation_kwh"] for r in x["held_duplicate_observations"]] == [12345, 999]
    assert len(x["candidates"]) == 1 and x["candidates"][0]["period"] == "2026-08"
    with pytest.raises(ValueError, match="held duplicate"):
        parse(
            rows, reviewed_duplicate_keys=["2026-07|甲太陽光電站"], after_key="2026-07|甲太陽光電站"
        )


@pytest.mark.parametrize(
    "keys",
    [
        ["2025-01|甲太陽光電站"],
        ["2026-07|甲太陽光電站", "2025-01|甲太陽光電站"],
        ["x", "x"],
        [None],
    ],
)
def test_stale_incomplete_or_malformed_duplicate_allowlists_fail_closed(keys):
    with pytest.raises(ValueError):
        parse([row(), row(**{"4": "999"})], reviewed_duplicate_keys=keys)
