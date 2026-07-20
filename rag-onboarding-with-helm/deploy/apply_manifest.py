"""Render a TrueFoundry manifest with values from .env, then run `tfy apply`.

`tfy apply` does not expand ${VAR} or load .env. This helper does both.

Usage:
    python deploy/apply_manifest.py deploy/qdrant.truefoundry.yaml
    python deploy/apply_manifest.py deploy/rag-app.truefoundry.yaml
    python deploy/apply_manifest.py deploy/qdrant.truefoundry.yaml --dry-run
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from dotenv import load_dotenv

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PLACEHOLDER = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def _load_dotenv() -> None:
    for env_path in (_REPO_ROOT / ".env", Path(".env")):
        if env_path.is_file():
            load_dotenv(env_path, override=False)
            return
    load_dotenv(override=False)


def _render(content: str) -> str:
    missing: list[str] = []

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        value = os.getenv(key)
        if value is None:
            missing.append(key)
            return match.group(0)
        return value

    rendered = _PLACEHOLDER.sub(repl, content)
    if missing:
        uniq = ", ".join(sorted(set(missing)))
        raise ValueError(f"Missing environment variables for manifest: {uniq}")
    return rendered


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, help="Path to a *.truefoundry.yaml file")
    parser.add_argument("--dry-run", action="store_true", help="Pass --dry-run to tfy apply")
    args = parser.parse_args()

    _load_dotenv()
    manifest_path = args.manifest if args.manifest.is_absolute() else _REPO_ROOT / args.manifest
    if not manifest_path.is_file():
        print(f"Manifest not found: {manifest_path}", file=sys.stderr)
        return 1

    try:
        rendered = _render(manifest_path.read_text())
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    with tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False) as tmp:
        tmp.write(rendered)
        tmp_path = tmp.name

    cmd = ["tfy", "apply", "-f", tmp_path]
    if args.dry_run:
        cmd.append("--dry-run")

    print(f"Applying rendered manifest from {manifest_path} ...")
    try:
        completed = subprocess.run(cmd, check=False)
        return completed.returncode
    finally:
        Path(tmp_path).unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
