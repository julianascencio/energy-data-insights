"""Stage the reviewed TOPzS PDF table; keep rate and fault-current units distinct."""

import re

MODELS = (
    "3 TOPzS 265",
    "4 TOPzS 353",
    "5 TOPzS 442",
    "4 TOPzS 500",
    "5 TOPzS 625",
    "6 TOPzS750",
    "7 TOPzS 875",
    "8 TOPzS 1000",
)


def parse_models(text: str) -> list[dict]:
    """Return exact printed identities and ten numeric observations, without energy inference."""
    page = next((p for p in text.split("\f") if "3 TOPzS 265" in p), "")
    normalized = " ".join(page.split())
    for header in (
        "Uf (V/cell) 1,80 1,80 1,85",
        "Capacity C10 C20 C100",
        "Ri Isc L W H Dry Wet",
        "Type Ah Ah Ah* mΩ A mm mm mm kg kg",
        "20 °C at C10 (1,80 V/cell) and 25 °C",
        "at C100 (1,85 V/cell)",
    ):
        if header not in normalized:
            raise ValueError("Changed TOPzS units, basis or headers")
    rows = []
    for line in page.splitlines():
        match = re.match(r"^(\d+ TOPzS\s*\d+)\s+(.+)$", line.strip())
        if not match:
            continue
        tokens = match[2].split()
        if len(tokens) != 10 or any(not re.fullmatch(r"\d+(?:,\d+)?", t) for t in tokens):
            raise ValueError("Partial or invalid TOPzS row")
        values = [float(t.replace(",", ".")) for t in tokens]
        if min(values) <= 0 or values[:3] != sorted(values[:3]) or values[8] >= values[9]:
            raise ValueError("Invalid TOPzS capacity or mass order")
        rows.append({"model": match[1], "values": values})
    if tuple(r["model"] for r in rows) != MODELS:
        raise ValueError("Changed, missing or duplicate TOPzS identities")
    return rows
