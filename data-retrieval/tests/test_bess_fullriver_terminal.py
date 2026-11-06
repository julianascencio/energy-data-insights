"""Synthetic terminal claims do not imply a torque value or certification."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.fullriver import parse_terminal_case

TEXT = """EXACT-12
C100 100 AH    Terminal Type M6 Button Terminal
Resistance 5mΩ    Case Type ABS Plastic - Flame Res. Rating UL94-HB
\fTERMINAL TORQUE: generic table
"""


def test_exact_claim_boundary():
    row = parse_terminal_case(TEXT, model="EXACT-12")
    assert row["terminal_type_native"] == "M6 Button Terminal"
    assert row["flame_resistance_claim"] == "UL94-HB"
    assert "not independently verified" in row["claim_basis"]
    assert "Not extracted" in row["torque"]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "\fEXACT-12",
        TEXT.replace("EXACT-12", "EXACT-12B"),
        TEXT.replace("M6 Button Terminal", "M10"),
        TEXT.replace("UL94-HB", "UL94-V0"),
        TEXT.replace("\f", "Terminal Type M8\n\f"),
        TEXT.replace("Case Type", "Case"),
    ],
)
def test_identity_or_unreviewed_claim_fails(text):
    with pytest.raises(ValueError):
        parse_terminal_case(text, model="EXACT-12")
