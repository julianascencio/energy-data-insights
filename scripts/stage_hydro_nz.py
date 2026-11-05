"""Stage NZ dispatch observations for review; never modify canonical records."""

import argparse
import hashlib
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.nz import parse_inventory


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data = args.csv.read_bytes()
    rows = parse_inventory(data)
    payload = {
        "sha256": hashlib.sha256(data).hexdigest(),
        "hydro_rows": len(rows),
        "distinct_source_names": len({x["raw"]["PlantName"] for x in rows}),
        "decision": "held_identity_interval_and_connection_scope_review",
        "observations": rows,
    }
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
