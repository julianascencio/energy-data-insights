"""Stage a complete local GPPD hydro partition without changing the catalogue.

Usage: python scripts/stage_hydro_gppd.py INPUT.csv NEW_OUTPUT --retrieved-at UTC_TIMESTAMP
Review the ledger and source checksum before copying shards into catalogues/hydro.
"""

import argparse
import hashlib
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.gppd import parse_gppd
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--retrieved-at", required=True)
    args = parser.parse_args()
    data = args.input.read_bytes()
    rows, ledger = parse_gppd(
        data.decode("utf-8-sig"), source_id="wri-gppd-1.3.0", now=args.retrieved_at
    )
    args.output.mkdir(parents=True, exist_ok=False)
    for name, items in (("projects", rows), ("decisions", ledger)):
        (args.output / f"{name}.jsonl").write_text("".join(canonical_json(x) + "\n" for x in items))
    (args.output / "input.json").write_text(
        json.dumps(
            {
                "sha256": hashlib.sha256(data).hexdigest(),
                "rows": len(rows),
                "reviewed": len(ledger),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Staged {len(rows)} hydro rows; reviewed {len(ledger)} candidates")


if __name__ == "__main__":
    main()
