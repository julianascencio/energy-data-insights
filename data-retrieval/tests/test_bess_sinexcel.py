# ruff: noqa: RUF001
# Preserve exact Chinese OEM table labels and unit glyphs.
"""Synthetic tables test unit separation and model-column boundaries."""

import pytest

from energy_data_retrieval.bess_oem_catalogue.sinexcel import (
    SHARED_ROWS,
    parse_sinexcel_pcs_text,
)


def sheet() -> bytes:
    rows = [
        "Synthetic features\f产品参数",
        "型号  PWS1-111KTL-H  PWS1-222KTL-H",
        "额定交流功率  111kVA  222kVA",
        "交流过载能力  121kVA  242kVA",
        "最大直流功率  130kW  260kW",
        "直流电压范围  500~900V  600~1000V",
        "允许电网电压  380V  400V",
    ]
    replacements = {"重量": "456kg", "尺寸（宽×高×深）": "1000×2000×500 mm"}
    rows.extend(
        f"{label}  {replacements.get(label, 'synthetic shared observation')}"
        for label in SHARED_ROWS
    )
    return "\n".join(rows).encode()


def test_distinct_columns_shared_dimensions_and_kw_not_kva():
    rows = parse_sinexcel_pcs_text(sheet(), expected_models=["PWS1-111KTL-H", "PWS1-222KTL-H"])
    assert [r["numeric"]["rated_ac_kva"] for r in rows] == [111, 222]
    assert [r["numeric"]["maximum_dc_kw"] for r in rows] == [130, 260]
    assert rows[1]["numeric"]["dc_min_v"] == 600
    assert rows[0]["numeric"]["height_mm"] == 2000
    assert rows[0]["numeric"]["depth_mm"] == 500
    assert "active_ac_kw" not in rows[0]["numeric"]


@pytest.mark.parametrize(
    "before,after",
    [
        ("111kVA  222kVA", "111kVA"),
        ("130kW  260kW", "130kVA  260kVA"),
        ("500~900V", "900~500V"),
        ("重量  456kg", "重量  456lb"),
    ],
)
def test_fail_closed_on_missing_columns_units_and_ranges(before, after):
    with pytest.raises(ValueError):
        parse_sinexcel_pcs_text(
            sheet().replace(before.encode(), after.encode()),
            expected_models=["PWS1-111KTL-H", "PWS1-222KTL-H"],
        )


def test_exact_model_reordering_rejected():
    with pytest.raises(ValueError, match="exact models"):
        parse_sinexcel_pcs_text(sheet(), expected_models=["PWS1-222KTL-H", "PWS1-111KTL-H"])
