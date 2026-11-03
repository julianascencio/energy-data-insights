# ruff: noqa: RUF001
# Preserve exact Chinese OEM table labels and unit glyphs.
"""Stage reviewed Chinese Sinexcel two-page PCS sheets; never infer AC watts.

Input is local UTF-8 ``pdftotext -layout`` output. The caller must review the
original table, source terms and exact model identities before catalogue upsert.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

MODEL_ROWS = ("额定交流功率", "交流过载能力", "最大直流功率", "直流电压范围", "允许电网电压")
SHARED_ROWS = (
    "接线方式",
    "允许电网频率",
    "总电流谐波畸变率",
    "功率因数",
    "稳压精度",
    "稳流精度",
    "最大转换效率",
    "尺寸（宽×高×深）",
    "重量",
    "噪声",
    "防护等级",
    "允许环境温度",
    "冷却方式",
    "允许相对湿度",
    "允许海拔高度",
    "通讯接口",
    "通讯协议",
    "BMS接入",
)
OPTION_ROWS = (
    "直流接入路数",
    "每路最大直流电流",
    "直流最大电流",
    "最大直流电流",
    "额定功率",
    "输入电压范围",
    "最大输入电流",
)


def parse_sinexcel_pcs_text(content: bytes, *, expected_models: list[str]) -> list[dict[str, Any]]:
    """Return table observations with units and source labels, without network I/O.

    Explicitly shared rows may span model columns. Rating rows may not: missing
    cells fail instead of copying the neighbouring model's specification.
    Optional DC connection arrangements remain strings, never synthetic variants.
    """
    text = content.decode("utf-8-sig")
    pages = text.split("\f")
    if len(pages) < 2 or "产品参数" not in pages[1]:
        raise ValueError("Expected parameter table on PDF page 2")
    table = pages[1]
    header = re.search(r"^型号[ \t]+(.+)$", table, re.MULTILINE)
    if not header:
        raise ValueError("Missing exact model header")
    models = header.group(1).split()
    if models != expected_models or len(set(models)) != len(models):
        raise ValueError("Unexpected or duplicate exact models")
    if not models or any(not re.fullmatch(r"PWS[12]-[0-9]+[A-Z0-9-]+", m) for m in models):
        raise ValueError("Unsupported model layout")
    fields: dict[str, list[str]] = {}
    for label in (*MODEL_ROWS, *SHARED_ROWS, *OPTION_ROWS):
        matches = re.findall(r"^" + re.escape(label) + r"[ \t]+([^\n]+)$", table, re.MULTILINE)
        if len(matches) > 1:
            raise ValueError(f"Duplicate table row: {label}")
        if not matches:
            if label in MODEL_ROWS or label in SHARED_ROWS:
                raise ValueError(f"Missing table row: {label}")
            continue
        value = matches[0].strip()
        if len(models) == 1:
            fields[label] = [value]
            continue
        cells = re.split(r"\s{2,}", value)
        if len(cells) == 1 and label in SHARED_ROWS:
            cells *= len(models)
        if len(cells) != len(models):
            raise ValueError(f"Ambiguous column count: {label}")
        fields[label] = cells
    result = []
    for i, model in enumerate(models):
        observed = {label: values[i] for label, values in fields.items()}
        numeric = {}
        for label, unit, key in (
            ("额定交流功率", "kVA", "rated_ac_kva"),
            ("交流过载能力", "kVA", "overload_ac_kva"),
            ("最大直流功率", "kW", "maximum_dc_kw"),
            ("重量", "kg", "mass_kg"),
        ):
            match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*" + unit, observed[label])
            if not match or float(match.group(1)) <= 0:
                raise ValueError(f"Invalid value or unit: {label}")
            numeric[key] = float(match.group(1))
        voltage = re.fullmatch(r"(\d+)V?~(\d+)(?:（[^）]+）)?V(?:dc)?", observed["直流电压范围"])
        dimensions = re.fullmatch(r"(\d+)[*×](\d+)[*×](\d+)\s*mm", observed["尺寸（宽×高×深）"])
        if not voltage or int(voltage[1]) >= int(voltage[2]) or not dimensions:
            raise ValueError("Invalid voltage range or ordered dimensions")
        numeric.update(
            dc_min_v=int(voltage[1]),
            dc_max_v=int(voltage[2]),
            width_mm=int(dimensions[1]),
            height_mm=int(dimensions[2]),
            depth_mm=int(dimensions[3]),
        )
        result.append(
            {
                "model": model,
                "numeric": numeric,
                "reported_fields": observed,
                "locator": f"PDF page 2, 产品参数, exact model column {i + 1}",
                "extracted_text_sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return result
