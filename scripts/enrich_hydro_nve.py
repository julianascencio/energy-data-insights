"""Replay the explicitly reviewed NVE identity partition into canonical JSONL."""

import argparse
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.reconcile import enrich_reviewed
from energy_data_retrieval.pv_catalogue.catalogue import canonical_json


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("catalogues/hydro"))
    args = parser.parse_args()
    research = args.root / "research"
    review = json.loads((research / "nve-crosswalk-20261105.json").read_text())
    crosswalk = {r["record_id"]: r for r in review["matches"]}
    candidates = {
        json.loads(r["external_ids_json"])["nve"]: r
        for p in sorted((research / "nve-20261105").glob("candidates-*.jsonl"))
        for line in p.read_text().splitlines()
        if (r := json.loads(line))
    }
    count = 0
    for path in sorted((args.root / "records").rglob("*.jsonl")):
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        output = []
        for row in rows:
            if row["record_id"] in crosswalk:
                match = crosswalk[row["record_id"]]
                row = enrich_reviewed(
                    row, candidates[match["nve_id"]], match, now=review["reviewed_at"]
                )
                count += 1
            output.append(row)
        text = "".join(canonical_json(row) + "\n" for row in output)
        if path.read_text() != text:
            path.write_text(text)
    if count != len(crosswalk):
        raise ValueError("Crosswalk targets missing from catalogue")
    print(f"Reviewed {count} existing identities; no new plant IDs")


if __name__ == "__main__":
    main()
