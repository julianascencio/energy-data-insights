"""Every example belongs to one reachable topic under one main gallery section."""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "examples"


def toctree_entries(path: Path) -> list[str]:
    """Read authored hidden toctrees without requiring documentation dependencies."""
    entries = []
    in_tree = False
    for line in path.read_text().splitlines():
        if line.startswith(".. toctree::"):
            in_tree = True
        elif line and not line.startswith(" "):
            in_tree = False
        elif in_tree and line.strip() and not line.strip().startswith(":"):
            entries.append(line.strip())
    return entries


def test_every_example_has_exactly_two_category_levels() -> None:
    sections = toctree_entries(EXAMPLES / "index.rst")
    assert sections == ["methods/index", "connectors/index", "analysis/index", "database/index"]
    assigned: list[Path] = []
    reachable_topics: set[Path] = set()
    for section in sections:
        index = EXAMPLES / f"{section}.rst"
        topics = toctree_entries(index)
        assert topics, f"Empty main section: {section}"
        assert len(topics) == len(set(topics))
        cards = re.findall(r"^\s+:link: (.+)$", index.read_text(), re.MULTILINE)
        assert cards == topics, f"Cards and sidebar disagree in {section}"
        for topic in topics:
            assert re.fullmatch(r"topic_[a-z_]+", topic), "No third category level"
            page = index.parent / f"{topic}.rst"
            reachable_topics.add(page)
            examples = toctree_entries(page)
            assert examples, f"Empty topic: {topic}"
            assert all(re.fullmatch(r"plot_[a-z_0-9]+", entry) for entry in examples)
            scripts = [page.parent / f"{entry}.py" for entry in examples]
            thumbnails = re.findall(r"^\s+\.\./examples/(.+\.py)$", page.read_text(), re.MULTILINE)
            assert [EXAMPLES / name for name in thumbnails] == scripts
            assigned.extend(scripts)
    assert reachable_topics == set(EXAMPLES.glob("*/topic_*.rst")), "Unreachable topic page"
    counts = Counter(assigned)
    assert all(count == 1 for count in counts.values()), "Example assigned more than once"
    assert set(assigned) == set(EXAMPLES.rglob("plot_*.py")), "Missing or stale example assignment"


def test_landing_cards_match_the_main_navigation() -> None:
    landing = EXAMPLES / "index.rst"
    assert re.findall(r"^\s+:link: (.+)$", landing.read_text(), re.MULTILINE) == toctree_entries(
        landing
    )
    # Category pages should stay concise; executable content belongs to examples.
    assert ".. minigallery::" not in landing.read_text()
    for section in EXAMPLES.glob("*/index.rst"):
        assert ".. minigallery::" not in section.read_text()
