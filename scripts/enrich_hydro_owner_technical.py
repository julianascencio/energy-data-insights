"""Replay the reviewed KenGen station technical assertions."""

import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.owner_technical import enrich_reviewed
from energy_data_retrieval.hydro_catalogue.replay import replay_reviewed

root = Path("catalogues/hydro")
batch = json.loads((root / "research/kengen-technical-20261106.json").read_text())
print(
    replay_reviewed(
        root,
        batch["accepted"],
        lambda row, entry: enrich_reviewed(row, entry, now=batch["reviewed_at"]),
    )
)
