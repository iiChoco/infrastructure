#!/usr/bin/env python3
"""Render portable templates into user-specific plists; does not load services."""
from __future__ import annotations

import argparse
from pathlib import Path
import plistlib

ROOT = Path(__file__).resolve().parents[1]


def render(template: Path, ciel_root: Path, home: Path) -> bytes:
    with template.open("rb") as fh:
        document = plistlib.load(fh)

    def replace(value):
        if isinstance(value, str):
            return value.replace("__CIEL_ROOT__", str(ciel_root)).replace("__USER_HOME__", str(home))
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return value

    return plistlib.dumps(replace(document), sort_keys=False)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ciel-root", type=Path, default=ROOT.parent / "ciel")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--output", type=Path, default=ROOT / "rendered")
    args = parser.parse_args()
    ciel_root = args.ciel_root.expanduser().resolve(strict=True)
    if not (ciel_root / "src/ciel/__main__.py").is_file():
        parser.error("--ciel-root must identify the Ciel source checkout")
    args.output.mkdir(parents=True, exist_ok=True)
    for template in sorted((ROOT / "services/launchd").glob("*.plist")):
        output = args.output / template.name
        output.write_bytes(render(template, ciel_root, args.home.expanduser().resolve()))
        print(output)


if __name__ == "__main__":
    main()
