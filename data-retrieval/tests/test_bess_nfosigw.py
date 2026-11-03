"""Synthetic ranking controls: identity, funding and technology boundaries."""

import runpy
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from energy_data_retrieval.bess_catalogue.nfosigw import parse_ranking


def row(rank="1", application="10/2025", title="Bateryjny magazyn Example"):
    return {
        "page": 1,
        "cells": [
            rank,
            "Dotacja",
            application,
            "BESS Example sp. z o.o.",
            title,
            "śląskie",
            "1 234 567,89",
            "500 000,00",
            "-------------",
            "29",
        ],
    }


def test_not_an_award_or_operating_confirmation():
    result = parse_ranking([row()])[0]
    assert result["total_cost_pln"] == 1234567.89
    assert result["recommended_funding_pln"] is None
    assert result["battery_explicit_in_title"]
    assert result["status"] == "announced"
    assert result["review_required"]


def test_applicant_name_does_not_classify_technology():
    assert not parse_ranking([row(title="Magazyn energii Example")])[0]["battery_explicit_in_title"]


def test_loan_and_grant_are_not_automatically_merged():
    second = row("2", "11/2025")
    second["cells"][1] = "Pożyczka"
    assert len(parse_ranking([row(), second])) == 2


@pytest.mark.parametrize(
    "column,value", [(0, "2"), (1, "Award"), (2, "10/2026"), (6, "1.234.567,89"), (9, "unknown")]
)
def test_layout_and_value_drift_fails(column, value):
    changed = deepcopy(row())
    changed["cells"][column] = value
    with pytest.raises(ValueError):
        parse_ranking([changed])


def test_duplicate_application_fails():
    with pytest.raises(ValueError):
        parse_ranking([row(), row("2")])


@pytest.mark.parametrize("help_requested", [True, False])
def test_cli_without_optional_pdf_dependency(monkeypatch, capsys, help_requested):
    script = Path(__file__).resolve().parents[2] / "scripts" / "stage_bess_nfosigw.py"
    main = runpy.run_path(str(script))["main"]

    def unavailable(name):
        raise ModuleNotFoundError(name=name)

    monkeypatch.setitem(main.__globals__, "import_module", unavailable)
    arguments = ["--help"] if help_requested else ["source.pdf", "--output", "staged.jsonl"]
    monkeypatch.setattr(sys, "argv", [str(script), *arguments])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == (0 if help_requested else 2)
    captured = capsys.readouterr()
    if help_requested:
        assert "--output" in captured.out
    else:
        assert "uv run --with pdfplumber" in captured.err
