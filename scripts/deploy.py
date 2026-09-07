#!/usr/bin/env python3
"""Validate source selection and preview a deploy; --apply performs it."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = {
    "ciel": ("ciel", "pyproject.toml", "ciel", "src/ciel/__main__.py"),
    "website": ("yunhan.me", "door/pyproject.toml", "door", "math/public/index.html"),
}


def validate_source(target: str, source: Path) -> Path:
    source = source.expanduser().resolve(strict=True)
    _, manifest, expected_name, marker = PROJECTS[target]
    if source == ROOT or not (source / ".git").exists():
        raise ValueError("source must be the application Git checkout, not infrastructure")
    with (source / manifest).open("rb") as fh:
        project = tomllib.load(fh)
    if project.get("project", {}).get("name") != expected_name or not (source / marker).is_file():
        raise ValueError(f"source does not contain the expected {target} application")
    return source


def validate_remote(host: str, destination: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.@-]*", host):
        raise ValueError("host must be a hostname or user@hostname")
    destination = destination.rstrip("/")
    if not re.fullmatch(r"(?:~/|/)[A-Za-z0-9_./-]+", destination):
        raise ValueError("destination must be an absolute or home-relative directory")
    if any(part in {".", ".."} for part in destination.split("/")):
        raise ValueError("destination must not contain traversal components")
    if destination.startswith("/") and len(Path(destination).parts) < 4:
        raise ValueError("absolute destination must name an application below its parent directories")
    return destination


def remote_cd(destination: str) -> str:
    if destination.startswith("~/"):
        return '"$HOME"/' + shlex.quote(destination[2:])
    return shlex.quote(destination)


def commands(target: str, source: Path, host: str, destination: str, sync: bool, apply: bool) -> list[list[str]]:
    source = validate_source(target, source)
    destination = validate_remote(host, destination)
    rsync = ["rsync", "-az", "--delete", "--itemize-changes"]
    if not apply:
        rsync.append("--dry-run")
    for exclusion in [".git", ".venv", "__pycache__", ".claude", ".codex", ".agents",
                      ".DS_Store", ".ruff_cache", "node_modules", ".env", ".env.*", "reports"]:
        rsync.extend(["--exclude", exclusion])
    if target == "website":
        # Older installs keep a service recovery copy in the app tree. Its
        # removal belongs to a deliberate service migration, not a site push.
        rsync.extend(["--exclude", "/door/deploy/door.service"])
    rsync.extend([str(source) + "/", f"{host}:{destination}/"])
    result = [rsync]
    if sync:
        project_dir = destination + ("/door" if target == "website" else "")
        options = " --no-default-groups --group hub --extra discord --extra web" if target == "ciel" else ""
        result.append(["ssh", host, f"cd {remote_cd(project_dir)} && ~/.local/bin/uv sync --locked{options}"])
    if target == "website":
        result.append(["ssh", host, "sudo systemctl restart door && systemctl is-active door"])
    else:
        result.append(["ssh", host, "systemctl is-active ciel-hub"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", choices=PROJECTS)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--host")
    parser.add_argument("--destination")
    parser.add_argument("--config", type=Path, default=ROOT / "config/deploy.toml")
    parser.add_argument("--sync", action="store_true", help="also synchronize server dependencies")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--apply", action="store_true", help="run the displayed deployment commands")
    mode.add_argument("--dry-run", action="store_true", help="run only rsync's remote dry run")
    args = parser.parse_args()
    try:
        with args.config.open("rb") as fh:
            config = tomllib.load(fh)["targets"][args.target]
        env_host = "CIEL_HUB_HOST" if args.target == "ciel" else "YUNHAN_HOST"
        host = args.host or os.environ.get(env_host) or config["host"]
        source = args.source or ROOT.parent / PROJECTS[args.target][0]
        plan = commands(args.target, source, host, args.destination or config["destination"], args.sync, args.apply)
    except (OSError, KeyError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Validated {args.target} source: {source.resolve()}", flush=True)
    for cmd in plan:
        print(shlex.join(cmd), flush=True)
    if args.apply:
        for cmd in plan:
            subprocess.run(cmd, check=True)
    elif args.dry_run:
        subprocess.run(plan[0], check=True)
    else:
        print("Preview only. Use --dry-run to compare with the server, or --apply to deploy.")


if __name__ == "__main__":
    main()
