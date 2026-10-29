"""Release gates must reject tags and wheels that could publish the wrong project."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


release = load_script("release_plan")
wheels = load_script("check_wheels")


@pytest.mark.parametrize("directory", ["data-retrieval", "methods", "analysis"])
@pytest.mark.parametrize("version", ["0.1.0", "1.2.3rc1"])
def test_release_selects_only_tagged_package(tmp_path, directory, version):
    package = release.PACKAGES[directory]
    (tmp_path / directory).mkdir()
    (tmp_path / directory / "pyproject.toml").write_text(
        f'[project]\nname = "{package}"\nversion = "{version}"\n'
    )
    assert release.release_plan(f"{directory}-v{version}", tmp_path) == {
        "package": package,
        "directory": directory,
        "version": version,
        "environment": f"pypi-{package}",
    }


@pytest.mark.parametrize(
    "tag",
    [
        "v0.1.0",
        "other-v0.1.0",
        "methods-v01.1.0",
        "methods-v0.1",
        "methods-v0.1.0+local",
        "methods-v0.1.0.dev1",
        "methods-v0.1.0\npackage=other",
        "methods-v0.1.0/extra",
    ],
)
def test_invalid_tag_is_rejected(tag):
    with pytest.raises(ValueError, match="Use"):
        release.release_plan(tag)


@pytest.mark.parametrize(
    ("name", "version", "message"),
    [("energy-methods", "0.2.0", "differs"), ("wrong-project", "0.1.0", "Expected project name")],
)
def test_metadata_must_match_tag(tmp_path, name, version, message):
    (tmp_path / "methods").mkdir()
    (tmp_path / "methods" / "pyproject.toml").write_text(
        f'[project]\nname = "{name}"\nversion = "{version}"\n'
    )
    with pytest.raises(ValueError, match=message):
        release.release_plan("methods-v0.1.0", tmp_path)


@pytest.mark.parametrize(
    "filenames",
    [
        [],
        ["energy_methods-0.2.0-py3-none-any.whl"],
        ["energy_analysis-0.1.0-py3-none-any.whl"],
        ["energy_methods-0.1.0-py3-none-any.whl", "energy_methods-0.1.0-1-py3-none-any.whl"],
    ],
)
def test_wrong_wheel_set_is_rejected(filenames):
    with pytest.raises(ValueError):
        wheels.validate_wheel_set(list(map(Path, filenames)), {"energy-methods": "0.1.0"})


def test_wheel_name_normalization():
    wheels.validate_wheel_set(
        [Path("energy_methods-0.1.0-py3-none-any.whl")], {"energy-methods": "0.1.0"}
    )
