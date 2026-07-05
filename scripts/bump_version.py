"""Conventional Commits からバージョンを自動更新する."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def get_last_tag() -> str | None:
    result = subprocess.run(
        ["git", "describe", "--tags", "--abbrev=0"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    return result.stdout.strip() if result.returncode == 0 else None


def get_commits_since(tag: str | None) -> list[str]:
    if tag:
        cmd = ["git", "log", f"{tag}..HEAD", "--format=%s"]
    else:
        cmd = ["git", "log", "--format=%s"]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    return result.stdout.strip().splitlines() if result.stdout.strip() else []


def detect_bump_type(messages: list[str]) -> str:
    for msg in messages:
        if re.search(r"BREAKING CHANGE|^[a-z]+!", msg):
            return "major"
    for msg in messages:
        if msg.startswith("feat"):
            return "minor"
    for msg in messages:
        if (
            msg.startswith("fix")
            or msg.startswith("chore")
            or msg.startswith("refactor")
        ):
            return "patch"
    return "patch"


def bump_version(version: str, bump_type: str) -> str:
    major, minor, patch = map(int, version.split("."))
    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    else:
        return f"{major}.{minor}.{patch + 1}"


def update_pyproject(new_version: str) -> None:
    path = REPO_ROOT / "pyproject.toml"
    content = path.read_text(encoding="utf-8")
    content = re.sub(
        r'^version = ".*"', f'version = "{new_version}"', content, flags=re.MULTILINE
    )
    path.write_text(content, encoding="utf-8")


def update_init(new_version: str) -> None:
    path = REPO_ROOT / "src" / "sbipf_reporter" / "__init__.py"
    content = path.read_text(encoding="utf-8")
    content = re.sub(r'__version__ = ".*"', f'__version__ = "{new_version}"', content)
    path.write_text(content, encoding="utf-8")


def main() -> None:
    dry_run = "--dry-run" in sys.argv

    # --set VERSION: 指定されたバージョンを直接書き込む
    if "--set" in sys.argv:
        idx = sys.argv.index("--set")
        if idx + 1 >= len(sys.argv):
            print("Usage: python scripts/bump_version.py --set X.Y.Z", file=sys.stderr)
            sys.exit(1)
        new_version = sys.argv[idx + 1]
        print(f"new_version={new_version}")
        if not dry_run:
            update_pyproject(new_version)
            update_init(new_version)
            print(f"Updated to {new_version}")
        return

    # 従来の auto-bump: 前回タグからのコミットを解析
    last_tag = get_last_tag()
    commits = get_commits_since(last_tag)

    if not commits:
        print("No new commits since last tag.")
        return

    bump_type = detect_bump_type(commits)
    current = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'version = "(.*)"', current)
    if not m:
        print("Could not find version in pyproject.toml", file=sys.stderr)
        sys.exit(1)

    new_version = bump_version(m.group(1), bump_type)
    print(f"bump_type={bump_type}")
    print(f"new_version={new_version}")

    if not dry_run:
        update_pyproject(new_version)
        update_init(new_version)
        print(f"Updated to {new_version}")


if __name__ == "__main__":
    main()
