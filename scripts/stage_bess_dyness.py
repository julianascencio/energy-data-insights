#!/usr/bin/env python3
"""Stage the reviewed Dyness STACK100 manual offline; never import automatically."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.dyness import parse_stack100_manual


def main() -> None:
    """Read local text/PDF, attach byte fingerprints, and emit review candidates."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", type=Path, required=True, help="pdftotext -layout output")
    parser.add_argument("--document", type=Path, required=True, help="Original publisher PDF")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pdf = args.document.read_bytes()
    if not pdf.startswith(b"%PDF-"):
        parser.error("--document must contain the original PDF bytes")
    text_bytes = args.text.read_bytes()
    candidates = parse_stack100_manual(text_bytes.decode("utf-8"))
    result = {
        "source_id": "dyness_stack100_manual_20250307",
        "document_sha256": hashlib.sha256(pdf).hexdigest(),
        "extracted_text_sha256": hashlib.sha256(text_bytes).hexdigest(),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "warning": (
            "Candidates only. Verify identity, source rights, revision and other fields "
            "before upsert."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Staged {len(candidates)} candidates; no catalogue records modified.")


if __name__ == "__main__":
    main()
