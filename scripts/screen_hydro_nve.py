"""Stage an explicit WRI-ID partition for NVE identity review; never accept merges."""

import argparse
import hashlib
import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue import load_records


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gis", type=Path, required=True)
    parser.add_argument("--api", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reviewed-at", required=True)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument(
        "--after-wri-id", help="Stable exclusive cursor; do not combine with offset"
    )
    args = parser.parse_args()
    if args.offset < 0 or args.limit < 1:
        parser.error("Require nonnegative offset and positive limit")
    if args.after_wri_id and args.offset:
        parser.error("Use a stable cursor or an offset, not both")
    root = Path("catalogues/hydro")
    remaining = sorted(
        [
            r
            for r in load_records(root)
            if r["country_code"] == "NOR" and "nve" not in json.loads(r["external_ids_json"])
        ],
        key=lambda r: json.loads(r["external_ids_json"])["wri_gppd"],
    )
    if args.after_wri_id:
        remaining = [
            r
            for r in remaining
            if json.loads(r["external_ids_json"])["wri_gppd"] > args.after_wri_id
        ]
    api = json.loads(args.api.read_bytes())
    gis = json.loads(args.gis.read_bytes())
    if gis.get("exceededTransferLimit") or "features" not in gis:
        raise ValueError("Incomplete GIS response")
    decisions = []
    for row in remaining[args.offset : args.offset + args.limit]:
        matches = [r for r in api if r["Navn"] == row["name"]]
        features = [
            f for f in gis["features"] if f["attributes"]["vannkraftverknavn"] == row["name"]
        ]
        decisions.append(
            dict(
                record_id=row["record_id"],
                wri_id=json.loads(row["external_ids_json"])["wri_gppd"],
                name=row["name"],
                historical_capacity_mw=row["historical_capacity_mw"],
                wri_coordinates=[row.get("longitude"), row.get("latitude")],
                api_exact_name_candidates=matches,
                gis_exact_name_candidates=features,
                decision="held_identity_and_scope_review",
                reason=(
                    "Name equality is insufficient; aliases, location offsets and physical scope "
                    "require explicit corroboration. No automatic fuzzy or nearest-neighbour merge."
                ),
            )
        )
    result = dict(
        reviewed_at=args.reviewed_at,
        accepted=0,
        held=len(decisions),
        partition=dict(
            offset=args.offset,
            after_wri_id=args.after_wri_id,
            limit=args.limit,
            last_wri_id=decisions[-1]["wri_id"] if decisions else None,
            next_offset=args.offset + len(decisions),
        ),
        source_sha256={
            p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.api, args.gis)
        },
        decisions=decisions,
    )
    text = json.dumps(result, indent=2) + "\n"
    if args.output.exists() and args.output.read_text() != text:
        raise ValueError("Refusing to replace a different review ledger")
    args.output.write_text(text)
    print(f"Staged {len(decisions)} held identities; none accepted")


if __name__ == "__main__":
    main()
