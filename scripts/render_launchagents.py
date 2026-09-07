#!/usr/bin/env python3
"""Render portable templates into user-specific plists; does not load services."""
from __future__ import annotations

import argparse
from pathlib import Path
import plistlib
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER_NAME = "Ciel.app"


def build_launcher(output: Path) -> Path:
    """Build the application bundle launchd starts, and return its executable.

    The bundle exists for one reason: macOS asks for the microphone on
    behalf of the *application responsible* for a process, and only an
    application whose Info.plist names why (NSMicrophoneUsageDescription)
    is asked at all. Python's bundle names nothing, so a spoke launchd
    starts as python is denied in silence; ``services/launcher/main.c``
    says the rest. Ad-hoc signed, so the grant is keyed to this exact
    build: rebuilding the launcher means allowing it once more.
    """
    app = output / LAUNCHER_NAME
    macos = app / "Contents/MacOS"
    macos.mkdir(parents=True, exist_ok=True)
    executable = macos / "ciel-launcher"
    source = ROOT / "services/launcher/main.c"
    subprocess.run(["cc", "-O2", "-Wall", "-o", str(executable), str(source)], check=True)
    shutil.copyfile(ROOT / "services/launcher/Info.plist", app / "Contents/Info.plist")
    subprocess.run(["codesign", "--force", "--sign", "-", "--identifier", "ai.ciel.launcher", str(app)],
                   check=True, capture_output=True)
    return executable


def render(template: Path, ciel_root: Path, home: Path, launcher: Path | None = None) -> bytes:
    with template.open("rb") as fh:
        document = plistlib.load(fh)
    launcher_path = str(launcher) if launcher is not None else "__LAUNCHER__"

    def replace(value):
        if isinstance(value, str):
            return (value.replace("__CIEL_ROOT__", str(ciel_root))
                    .replace("__USER_HOME__", str(home))
                    .replace("__LAUNCHER__", launcher_path))
        if isinstance(value, dict):
            return {key: replace(item) for key, item in value.items()}
        if isinstance(value, list):
            return [replace(item) for item in value]
        return value

    return plistlib.dumps(replace(document), sort_keys=False)


def ensure_log_dir(home: Path) -> Path:
    """Create the directory launchd will open the logs in.

    launchd opens StandardOutPath and StandardErrorPath before the program
    runs and cannot create their directory. The launcher must not do it
    either: a ``/bin/sh -c 'mkdir … && exec python'`` wrapper makes the
    shell the process launchd spawned, and macOS keys microphone permission
    to that process — an Apple platform binary is never asked, so the spoke
    came up hearing silence with no prompt. Rendering happens on the Mac
    that will run the service, so the directory is made here, once.
    """
    log_dir = home / ".ciel/log"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


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
    home = args.home.expanduser().resolve()
    ensure_log_dir(home)
    launcher = build_launcher(args.output.resolve())
    print(launcher)
    for template in sorted((ROOT / "services/launchd").glob("*.plist")):
        output = args.output / template.name
        output.write_bytes(render(template, ciel_root, home, launcher))
        print(output)


if __name__ == "__main__":
    main()
