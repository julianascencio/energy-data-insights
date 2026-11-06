"""Offline staging for the reviewed five-column ATESS HPS/PCS English tables.

Input is ``pdftotext -layout`` output. Never fetch, upsert, infer stored energy,
or equate kVA, DC limits, rectifier limits and rated AC output. Common merged
cells require visual review; certificates and optional features remain manual.
"""

import re
import unicodedata
from itertools import pairwise

MODELS = {
    "HPS": ("HPS30", "HPS50", "HPS100", "HPS120", "HPS150"),
    "PCS": ("PCS100", "PCS250", "PCS500", "PCS630", "PCS1000"),
}


def _number(value: str, unit: str) -> float:
    match = re.fullmatch(r"(\d+(?:\.\d+)?)" + re.escape(unit), value)
    if not match:
        raise ValueError(f"Expected explicit {unit}: {value}")
    return float(match[1])


def _row(section: str, label: str) -> list[str]:
    matches = re.findall(r"^\s*" + re.escape(label) + r" {2,}(.+)$", section, re.M)
    if len(matches) != 1:
        raise ValueError(f"Missing or repeated row: {label}")
    values = re.split(r" {2,}", matches[0].strip())
    if len(values) != 5:
        raise ValueError(f"Expected five model cells: {label}")
    return values


def parse_table(text: str, *, family: str) -> list[dict]:
    """Stage exact model observations; reject shifted headers, rows and units."""
    if family not in MODELS:
        raise ValueError("Unreviewed family")
    text = unicodedata.normalize("NFKC", text)
    headers = [line.split() for line in text.splitlines() if line.split() == list(MODELS[family])]
    if len(headers) != 1:
        raise ValueError("Missing or repeated exact ordered model header")
    sections = [
        "AC(on-grid)",
        "AC(off-grid)",
        "DC (Battery and PV)" if family == "HPS" else "DC (Battery)",
        "General Information",
        "Communication",
        "Certificate",
    ]
    positions = []
    for heading in sections:
        matches = list(re.finditer(r"^\s*" + re.escape(heading) + r"\s*$", text, re.M))
        if len(matches) != 1:
            raise ValueError(f"Missing or repeated section: {heading}")
        positions.append(matches[0].start())
    if positions != sorted(positions):
        raise ValueError("Reordered sections")
    ac, off, dc, general = [text[a:b] for a, b in pairwise(positions)][:4]
    columns = {
        "rated_ac_kw": (_row(ac, "Rated power"), "kW"),
        "apparent_ac_kva": (_row(ac, "Apparent power"), "kVA"),
        "rated_ac_v": (_row(ac, "Rated voltage"), "V"),
        "rated_ac_a": (_row(ac, "Rated current"), "A"),
        "off_grid_rated_kw": (_row(off, "Rated power"), "kW"),
        "weight_kg": (_row(general, "Weight"), "kg"),
    }
    if family == "HPS":
        for key, label, unit in [
            ("max_dc_charge_kw", "Max. charge power", "kW"),
            ("max_dc_discharge_kw", "Max. discharge power", "kW"),
            ("max_charge_a", "Max. charge current", "A"),
            ("max_discharge_a", "Max. discharge current", "A"),
            ("max_pv_kwp", "Max. PV power", "kWp"),
            ("ac_input_kva", "AC input", "kVA"),
        ]:
            columns[key] = (_row(ac if key == "ac_input_kva" else dc, label), unit)
    else:
        columns["max_rectified_kw"] = (_row(ac, "Max. rectified power"), "kW")
        columns["rated_dc_kw"] = (_row(dc, "Rated power"), "kW")
        columns["maximum_conversion_efficiency_pct"] = (_row(general, "Max. efficiency"), "%")
    voltages = _row(dc, "Battery voltage range" if family == "HPS" else "Voltage range")
    dimensions = _row(general, "Dimension (W/H/D)" if family == "HPS" else "Dimension(W/H/D)mm")
    transformers = _row(general, "Build-in transformer")
    currents = _row(dc, "Max. charge/discharge current") if family == "PCS" else []
    results = []
    for i, model in enumerate(MODELS[family]):
        row = {"model": model, "locator": f"PDF page 2; exact {model} column"}
        row.update({key: _number(values[i], unit) for key, (values, unit) in columns.items()})
        voltage = re.fullmatch(r"(\d+)V-(\d+)V", voltages[i])
        dim = re.fullmatch(r"(\d+)/(\d+)/(\d+)(?:mm)?", dimensions[i])
        if not voltage or int(voltage[1]) >= int(voltage[2]) or not dim:
            raise ValueError(f"Invalid voltage/dimensions: {model}")
        row.update(
            dc_min_v=int(voltage[1]),
            dc_max_v=int(voltage[2]),
            width_mm=int(dim[1]),
            height_mm=int(dim[2]),
            depth_mm=int(dim[3]),
        )
        if transformers[i] not in {"Yes", "No"}:
            raise ValueError("Unrecognized transformer value")
        row["builtin_transformer"] = transformers[i] == "Yes"
        if currents:
            pair = currents[i].split("/")
            if len(pair) not in {1, 2}:
                raise ValueError("Ambiguous charge/discharge current")
            row["max_charge_a"] = _number(pair[0], "A")
            row["max_discharge_a"] = _number(pair[-1], "A")
            row["charge_discharge_current_as_printed"] = currents[i]
        results.append(row)
    return results


def parse_enerstack314_clusters(text: str) -> list[dict]:
    """Stage the nine published codes using the document's explicit n formulas.

    No Cartesian products, model-number capacity guesses, inferred power or module
    environmental specifications. Diagrams and shared conditions need human review.
    """
    from decimal import Decimal

    text = unicodedata.normalize("NFKC", text)
    if text.count("ATESS ESS-BM-51.2-314RPB-S") != 1:
        raise ValueError("Wrong or repeated exact component heading")
    if text.count("Battery cluster specification") != 1:
        raise ValueError("Missing or repeated cluster section")
    cluster = text.split("Battery cluster specification", 1)[1].split("Certificate", 1)[0]

    def cells(label):
        matches = re.findall(r"^\s*" + re.escape(label) + r" {2,}(.+)$", cluster, re.M)
        if len(matches) != 1:
            raise ValueError(f"Missing or repeated cluster row: {label}")
        return matches[0].split()

    codes = cells("Energy code")
    expected = ["BS96", "BS112", "BS128", "BS144", "BS160", "BS176", "BS192", "BS208R", "BS225"]
    if codes != expected:
        raise ValueError("Changed exact energy-code columns")
    counts, weights = cells("Module Number"), cells("Weight(kg)")
    if len(counts) != 9 or len(weights) != 9 or not all(x.isdigit() for x in counts + weights):
        raise ValueError("Invalid count/weight alignment")
    if list(map(int, counts)) != list(range(6, 15)):
        raise ValueError("Changed module configurations")
    flat = " ".join(cluster.split())
    for required in [
        "16.076n (n=Module Number)",
        "51.2n (n=Module Number)",
        "44.8n~57.6n (n=Module Number)",
    ]:
        if required not in flat:
            raise ValueError("Missing explicit per-module formula")
    result = []
    for code, count, weight in zip(codes, counts, weights, strict=True):
        n = int(count)
        result.append(
            {
                "energy_code": code,
                "module_count": n,
                "weight_kg": int(weight),
                "nominal_energy_kwh": float(Decimal("16.076") * n),
                "nominal_voltage_v": float(Decimal("51.2") * n),
                "voltage_min_v": float(Decimal("44.8") * n),
                "voltage_max_v": float(Decimal("57.6") * n),
                "calculation_basis": (
                    "Explicit source formulas: energy=16.076n kWh; voltage=51.2n V; "
                    "range=44.8n..57.6n V, n=published module count"
                ),
                "locator": f"PDF page 2; {code} column and common cluster formula rows",
            }
        )
    return result
