"""Stage reviewed Pylontech Force-L1 v2.3 / Force-L2 v2.2 system tables offline."""

import re


def parse_force(text: str, *, family: str) -> list[dict[str, object]]:
    """Preserve explicit configurations and current classes; infer no active power.

    Input is pdftotext -layout output. Mechanical dimensions and the separate
    module tables require review outside this staging adapter.
    """
    versions = {
        "Force-L1": ("20P1FL0302", "FL48074", "FC0048-100S", 6, "2.3"),
        "Force-L2": ("20P2FL0301", "FL4874M", "FC0048M-100S", 3, "2.2"),
    }
    if family not in versions:
        raise ValueError("Unreviewed family")
    code, module, controller, count, revision = versions[family]
    if (
        family + " Operation Manual" not in text
        or code not in text
        or not re.search(r"Information Version:\s*" + re.escape(revision) + r"(?![\d.])", text)
    ):
        raise ValueError("Unreviewed manual identity/revision")
    pages = [p for p in text.split("\f") if "Battery System Capacity(kWh)" in p]
    if len(pages) != 1:
        raise ValueError("Missing or repeated system table")
    page = pages[0]

    def values(label: str, expected: int) -> list[float]:
        matches = [
            line.split(")", 1)[-1].strip()
            for line in page.splitlines()
            if re.sub(r"\s+", "", line).startswith(re.sub(r"\s+", "", label))
        ]
        if len(matches) != 1:
            raise ValueError("Missing or duplicate row: " + label)
        tokens = matches[0].split()
        if len(tokens) != expected or any(not re.fullmatch(r"\d+(?:\.\d+)?", t) for t in tokens):
            raise ValueError("Changed numeric columns: " + label)
        return [float(t) for t in tokens]

    energies = values("Battery System Capacity(kWh)", count)
    quantities = values("Battery Module Quantity(pcs)", count)
    if quantities != list(range(2, count + 2)):
        raise ValueError("Changed configuration order or duplicate module count")
    ah = (
        values("Battery System Capacity(AH)", count)
        if family == "Force-L1"
        else values("Battery System Capacity(Ah)", count)
    )
    charge = values("Battery System Charge Current(Amps, Standard)", count)
    discharge = values("Battery System Discharge Current(Amps, Standard)", count)
    normal_charge = values(
        "Battery System Charge Current(Amps, Normal)", 2 if count == 6 else count
    )
    normal_discharge = values(
        "Battery System Discharge Current(Amps, Normal)", 2 if count == 6 else count
    )
    if count == 6:
        normal_charge = normal_charge[:1] + normal_charge[1:] * 5
        normal_discharge = normal_discharge[:1] + normal_discharge[1:] * 5
    peak_charge = values("Battery System Charge Current(Amps, Max.@15S)", 1)[0]
    peak_label = (
        "Battery System Discharge Current(Amps, Max.)"
        if count == 6
        else "Battery System Discharge Current(Amps, Max.@15S)"
    )
    peak_discharge = values(peak_label, 1)[0]
    mass = values("Weight (kg)", count)
    voltage = values("Battery System Voltage(Vdc)", 1)[0]
    upper = values("Battery System Charge Upper-Voltage(Vdc)", 1)[0]
    lower = values("Battery System Discharge lower-Voltage(Vdc)", 1)[0]
    for label, expected in [
        ("Battery Module Name", module),
        ("Battery Controller Name", controller),
    ]:
        rows = [line.strip() for line in page.splitlines() if line.strip().startswith(label)]
        if len(rows) != 1 or rows[0].split()[-1] != expected:
            raise ValueError("Changed component identity")
    if not 0 < lower < voltage < upper or any(x <= 0 for x in energies + mass):
        raise ValueError("Invalid ratings")
    return [
        {
            "family": family,
            "module_model": module,
            "controller_model": controller,
            "module_count": int(quantities[i]),
            "energy_kwh_reported": energies[i],
            "capacity_ah": ah[i],
            "nominal_voltage_v": voltage,
            "charge_upper_voltage_v": upper,
            "discharge_lower_voltage_v": lower,
            "charge_standard_a": charge[i],
            "discharge_standard_a": discharge[i],
            "charge_normal_a": normal_charge[i],
            "discharge_normal_a": normal_discharge[i],
            "charge_peak_a": peak_charge,
            "charge_peak_seconds": 15,
            "discharge_peak_a": peak_discharge,
            "discharge_peak_seconds": None if count == 6 else 15,
            "weight_kg": mass[i],
        }
        for i in range(count)
    ]
