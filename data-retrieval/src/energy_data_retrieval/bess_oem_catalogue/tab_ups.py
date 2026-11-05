"""Stage the reviewed TAB UPS table from local layout-preserving PDF text."""

import re

MODELS = (
    *(f"12V {i} UPS {i * 100}" for i in range(1, 7)),
    *(f"6V {i} UPS {i * 100}" for i in range(7, 13)),
    "2V 24 UPS 2400",
    "2V 30 UPS 3000",
    "2V 36 UPS 3600",
)


def parse_models(text: str) -> list[dict]:
    """Preserve per-cell timed watts; do not infer unit energy or continuous power."""
    page = next((p for p in text.split("\f") if "12V 1 UPS 100" in p), "")
    normalized = " ".join(page.split())
    for header in (
        "Uf (V/cell) 1,80 1,75 1,70 1,65 1,63 1,60",
        "Discharging time (min) 60 30 15 10 5",
        "Type C10 (Ah) W/cell W/cell W/cell W/cell W/cell",
        "Dry Wet",
        "mΩ (kA) mm mm mm kg kg",
    ):
        if header not in normalized:
            raise ValueError("Changed UPS table units or rate headers")
    rows = []
    for line in page.splitlines():
        match = re.match(r"^(\d+V \d+ UPS \d+)\s+(.+)$", line.strip())
        if not match:
            continue
        tokens = match[2].split()
        if len(tokens) != 13 or any(not re.fullmatch(r"\d+(?:,\d+)?", t) for t in tokens):
            raise ValueError("Partial or invalid UPS row")
        values = [float(t.replace(",", ".")) for t in tokens]
        if min(values) <= 0 or values[1:6] != sorted(values[1:6]) or values[11] >= values[12]:
            raise ValueError("Invalid power or mass ordering")
        rows.append({"model": match[1], "values": values})
    if tuple(r["model"] for r in rows) != MODELS:
        raise ValueError("Changed, missing or duplicate UPS identities")
    return rows
