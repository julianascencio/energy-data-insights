"""Resolve a scoped release tag without executing project code or installing dependencies."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = {
    "data-retrieval": "energy-data-retrieval",
    "methods": "energy-methods",
    "analysis": "energy-analysis",
}
VERSION = r"(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:(?:a|b|rc)(?:0|[1-9]\d*))?"


def release_plan(tag: str, root: Path = ROOT) -> dict[str, str]:
    """Require one known package and an exact, committed release version."""
    match = re.fullmatch(rf"(data-retrieval|methods|analysis)-v({VERSION})", tag)
    if match is None:
        raise ValueError("Use <data-retrieval|methods|analysis>-vX.Y.Z (optionally aN, bN or rcN)")
    directory, version = match.groups()
    with (root / directory / "pyproject.toml").open("rb") as source:
        project = tomllib.load(source)["project"]
    package = PACKAGES[directory]
    if project["name"] != package:
        raise ValueError(f"Expected project name {package!r} in {directory}/pyproject.toml")
    if project["version"] != version:
        raise ValueError(
            f"Tag version {version} differs from {package} version {project['version']}"
        )
    return {
        "package": package,
        "directory": directory,
        "version": version,
        "environment": f"pypi-{package}",
    }


def all_release_tags(root: Path = ROOT) -> dict[str, str]:
    """Validate all package names and versions before an ordered workspace release."""
    tags = {}
    for directory in PACKAGES:
        with (root / directory / "pyproject.toml").open("rb") as source:
            version = tomllib.load(source)["project"]["version"]
        tag = f"{directory}-v{version}"
        release_plan(tag, root)
        tags[f"{directory.replace('-', '_')}_tag"] = tag
    return tags


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("tag", nargs="?")
    selection.add_argument("--all", action="store_true", help="Plan all committed package versions")
    parser.add_argument("--output", type=Path, help="Append validated values to GITHUB_OUTPUT")
    args = parser.parse_args()
    try:
        plan = all_release_tags() if args.all else release_plan(args.tag)
    except ValueError as error:
        parser.error(str(error))
    if args.output:
        with args.output.open("a", encoding="utf-8") as output:
            output.writelines(f"{key}={value}\n" for key, value in plan.items())
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
