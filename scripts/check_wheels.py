"""Install built wheels outside the workspace and exercise their public entry points."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

from packaging.utils import parse_wheel_filename

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = ("data-retrieval", "methods", "analysis")

# Runs under the fresh interpreter, with no access to the editable workspace.
CHECK_INSTALLATION = """
import importlib
import importlib.metadata
import importlib.resources
import json
import pathlib
import subprocess
import sys

for name, expected_version in json.loads(sys.argv[1]).items():
    module = importlib.import_module(name.replace('-', '_'))
    assert pathlib.Path(module.__file__).is_relative_to(sys.prefix), module.__file__
    assert module.__version__ == expected_version, module.__version__
    distribution = importlib.metadata.distribution(name)
    assert distribution.version == expected_version, distribution.version
    resources = importlib.resources.files(module)
    assert resources.joinpath('py.typed').is_file(), name
    if name == 'energy-methods':
        json.loads(resources.joinpath('references.json').read_text())
    for entry in distribution.entry_points:
        if entry.group == 'console_scripts':
            result = subprocess.run(
                [str(pathlib.Path(sys.executable).parent / entry.name), '--help'],
                capture_output=True, text=True)
            if result.returncode:
                print(result.stdout)
                print(result.stderr, file=sys.stderr)
                result.check_returncode()
            print(f'{entry.name} --help: passed')
    print(f'{name} {expected_version}: installed wheel passed')
"""


def expected_versions(package: str | None = None) -> dict[str, str]:
    projects = []
    for directory in DIRECTORIES:
        with (ROOT / directory / "pyproject.toml").open("rb") as source:
            projects.append(tomllib.load(source)["project"])
    expected = {p["name"]: p["version"] for p in projects if package in (None, p["name"])}
    if not expected:
        raise ValueError(f"Unknown package: {package}")
    return expected


def validate_wheel_set(wheels: list[Path], expected: dict[str, str]) -> None:
    """Reject absent, duplicate, unrelated or incorrectly versioned wheels."""
    found: dict[str, str] = {}
    for wheel in wheels:
        name, version, _, _ = parse_wheel_filename(wheel.name)
        if name in found:
            raise ValueError(f"Duplicate wheel for {name}")
        found[name] = str(version)
    if found != expected:
        raise ValueError(f"Wheel names/versions {found} do not match {expected}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, default=ROOT / "dist")
    parser.add_argument(
        "--package", help="Check just this project's wheel; resolve siblings on PyPI"
    )
    args = parser.parse_args()
    expected = expected_versions(args.package)
    wheels = sorted(args.dist.resolve().glob("*.whl"))
    validate_wheel_set(wheels, expected)
    with tempfile.TemporaryDirectory(prefix="energy-wheel-check-") as temporary:
        environment = Path(temporary) / "venv"
        subprocess.run(["uv", "venv", "--python", sys.executable, str(environment)], check=True)
        python = environment / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
        subprocess.run(
            [
                "uv",
                "--no-config",
                "pip",
                "install",
                "--python",
                str(python),
                "--default-index",
                "https://pypi.org/simple",
                *map(str, wheels),
            ],
            check=True,
            cwd=temporary,
        )
        subprocess.run(
            [str(python), "-I", "-c", CHECK_INSTALLATION, json.dumps(expected)],
            check=True,
            cwd=temporary,
        )


if __name__ == "__main__":
    main()
