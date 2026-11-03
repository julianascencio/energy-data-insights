"""Reconcile a local REPD CSV and pinned WRI crosswalk; never download or publish.

Usage: stage_wind_repd.py REPD.csv matches_GBR.csv NEW_OUTPUT --retrieved-at UTC
"""

import argparse
import hashlib
import json
from pathlib import Path

from energy_data_retrieval.pv_catalogue.catalogue import canonical_json, load_records
from energy_data_retrieval.wind_catalogue.repd import reconcile_repd


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("crosswalk", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--root", type=Path, default=Path("catalogues/wind"))
    parser.add_argument("--encoding", default="cp1252")
    parser.add_argument("--retrieved-at", required=True)
    parser.add_argument("--as-of", default="2026-08-03")
    args = parser.parse_args()
    original = args.input.read_bytes()
    crosswalk = args.crosswalk.read_bytes()
    rows, decisions = reconcile_repd(
        original.decode(args.encoding),
        crosswalk.decode("utf-8-sig"),
        load_records(args.root),
        source_id="desnz-repd-q2-2026",
        crosswalk_source_id="wri-gbr-crosswalk-2021",
        now=args.retrieved_at,
        as_of=args.as_of,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    for name, items in (("enrichments", rows), ("decisions", decisions)):
        (args.output / f"{name}.jsonl").write_text("".join(canonical_json(r) + "\n" for r in items))
    metadata = {
        "input_sha256": hashlib.sha256(original).hexdigest(),
        "crosswalk_sha256": hashlib.sha256(crosswalk).hexdigest(),
        "selected_wind_rows": len(decisions),
        "enrichments": len(rows),
        "encoding": args.encoding,
        "retrieved_at": args.retrieved_at,
    }
    (args.output / "input.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(metadata))


if __name__ == "__main__":
    main()
