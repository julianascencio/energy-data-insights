"""Reject accidental secrets and large generated data before a public commit.

This is a deliberately narrow local check, not a replacement for provider-side
secret scanning. It reads Git's candidate file inventory, never local ignored
credentials, and prints filenames plus categories rather than matching secrets.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_FILE_BYTES = 2_000_000
GENERATED_SUFFIXES = {
    ".gz",
    ".joblib",
    ".parquet",
    ".pickle",
    ".pkl",
    ".xlsx",
    ".zip",
}
SECRET_PATTERNS = (
    re.compile(rb"(?:ghp_|github_pat_)[A-Za-z0-9_]{30,}"),
    re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(
        rb"(?i)[\"']?(?:user_key|api_key|access_token|client_secret)[\"']?"
        rb"\s*[:=]\s*[\"'][a-zA-Z0-9+/]{24,64}[\"']"
    ),
)


def candidate_files() -> list[Path]:
    """Return tracked and nonignored new files without following symlinks."""
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / name.decode() for name in result.stdout.split(b"\0") if name]


def main() -> int:
    problems: list[str] = []
    files = candidate_files()
    for path in files:
        name = path.relative_to(ROOT).as_posix()
        if not path.exists():
            continue  # A tracked deletion is not new content.
        if path.is_symlink():
            problems.append(f"{name}: symlink requires explicit review")
            continue
        if path.name.startswith(".env") and path.name != ".env.example":
            problems.append(f"{name}: local credentials file")
        if path.suffix.lower() in GENERATED_SUFFIXES:
            problems.append(f"{name}: generated/binary data belongs outside Git")
        if path.stat().st_size > MAX_FILE_BYTES:
            problems.append(f"{name}: exceeds {MAX_FILE_BYTES:,}-byte source limit")
            continue
        if any(pattern.search(path.read_bytes()) for pattern in SECRET_PATTERNS):
            problems.append(f"{name}: possible embedded credential")
    if problems:
        print("Repository check failed:")
        print("\n".join(problems))
        return 1
    print(f"Repository check passed: {len(files)} candidate files; no flagged secrets or data.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
