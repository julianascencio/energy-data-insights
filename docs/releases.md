# Public PyPI releases

Each subproject publishes a universal Python wheel (`py3-none-any.whl`) and a
source distribution to public PyPI. Python 3.12 or newer is required. Dependencies
such as NumPy and LightGBM supply their own platform-specific wheels.

| Directory | PyPI project / pip install name | Release tag | GitHub environment |
| --- | --- | --- | --- |
| `data-retrieval` | `energy-data-retrieval` | `data-retrieval-v0.1.0` | `pypi-energy-data-retrieval` |
| `methods` | `energy-methods` | `methods-v0.1.0` | `pypi-energy-methods` |
| `analysis` | `energy-analysis` | `analysis-v0.1.0` | `pypi-energy-analysis` |

Versions are independent. A tag releases only its named package. The workspace
root is not a distribution, and unscoped tags such as `v0.1.0` do not publish.

The optional Orbital PV imagery integration is installed separately from its pinned
Git source; its workspace dependency group is not part of published wheel metadata.
See the [satellite installation guide](satellite-imagery.md). This keeps the
release artifacts free of direct Git URL dependencies.

## One-time API token setup

Publishing uses the same API-token method as Orbital PV, through
[PyPA's publishing action](https://github.com/pypa/gh-action-pypi-publish) and
[PyPI's upload API](https://docs.pypi.org/api/upload/).

1. Sign in to the PyPI account that will own all three projects. Create an API
   token in [PyPI account settings](https://pypi.org/manage/account/token/).
   For the first release, the token must allow creation of these projects;
   a token scoped only to `orbital-pv` cannot publish them. Once projects exist,
   appropriately scoped tokens can be used for individual package releases.
2. In this repository's [Actions secrets](https://github.com/julianascencio/energy-data-insights/settings/secrets/actions),
   add a **repository secret** named `PYPI_API_TOKEN` with the token as its value.
   A secret saved only in the Orbital PV repository is not shared automatically.
   Never put the token in source files, workflow inputs, logs or release notes.
3. Keep the package environments in the table above. If an environment defines
   its own `PYPI_API_TOKEN`, that token overrides the repository secret and must
   permit that environment's package. Any environment approval or deployment
   rules still apply; allow the relevant tags and `main` for manual/batch runs.

No Trusted Publisher registration is required for this configuration. Publishing
jobs have no OIDC permission and explicitly disable attestations, which require
Trusted Publishing. The token is used only for the credential-presence check and
upload; builds and package tests run in separate jobs without it.

## Release all three packages

Run **Actions → Release all packages → Run workflow** on `main`. The workflow
reads each package's committed version, validates it, and releases retrieval,
then methods, then analysis. Each package passes the same quality, metadata and
isolated-install checks used by a tag release. Analysis is only built against
public sibling dependencies after their uploads succeed.

The initial release is also triggered when `.pypi-initial-release` changes on
`main`, matching Orbital PV's bootstrap mechanism. Ordinary code or database
updates do not publish packages. The marker is a trigger, not a version source;
manual/batch releases do not create Git tags or GitHub release objects.

If the token is missing, the batch stops before building or uploading anything
and identifies the missing secret. Add it and rerun that failed workflow. For a
partially successful batch, **rerun failed jobs**, not all jobs: completed PyPI
versions must not be uploaded again. Use the single-package workflow below when
only some package versions have changed.

## Release a package

1. Update the chosen package's version and lockfile, then merge the change into
   `main` after CI passes. For example, for the next methods release:

   ```bash
   uv version --package energy-methods 0.1.1 --no-sync
   uv sync --locked --all-packages --extra cds
   ```

   The version in that package's `pyproject.toml` is the source of truth;
   `__version__` reads installed distribution metadata. The tag must match it
   exactly. Supported versions are `X.Y.Z` and prereleases such as `0.2.0rc1`
   (`aN` and `bN` are also accepted). Development, local and post-release tags are
   rejected. Update analysis dependency bounds when it starts requiring a newer
   retrieval or methods API; local workspace resolution alone does not check
   compatibility with older public releases.

2. Tag the merged commit and push that tag:

   ```bash
   git switch main
   git pull --ff-only
   git tag -a methods-v0.1.1 -m "Release energy-methods 0.1.1"
   git push origin methods-v0.1.1
   ```

   The commit must be part of `main` history. GitHub's **Create a new release** UI
   can also create the corresponding tag on that commit. A release object using
   a tag that already exists does not trigger another upload. Tags created by a
   workflow's default `GITHUB_TOKEN` do not trigger this push workflow; create
   them as a maintainer.

   Alternatively, run **Actions → Publish packages to PyPI → Run workflow** on
   `main` and supply the exact scoped release tag, for example `methods-v0.1.1`.
   This validates the same package/version without creating a Git tag.

3. Follow **Actions → Publish packages to PyPI**. It validates the tag, runs the
   full quality/test workflow on Python 3.12 and 3.13, builds the selected package
   from its source distribution with uv's workspace sources disabled, checks
   metadata with Twine, and installs the wheel into an isolated environment.
   The installation check imports the package, checks its version and packaged
   resources, and runs every console script's `--help`.

4. A separate publishing job downloads the checked artifacts and uploads them
   using `PYPI_API_TOKEN`. It does not check out or build repository code. The
   environment links to the published PyPI version.

For the **first release**, publish `data-retrieval-v0.1.0` and `methods-v0.1.0`
first, and wait for both to succeed. Then push `analysis-v0.1.0`. Analysis's
release check installs only its own local wheel, resolving its sibling packages
and all other dependencies from public PyPI. It fails before upload if required
sibling versions have not been published. The same ordering applies when
analysis raises a dependency's minimum version.

PyPI versions are immutable. Do not move a published tag or overwrite a version.
Fix a code or packaging defect with a new version and tag. For an authentication
or transient failure before upload, fix the token configuration and rerun
the failed job. If an upload was partially completed, inspect PyPI's files before
retrying; this workflow deliberately does not skip existing files.

## Install a published release

These commands become available after the corresponding first release succeeds:

```bash
python -m pip install energy-data-retrieval
python -m pip install energy-methods
python -m pip install energy-analysis
```

Installing `energy-analysis` also installs compatible retrieval and methods
packages. Optional sources remain available through extras:

```bash
python -m pip install 'energy-data-retrieval[cds]'
python -m pip install 'energy-data-retrieval[era5-native]'
energy-retrieve --help
energy-kgpv --help
energy-ccya --help
```

Pin a version for reproducible use, for example `energy-methods==0.1.0`. Pip
normally excludes prereleases unless you specify their version or use `--pre`.
CDS credentials and accepted dataset terms are still required for live downloads.

## Check packaging locally

From a clean checkout:

```bash
uv sync --locked --all-packages --extra cds
uv run --no-sync pytest tests/test_releases.py
uv build --no-sources --all-packages --out-dir dist
uv run --no-sync twine check --strict dist/*
uv run --no-sync python scripts/check_wheels.py
```

Use an empty `dist/` directory when changing versions; the checker rejects
duplicate, stale or unrelated wheels. CI installs all three local wheels together
so PRs can be checked before their first public release. Tag builds additionally
check the selected wheel against public dependencies. Neither the local checks
nor pull-request CI uploads anything.

Implementation references: [uv package builds](https://docs.astral.sh/uv/guides/package/)
and [PyPA's GitHub Actions publisher](https://github.com/pypa/gh-action-pypi-publish).
