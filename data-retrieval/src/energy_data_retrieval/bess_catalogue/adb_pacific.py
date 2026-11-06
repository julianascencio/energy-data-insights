"""Offline factual partition from ADB TCS220320-2; no automatic project import."""

import re


def parse_cook_outer_islands(text: str) -> list[dict[str, object]]:
    """Stage the four explicit battery/PV rows in Table 3.3, printed page 23.

    Require the licensed 2022 report and chemistry/SoC qualification. The energy
    observation has unspecified gross/usable basis; no usable energy is derived.
    Other pages and similarly named island phases are deliberately not selected.
    """
    pages = text.split("\f")
    if len(pages) < 39 or "TCS220320-2" not in text or "AUGUST 2022" not in text:
        raise ValueError("Unreviewed report or page structure")
    page = " ".join(pages[38].split())
    required = (
        "Table 3.3 continued",
        "Subproject: 3",
        "sealed lead-acid technology",
        "Minimum state of charge",
        "approximately 50%",
        "All projects were completed in 2019",
    )
    if not all(token in page for token in required):
        raise ValueError("Unreviewed table conditions")
    rows = re.findall(
        r"(Mitiaro|Mauke|Atiu|Mangaia): (\d+) kW solar PV, "
        r"(\d+) kW/(\d+)(?: infrastructure)? kWh BESS",
        page,
    )
    if [r[0] for r in rows] != ["Mitiaro", "Mauke", "Atiu", "Mangaia"]:
        raise ValueError("Changed, missing or duplicate island rows")
    return [
        {
            "island": name,
            "solar_power_kw": int(solar),
            "battery_power_kw": int(power),
            "battery_energy_kwh": int(energy),
            "energy_basis": "unspecified",
            "chemistry": "sealed lead-acid",
            "minimum_soc_pct_approximate": 50,
            "reported_completion_year": 2019,
            "locator": "PDF page 39 / printed page 23, Table 3.3 subproject 3 and footnote a",
        }
        for name, solar, power, energy in rows
    ]
