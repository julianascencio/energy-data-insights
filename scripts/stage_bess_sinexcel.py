"""Stage an exact reviewed Sinexcel PDF text table for manual identity review."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from energy_data_retrieval.bess_oem_catalogue.sinexcel import parse_sinexcel_pcs_text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("text", type=Path)
    parser.add_argument("--models", nargs="+", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = parse_sinexcel_pcs_text(args.text.read_bytes(), expected_models=args.models)
    args.output.write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows)
    )


if __name__ == "__main__":
    main()
