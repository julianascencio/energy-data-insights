"""Synthetic BTL layout examples; no manufacturer documents redistributed."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.effekta import SOURCE_URL, parse_btl_table

HEADER = "BTL series AGM\nin Ah (C20) H (mm) Terminal\n"
ROW = "BTL 12-100 LX   12 100 325,5 170 213 216 31.6 M8\n"


def parse(text: str):
    return parse_btl_table(text.encode(), source_url=SOURCE_URL)


def test_preserves_decimal_comma_rate_and_terminal_height():
    row = parse(HEADER + ROW)[0]
    assert row["length_mm"] == 325.5
    assert row["case_height_mm"] == 213
    assert row["overall_height_mm"] == 216
    assert row["monobloc_capacity_ah_c20"] == 100
    assert "cell_capacity_ah" not in row
    assert "energy_capacity_mwh" not in row


def test_exact_suffixes_are_not_merged():
    rows = parse(HEADER + ROW.replace("100 LX", "120 L") + ROW.replace("100 LX", "120 S"))
    assert [r["model"] for r in rows] == ["BTL 12-120 L", "BTL 12-120 S"]


@pytest.mark.parametrize(
    "text",
    [
        HEADER + ROW + ROW,
        HEADER.replace("C20", "C10") + ROW,
        HEADER + ROW.replace("213 216", "213 200"),
        HEADER + ROW.replace("12 100", "24 100"),
        HEADER + ROW.replace("31.6", "0"),
        HEADER + ROW.replace("325,5", "325,5/330"),
        HEADER,
    ],
)
def test_ambiguous_or_changed_input_fails(text):
    with pytest.raises(ValueError):
        parse(text)


def test_rejects_unreviewed_source():
    with pytest.raises(ValueError):
        parse_btl_table((HEADER + ROW).encode(), source_url="https://example.org/table")
