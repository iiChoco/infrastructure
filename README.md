# Personal infrastructure

Deployment and operations for two independent applications: Ciel and yunhan.me.
Application behavior, authentication code, and design assets stay in their own
repositories. This repository owns service definitions, deployment commands, and
the map of how the applications run together.

## Local layout

```text
~/Projects/
  ciel/             # Ciel; Git remote iiChoco/ciel (renamed from jarvis 2026-09-06)
  yunhan.me/        # website, Door, math, Instrument
  infrastructure/  # this repository
```

The parent directory is not a Git repository. Each repository has independent
history. The Mac's source layout does not dictate the server's source layout.

## Deploy

Python 3.12 or later is required; only the standard library is used.

```sh
python3 scripts/deploy.py ciel                 # validate and print commands; no network
python3 scripts/deploy.py website --sync       # preview deployment and dependency sync
python3 scripts/deploy.py ciel --dry-run       # compare with server using rsync dry-run
python3 scripts/deploy.py ciel --sync --apply  # perform deployment
```

Sources default to sibling `ciel` and `yunhan.me` checkouts. `--source` overrides
that location and is validated against the application's Git checkout and
project files. Host and destination defaults are in `config/deploy.toml`.
`--host`, `--destination`, and `--config` allow explicit overrides; existing
`CIEL_HUB_HOST` and `YUNHAN_HOST` overrides still work. Use ignored
`config/local.toml` for local overrides, passed with `--config`.

The application repositories retain `scripts/push_hub.sh` and `scripts/push.sh`
as forwarding commands. Unlike `deploy.py`, they deploy by default (`--preview`
prints only, `--dry-run` compares). Set `INFRASTRUCTURE_DIR` if this repository
is not under `~/Projects`.

An applied deployment uses rsync with deletion inside the selected application
directory. Review source and destination first. Application credentials,
virtual environments, Git metadata, and local agent settings are excluded.
Runtime data belongs outside the deployment directory. Dependency sync is
locked and errors propagate. The hub retains its existing source autoreload
behavior; Door is explicitly restarted after upload. This is still a source
sync deployment, not an atomic release mechanism.

## Services and state

| Component | Source on the server | Service / launch label | State |
|---|---|---|---|
| Ciel hub | `/home/ciel/ciel` | `ciel-hub` | `/home/ciel/.ciel` |
| Door and static sites | `/home/ciel/yunhan.me` | `door` | `/home/ciel/.door` |
| Mac spoke | `~/Projects/ciel` | `ai.ciel.spoke` | `~/.ciel` |
| Optional local all-in-one Ciel | `~/Projects/ciel` | `ai.ciel` | `~/.ciel` |

The server checkout moved to `/home/ciel/ciel` on 2026-09-06 (`~/jarvis` there is a symlink for stale pushes). `services/systemd/`
contains the units for that server layout. Copying these files locally does
not install them on the server. Installation and routing are documented in
[operations](docs/operations.md).

## Mac launch agents

```sh
python3 scripts/render_launchagents.py --ciel-root ~/Projects/ciel
plutil -lint rendered/ai.ciel.spoke.plist
```

Templates in `services/launchd` contain placeholders; install only rendered
plists. Rendering generates absolute paths without hardcoding a Mac username
in source, creates `~/.ciel/log`, which launchd must open before the program
runs, and builds `rendered/Ciel.app`, the launcher launchd actually starts.

The launcher exists for the microphone. macOS asks for it on behalf of the
*application responsible* for a process, and only an application whose
Info.plist says why (`NSMicrophoneUsageDescription`) is ever asked: Python's
bundle says nothing, so a spoke launchd starts as python is denied in
silence, and a `/bin/sh -c 'exec python'` wrapper is an Apple platform binary
that is never asked either. `Ciel.app` (`services/launcher/main.c`) is a
few lines of C that spawn Python as a child, forward launchd's signals, and
exit with the child's status. The first start prompts "Ciel" would like to
access the microphone; allow it, and the grant outlives every source reload,
since the child re-execs in place. It is ad-hoc signed, so **rebuilding the
launcher means allowing it again**. Prepare the Ciel environment with
`uv sync --locked --all-extras` in the Ciel checkout before loading a service.
Fresh environments also need openWakeWord's downloaded support models. This
applies even when the configured wake phrase uses a custom model in `~/.ciel`:

```sh
~/Projects/ciel/.venv/bin/python -c 'from openwakeword.utils import download_models; download_models(["hey_jarvis"])'
```

This provisions the shared feature/VAD assets and the stock model without
changing Ciel's configured wake phrase. During the migration, these cached files
were restored and hash-verified from the previous environment instead.

The launcher runs the prepared environment directly; it does not synchronize
dependencies at every restart. Run either the spoke or the all-in-one service
according to the intended setup, not both.

## Validation

```sh
python3 -m unittest discover -s tests -v
python3 scripts/deploy.py ciel
python3 scripts/deploy.py website
```

No credentials, live accounts, memory, recordings, private keys, or backups
belong in this repository. Store backups separately with restricted permissions.
This repository is local until a remote is explicitly configured and pushed.
