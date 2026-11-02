#!/usr/bin/env python3
"""Stage Deye BOS-G-Pro EU brochure observations offline, without importing them."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.deye import parse_bos_g_pro


def main() -> None:
    """Attach original-byte fingerprints to review-only candidates."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", type=Path, required=True)
    parser.add_argument("--document", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    pdf, raw = args.document.read_bytes(), args.text.read_bytes()
    if not pdf.startswith(b"%PDF-"):
        parser.error("--document must contain original PDF bytes")
    candidates = parse_bos_g_pro(raw.decode("utf-8"))
    result = {
        "source_id": "deye_bosgpro_eu_20260414",
        "document_sha256": hashlib.sha256(pdf).hexdigest(),
        "text_sha256": hashlib.sha256(raw).hexdigest(),
        "candidates": candidates,
        "warning": "Review source rights, revision, identities and conflicts before upsert.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"Staged {len(candidates)} observations; no records imported.")


if __name__ == "__main__":
    main()
