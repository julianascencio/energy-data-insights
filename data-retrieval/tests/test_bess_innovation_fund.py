"""Synthetic inventory avoids redistributing source HTML."""

import pytest

from energy_data_retrieval.bess_catalogue.innovation_fund import parse_innovation_fund_html


def page(extra: str = "") -> bytes:
    header = (
        "<tr>"
        + "".join(
            f"<th>{x}</th>"
            for x in [
                "Project",
                "Type",
                "Category",
                "Sector",
                "Location",
                "Technology pathways",
                "Status",
            ]
        )
        + "</tr>"
    )
    rows = []
    for name, cat, tech, status in [
        ("Battery A", "Renewable energy", "Battery", "Grant signed"),
        ("Factory B", "Energy storage", "Battery manufacturing", "Terminated"),
    ]:
        cells = [
            f'<a href="https://example.test/1.pdf">{name}</a>',
            "Call",
            cat,
            "Sector",
            "Country",
            tech,
            status,
        ]
        rows.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>")
    return ("<table>" + header + "".join(rows) + extra + "</table>").encode()


def test_no_grant_to_lifecycle_or_category_to_bess_inference():
    rows = parse_innovation_fund_html(page())
    assert len(rows) == 2
    assert rows[1]["grant_status"] == "Terminated"
    assert all(r["review_required"] and r["shared_factsheet_url"] for r in rows)
    assert "status" not in rows[1]
    assert rows[0]["category"] == "Renewable energy"


def test_bad_header():
    with pytest.raises(ValueError, match="header"):
        parse_innovation_fund_html(page().replace(b"Technology pathways", b"Technology"))


def test_duplicate_identity():
    with pytest.raises(ValueError, match="Duplicate"):
        parse_innovation_fund_html(page().replace(b"Factory B", b"Battery A"))


def test_bad_row():
    with pytest.raises(ValueError, match="Incomplete"):
        parse_innovation_fund_html(page("<tr><td>Missing</td></tr>"))
