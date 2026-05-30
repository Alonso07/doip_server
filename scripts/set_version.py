#!/usr/bin/env python3
"""Compute and write the CalVer + git-hash version for doip-server.

Display version (in __init__.py):   YYYY.MM.DD.<short-hash>
                                     e.g. 2026.05.30.49f2dd5

PyPI version (in pyproject.toml):   YYYY.M.D.post<commit-count>
                                     e.g. 2026.5.30.post142

PEP 440 does not allow hex characters in release segments, so the hash
lives in the display version only; the PyPI version uses the total commit
count as a monotonically-increasing post-release suffix.

Usage:
    python scripts/set_version.py            # write both files
    python scripts/set_version.py --dry-run  # print versions, write nothing
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INIT_FILE = REPO_ROOT / "src" / "doip_server" / "__init__.py"
PYPROJECT = REPO_ROOT / "pyproject.toml"


def _run(cmd: list[str]) -> str:
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    if result.returncode != 0:
        raise RuntimeError(f"Command {cmd} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def compute_versions() -> tuple[str, str]:
    """Return (display_version, pypi_version)."""
    today = datetime.now()
    date_display = today.strftime("%Y.%m.%d")
    date_pypi = f"{today.year}.{today.month}.{today.day}"

    short_hash = _run(["git", "rev-parse", "--short", "HEAD"])
    commit_count = _run(["git", "rev-list", "--count", "HEAD"])

    display_version = f"{date_display}.{short_hash}"
    pypi_version = f"{date_pypi}.post{commit_count}"

    return display_version, pypi_version


def update_init(display_version: str) -> None:
    content = INIT_FILE.read_text()
    updated = re.sub(
        r'^__version__\s*=\s*["\'][^"\']*["\']',
        f'__version__ = "{display_version}"',
        content,
        flags=re.MULTILINE,
    )
    if updated == content:
        raise RuntimeError(f"Could not find __version__ assignment in {INIT_FILE}")
    INIT_FILE.write_text(updated)


def update_pyproject(pypi_version: str) -> None:
    content = PYPROJECT.read_text()
    updated = re.sub(
        r'^version\s*=\s*["\'][^"\']*["\']',
        f'version = "{pypi_version}"',
        content,
        flags=re.MULTILINE,
    )
    if updated == content:
        raise RuntimeError(f"Could not find version assignment in {PYPROJECT}")
    PYPROJECT.write_text(updated)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print computed versions without writing any files",
    )
    args = parser.parse_args()

    display_version, pypi_version = compute_versions()

    print(f"Display version : {display_version}")
    print(f"PyPI version    : {pypi_version}")

    if args.dry_run:
        print("(dry-run: no files written)")
        return

    update_init(display_version)
    print(f"Updated {INIT_FILE.relative_to(REPO_ROOT)}")

    update_pyproject(pypi_version)
    print(f"Updated {PYPROJECT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
