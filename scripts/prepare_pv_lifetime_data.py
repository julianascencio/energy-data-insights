"""Extract attributed numerical facts from the verified Zenodo v1.0.0 archive.

Download https://zenodo.org/records/14524159/files/Shared_data_results.zip?download=1
and pass --archive. Uses only the standard library, does not redistribute the
workbooks, and never overwrites or repairs their contents. No network at runtime.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

NS = {"s": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
ARCHIVE_MD5 = "b19a01369228f92769096a5a45965b1f"
MODULE_FILE = "Module degradation results/Indoor_module_degradation_results.xlsx"
SYSTEM_FILE = "System PLR results/Outdoor_PLR_results.xlsx"


def _cells(content: bytes, sheet_name: str) -> dict:
    with ZipFile(io.BytesIO(content)) as workbook:
        meta = ET.fromstring(workbook.read("xl/workbook.xml"))
        first = meta.find("s:sheets/s:sheet", NS)
        if first is None or first.attrib["name"] != sheet_name:
            raise ValueError("Unexpected first worksheet")
        shared = []
        if "xl/sharedStrings.xml" in workbook.namelist():
            root = ET.fromstring(workbook.read("xl/sharedStrings.xml"))
            shared = ["".join(si.itertext()) for si in root]
        root = ET.fromstring(workbook.read("xl/worksheets/sheet1.xml"))
        result = {}
        for cell in root.findall(".//s:sheetData/s:row/s:c", NS):
            value = cell.find("s:v", NS)
            if value is not None and value.text is not None:
                kind = cell.attrib.get("t")
                result[cell.attrib["r"]] = shared[int(value.text)] if kind == "s" else value.text
            elif cell.attrib.get("t") == "inlineStr":
                result[cell.attrib["r"]] = "".join(cell.itertext())
        return result


def extract(archive: Path, output: Path) -> None:
    """Validate the source version, retain cell addresses and write small tables."""
    raw = archive.read_bytes()
    if hashlib.md5(raw).hexdigest() != ARCHIVE_MD5:
        raise ValueError("Archive differs from verified Zenodo v1.0.0; review before extraction")
    with ZipFile(io.BytesIO(raw)) as bundle:
        modules, systems = bundle.read(MODULE_FILE), bundle.read(SYSTEM_FILE)
    cells = _cells(modules, "PM")
    groups = [
        (6, "Birg"),
        (15, "Tiergarten SM55"),
        (24, "Tiergarten SM55-HO"),
        (33, "Stored reference"),
        (42, "Jungfraujoch"),
        (51, "Mont-Soleil"),
        (60, "Moehlin"),
    ]
    rows = []
    for row, group in groups:
        if cells[f"B{row}"] != "Pmax" or cells[f"L{row}"] != "Pmax":
            raise ValueError("Unexpected Pmax layout")
        for nominal_col, measured_col in zip("CDEFGH", "MNOPQR", strict=True):
            measured = cells.get(f"{measured_col}{row}")
            if measured is None:
                continue
            nominal = cells.get(f"{nominal_col}{row}", "")
            is_reference = group == "Stored reference"
            rows.append(
                {
                    "group": group,
                    "module_id": cells[f"{measured_col}{row - 1}"],
                    "installation_year": int(cells[f"K{row}"]),
                    "dismantle_year": "" if is_reference else int(cells[f"K{row + 1}"]),
                    "nominal_power_w": "" if nominal == "-" else float(nominal),
                    "measured_power_w": float(measured),
                    "stored_reference": is_reference,
                    "nominal_cell": f"PM!{nominal_col}{row}",
                    "measured_cell": f"PM!{measured_col}{row}",
                    "dates_cells": f"PM!K{row}:K{row + 1}" if not is_reference else f"PM!K{row}",
                }
            )
    system_cells = _cells(systems, "Sheet1")
    system_rows = [
        {
            "site_id": system_cells[f"A{row}"],
            "plr_percent_per_year": float(system_cells[f"B{row}"]),
            "ci_low_percent_per_year": float(system_cells[f"C{row}"]),
            "ci_high_percent_per_year": float(system_cells[f"D{row}"]),
            "source_cells": f"Sheet1!A{row}:D{row}",
        }
        for row in range(2, 8)
    ]
    output.mkdir(parents=True, exist_ok=True)
    for name, records in (("module_measurements.csv", rows), ("system_plr.csv", system_rows)):
        with (output / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(records[0]))
            writer.writeheader()
            writer.writerows(records)
    provenance = {
        "dataset_doi": "10.5281/zenodo.14524159",
        "paper_doi": "10.1039/D4EL00040D",
        "creators": ["Hugo Quest", "Ebrar Özkalay", "Anika Gassner"],
        "dataset_version": "1.0.0",
        "dataset_publication_date": "2024-12-19",
        "accessed_date": "2026-11-03",
        "license": "CC-BY-4.0 (Zenodo API metadata. Paper is separately CC-BY-3.0.)",
        "source_url": "https://zenodo.org/records/14524159",
        "archive_md5": ARCHIVE_MD5,
        "archive_sha256": hashlib.sha256(raw).hexdigest(),
        "workbooks_sha256": {
            MODULE_FILE: hashlib.sha256(modules).hexdigest(),
            SYSTEM_FILE: hashlib.sha256(systems).hexdigest(),
        },
        "modifications": "Numerical cells extracted to CSV; source workbooks unchanged.",
        "age_convention": (
            "Dismantle minus installation year, exactly as recorded in PM; integer years."
        ),
        "limitations": [
            "Workbook dates imply exposures of 16, 24, 25, 30, 31 and 37 years. Do "
            "not replace with the paper's summary 30-35 years.",
            "The pre-publication workbook has six Tiergarten SM55 and six HO records; "
            "paper section 3.2.1.1 reports five and seven. No reassignment made.",
            "Outdoor v1.0.0 PLRs differ slightly from published text (e.g. -0.56 vs "
            "-0.55); these CSVs preserve the archive.",
            "Mont-Soleil has no numeric nameplate powers, so normalized power is unavailable.",
            "Stored references are not field-exposed modules. Nominal ratings are not "
            "measured initial powers.",
            "EL sheet contains cached #REF! values; only PM numeric measurements and "
            "outdoor PLRs are used.",
            "Selected module measurements do not provide fleet survival probabilities "
            "or complete failure histories.",
        ],
        "tables_sha256": {
            name: hashlib.sha256((output / name).read_bytes()).hexdigest()
            for name in ("module_measurements.csv", "system_plr.csv")
        },
    }
    (output / "provenance.json").write_text(
        json.dumps(provenance, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).resolve().parents[1]
        / "analysis/src/energy_analysis/pv_lifetime/data",
    )
    args = parser.parse_args()
    extract(args.archive, args.output)


if __name__ == "__main__":
    main()
