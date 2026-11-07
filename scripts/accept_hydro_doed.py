"""Replay a reviewed Nepal DoED partition, optionally verifying original source bytes."""

import argparse
import hashlib
import json
from functools import partial
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.doed import (
    new_record,
    parse_inventory,
    parse_updated_date,
    validate_reviewed_batch,
)
from energy_data_retrieval.hydro_catalogue.era import accept_new

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--html", type=Path)
parser.add_argument(
    "--batch",
    type=Path,
    default=Path("catalogues/hydro/research/doed-20261106-0001-0100.json"),
)
args = parser.parse_args()
root = Path("catalogues/hydro")
batch = json.loads(args.batch.read_text())
validate_reviewed_batch(batch)
if args.html:
    raw = args.html.read_bytes()
    if batch.get("source_sha256") and hashlib.sha256(raw).hexdigest() != batch["source_sha256"]:
        raise ValueError("Source checksum differs; review the new capture")
    html = raw.decode("utf-8")
    if parse_inventory(html) != batch["parsed_inventory"]:
        raise ValueError("Source drift requires review")
    if batch.get("source_as_of") and parse_updated_date(html) != batch["source_as_of"]:
        raise ValueError("Source update date differs")
print(
    accept_new(
        root,
        batch,
        root / "records/projects" / (args.batch.stem + ".jsonl"),
        record_factory=partial(
            new_record, source_id=batch["source_id"], source_as_of=batch.get("source_as_of")
        ),
    )
)
