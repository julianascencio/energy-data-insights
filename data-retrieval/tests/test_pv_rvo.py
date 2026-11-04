"""Synthetic RVO fixtures exercise privacy, identity, units and resumable staging."""

import hashlib
import io

import pytest
from openpyxl import Workbook

from energy_data_retrieval.pv_catalogue.rvo import read_rvo_workbook

HEADERS = [
    "SDE ronde",
    "Referentie",
    "Categorie",
    "Thema",
    "Aanvrager Naam",
    "Adres",
    "Postcode",
    "Plaats lokatie",
    "Gemeente",
    "RES-regio",
    "Provincie",
    "Looptijd [jr.]",
    "Maximale subsidie [€]",
    "Opstelling zon-pv",
    "Gerealiseerd",
    "Ingebruikname jaar ",
]


def source(rows, headers=None, extra_sheet=False):
    book = Workbook()
    book.active.title = "Projecten in beheer (synthetic)"
    book.active.append(["Synthetic test data; not publisher evidence"])
    book.active.append(headers or HEADERS)
    for update in rows:
        row = {
            "Referentie": "SDE0000001",
            "Categorie": "Zon",
            "Thema": "2024 Zon-PV >= 1 MWp veld",
            "Aanvrager Naam": "Synthetic recipient",
            "Adres": "Private address",
            "Postcode": "Private postcode",
            "Plaats lokatie": "Private locality",
            "Gemeente": "Synthetic municipality",
            "Provincie": "Synthetic province",
            "Looptijd [jr.]": 15,
            "Maximale subsidie [€]": 500000,
            "Opstelling zon-pv": "Veldsysteem",
            "Gerealiseerd": "Ja",
            "Ingebruikname jaar": 2020,
            **update,
        }
        book.active.append([row.get(h.strip()) for h in (headers or HEADERS)])
    if extra_sheet:
        book.create_sheet("Projecten in beheer (ambiguous)")
    stream = io.BytesIO()
    book.save(stream)
    data = stream.getvalue()
    return data, hashlib.sha256(data).hexdigest()


def read(rows, **kwargs):
    content, sha = source(rows)
    return read_rvo_workbook(content, sha256=sha, **kwargs)


def test_preserves_decision_evidence_without_plant_or_financial_inference():
    result = read([{}])
    row = result["candidates"][0]
    assert row["maximum_subsidy_eur"] == 500000
    assert row["realised_native"] == "Ja" and row["in_use_year_native"] == 2020
    assert row["accepted"] is False and result["accepted_records"] == 0
    assert (
        not {"capex", "capacity_dc_mw", "capacity_ac_mw", "status", "commissioning_year"}
        & row.keys()
    )
    assert "Private" not in str(result) and "Synthetic recipient" not in str(result)


@pytest.mark.parametrize("field", ["Aanvrager Naam", "Adres", "Postcode", "Plaats lokatie"])
def test_anonymised_decision_entirely_withheld(field):
    result = read([{field: "***"}])
    assert result["candidates"] == [] and result["counts"]["anonymised_pv"] == 1


def test_explicit_pv_required_and_mountings_partitioned():
    result = read(
        [
            {"Referentie": "A", "Thema": "Solar"},
            {"Referentie": "B", "Categorie": "Zon warmte", "Thema": "Solar thermal"},
            {"Referentie": "C", "Opstelling zon-pv": "Daksysteem"},
            {"Referentie": "D", "Opstelling zon-pv": "Watersysteem"},
        ]
    )
    assert [r["decision_reference"] for r in result["candidates"]] == ["D"]
    assert result["counts"]["non_pv_or_unproven"] == 2
    assert result["counts"]["other_pv_mountings"] == 1


def test_cursor_orders_exact_awards_without_merging_same_municipality():
    result = read([{"Referentie": "C"}, {"Referentie": "A"}, {"Referentie": "B"}], limit=1)
    assert result["next_after_reference"] == "A" and result["remaining_after_partition"] == 2
    second = read(
        [{"Referentie": "C"}, {"Referentie": "A"}, {"Referentie": "B"}], after_reference="A"
    )
    assert [r["decision_reference"] for r in second["candidates"]] == ["B", "C"]
    assert read([{}], after_reference="Z")["next_after_reference"] == "Z"


def test_repeated_award_requires_review_even_when_content_identical():
    with pytest.raises(ValueError, match="repeated decision"):
        read([{}, {}])


@pytest.mark.parametrize(
    "kwargs", [{"limit": 0}, {"limit": 1001}, {"limit": True}, {"after_reference": ""}]
)
def test_bounded_partition_arguments(kwargs):
    with pytest.raises(ValueError):
        read([{}], **kwargs)


@pytest.mark.parametrize("amount", [-1, True, "500,00"])
def test_bad_grant_cells_are_not_repaired(amount):
    with pytest.raises(ValueError, match="native nonnegative"):
        read([{"Maximale subsidie [€]": amount}])


def test_checksum_schema_and_worksheet_guards():
    content, sha = source([{}])
    with pytest.raises(ValueError, match="checksum"):
        read_rvo_workbook(content, sha256="bad")
    for headers in [HEADERS[:-1], [*HEADERS, "Referentie"]]:
        content, sha = source([], headers=headers)
        with pytest.raises(ValueError, match="schema"):
            read_rvo_workbook(content, sha256=sha)
    content, sha = source([{}], extra_sheet=True)
    with pytest.raises(ValueError, match="worksheet"):
        read_rvo_workbook(content, sha256=sha)


def test_geometry_extra_columns_and_recipients_never_leave_projection():
    content, sha = source(
        [{"Latitude": 52.0, "Longitude": 5.0}], headers=[*HEADERS, "Latitude", "Longitude"]
    )
    result = read_rvo_workbook(content, sha256=sha)
    assert "Latitude" not in str(result) and "Longitude" not in str(result)
    assert "Private" not in str(result)


@pytest.mark.parametrize("update", [{"Gemeente": 123}, {"Ingebruikname jaar": True}])
def test_changed_text_and_year_types_are_held(update):
    with pytest.raises(ValueError, match="type changed"):
        read([update])
