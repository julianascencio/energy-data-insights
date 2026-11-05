"""NSW parsing must preserve planning scope and refuse silent schema drift."""

import hashlib

import pytest

from energy_data_retrieval.pv_catalogue.nsw import read_nsw_renewable_tracker


def document(**changes):
    values = {
        "Project": "Example Solar Farm",
        "Project type": "Solar Farm",
        "Status": "Approved",
        "Location": "Regional label",
        "Renewable Energy Zone": "N/A",
        "Generating capacity (MW)": "80 MW",
        "Storage capacity (MW/MWh)": "20 MW / 40 MWh",
        "Modifications": "N/A",
        "Number of households capable of being powered": "100",
        "Carbon emissions avoided in first year (Tonnes CO2e)": "200",
        "Potential number of jobs created": "300",
        "Approval date": "8/10/2018",
        "Approved by": "Minister",
        "Referred to Independent Planning Commission": "No",
    }
    values.update(changes)
    return (
        "This table was last updated on 6 August 2026.<table>"
        + "<tr>"
        + "".join(f"<td>{values[k]}</td>" for k in ["Project", "Project type", "Status"])
        + "<td>Details</td></tr>"
        + "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in values.items())
        + "</table>"
    ).encode()


def read(data):
    return read_nsw_renewable_tracker(
        data, sha256=hashlib.sha256(data).hexdigest(), as_of="2026-08-06"
    )


def test_planning_scope_and_australian_date_preserved():
    row = read(document())[0]
    assert row["approval_date"] == "2018-10-08"
    assert row["generating_capacity_native"] == "80 MW"
    assert row["storage_capacity_native"] == "20 MW / 40 MWh"
    assert "Unspecified" in row["generating_capacity_basis"]
    assert row["review_status"].startswith("Unaccepted")
    assert "capacity_ac_mw" not in row and "technology" not in row


def test_checksum_and_snapshot_are_required():
    data = document()
    with pytest.raises(ValueError, match="checksum"):
        read_nsw_renewable_tracker(data, sha256="0" * 64, as_of="2026-08-06")
    with pytest.raises(ValueError, match="as-of"):
        read_nsw_renewable_tracker(
            data, sha256=hashlib.sha256(data).hexdigest(), as_of="2026-08-07"
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"Unknown column": "value"},
        {"Status": "Current"},
        {"Approval date": "7/8/2026"},
        {"Approval date": "2018"},
        {"Location": ""},
    ],
)
def test_unknown_schema_status_or_dates_rejected(changes):
    with pytest.raises(ValueError):
        read(document(**changes))


def test_duplicate_card_names_are_not_merged():
    rows = read(document() + document())
    assert len(rows) == 2 and all(r["source_name_count"] == 2 for r in rows)


def test_non_solar_cards_are_not_pv_candidates():
    assert len(read(document() + document(**{"Project type": "Wind Farm"}))) == 1


def test_duplicate_column_is_rejected():
    data = document().replace(b"</table>", b"<tr><th>Status</th><td>Approved</td></tr></table>")
    with pytest.raises(ValueError, match="Duplicate"):
        read(data)


def test_pending_project_has_no_invented_approval():
    row = read(document(**{"Status": "Under assessment", "Approval date": "N/A"}))[0]
    assert row["approval_date"] is None and row["source_status"] == "Under assessment"
    with pytest.raises(ValueError):
        read(document(**{"Approval date": "N/A"}))


def test_summary_inventory_detects_missing_detail_card():
    data = document()
    data = data.replace(
        b"<th>Project</th><td>Example Solar Farm</td>",
        b"<th>Project</th><td>Different Solar Farm</td>",
    )
    with pytest.raises(ValueError, match="inventory"):
        read(data)
