"""Replay the explicitly reviewed KenGen new-identity batch."""

import json
from pathlib import Path

from energy_data_retrieval.hydro_catalogue.kengen_new import accept_new

root = Path("catalogues/hydro")
batch = json.loads((root / "research/kengen-new-20261106.json").read_text())
print(accept_new(root, batch, root / "records/projects/kengen-new-20261106.jsonl"))
