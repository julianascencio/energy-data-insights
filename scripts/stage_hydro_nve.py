"""Stage NVE API bytes offline; never write canonical catalogue records."""

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.nve import parse_nve
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--retrieved-at", required=True)
    args = parser.parse_args()
    data = args.input.read_bytes()
    candidates, decisions = parse_nve(
        data.decode("utf-8-sig"), source_id="nve-hydro-20261105", now=args.retrieved_at
    )
    args.output.mkdir(parents=True, exist_ok=False)
    for index in range(0, len(candidates), 100):
        shard = args.output / f"candidates-{index // 100:03d}.jsonl"
        shard.write_text(
            "".join(canonical_json(row) + "\n" for row in candidates[index : index + 100]),
            encoding="utf-8",
        )
    (args.output / "decisions.jsonl").write_text(
        "".join(canonical_json(row) + "\n" for row in decisions), encoding="utf-8"
    )
    manifest = {
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "retrieved_at": args.retrieved_at,
        "source_rows": len(decisions),
        "accepted": 0,
        "decisions": dict(Counter(row["decision"] for row in decisions)),
        "next_action": "Review registry crosswalk against existing NOR records before acceptance",
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
