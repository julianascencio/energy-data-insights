# /// script
# dependencies = ["pdfplumber>=0.11,<0.12"]
# ///
"""Stage a local NFOŚiGW 12 December 2025 PDF; no network or automatic import.

Run with the repository package on PYTHONPATH and pdfplumber installed, or use
uv run --with pdfplumber. The output is intermediate factual data, not a census.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from energy_data_retrieval.bess_catalogue.nfosigw import parse_ranking


def main() -> None:
    import pdfplumber  # Optional source-extraction dependency.

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = []
    with pdfplumber.open(args.pdf) as pdf:
        if len(pdf.pages) != 24 or "Lista rankingowa" not in (pdf.pages[0].extract_text() or ""):
            raise ValueError("Not the reviewed 24-page ranking layout")
        for page_number, page in enumerate(pdf.pages, 1):
            for table in page.extract_tables():
                for cells in table:
                    if cells[0] and cells[0].strip().isdigit():
                        rows.append(
                            {
                                "page": page_number,
                                "cells": [" ".join((value or "").split()) for value in cells],
                            }
                        )
    staged = parse_ranking(rows)
    if len(staged) != 479:
        raise ValueError("Changed ranking length; review a new edition before proceeding")
    checksum = hashlib.sha256(args.pdf.read_bytes()).hexdigest()
    args.output.write_text(
        "".join(
            json.dumps({**row, "source_sha256": checksum}, ensure_ascii=False) + "\n"
            for row in staged
        )
    )


if __name__ == "__main__":
    main()
