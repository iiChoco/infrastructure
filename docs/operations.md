# Operations

## Routing inventory

The existing application documentation describes these routes on the same VM:

| Host / path | Destination | Access described in application docs |
|---|---|---|
| `ciel.yunhan.me` | Ciel hub's web interface (Chart) | Owner's Cloudflare Access gate |
| `ciel.yunhan.me/interview` | Ciel Interview, served by the hub | Application account login; separate Access policy |
| `auth.yunhan.me` | Door | Application login; admin paths additionally owner-gated |
| `math.yunhan.me` | Door serving the math static directory | Application login for per-user persistence |

These are an inventory from repository documentation, not a downloaded or
verified production tunnel configuration. Retrieve the deployed ingress and
Access settings before changing routing. The root site's deployed origin was
not established by the repository audit. No DNS/tunnel/Access settings were
changed during the local reorganization.

## Server configuration

- Ciel: `/home/ciel/.ciel/config.toml`; login environment in `.ciel/hub.env`.
- Door: `/home/ciel/.door/config.toml`; `instrument` and `[sites]` select assets
  under `/home/ciel/yunhan.me`.
- Shared account files remain runtime data. The Door/Ciel account compatibility
  issue identified in the earlier audit is a separate application change.

When deliberately installing changed units on the server, copy the relevant
file from `services/systemd` into `/etc/systemd/system`, run
`sudo systemctl daemon-reload`, and restart only that service. Verify with
`systemctl is-active ciel-hub` or `systemctl is-active door`, inspect its journal,
and exercise its user interface. Do not change server working directories just
because a local checkout moved.

## Local migration and recovery

The September 2026 reorganization preserves runtime state in `~/.ciel` and
`~/.door`. Source directories move to `~/Projects`; compatibility symlinks at
`~/jarvis` and `~/yunhan.me` preserve older references and active workspaces.
Leave these links until active agent sessions and saved workspaces have been
reopened at the new paths. Codex's existing task retains its original sandbox
root; a symlink at that root is not accepted by its ordinary shell sandbox.
Reopen Ciel at `~/Projects/ciel` for subsequent work; compatibility links alone
do not migrate a saved application's sandbox configuration. They are links to the same repositories, not copies.

Private pre-migration backups live under `~/Projects/.migration-backups/`.
Each timestamped directory contains source/Git archives, the original local
launchers and Ciel configuration, and Claude project-state/config backups.
The backed-up Git trees include the pre-existing uncommitted work. Virtual
environments are excluded from archives; rebuild them from lockfiles with the
required extras. Keep these backups outside Git. The original virtual environments were also
retained as `ciel.venv` and `door.venv` in the migration backup directory; their
old-path entry points are a recovery resource, not the active environments.

For rollback, stop the spoke first, remove only compatibility symlinks after
checking that they are symlinks, and move the source directories back. Preserve
all changes made after migration before restoring any archive. Restore the
backed-up local launcher/config files, rebuild environments at the restored
paths, and reload the originally active launch agent. Do not load previously
inactive services. Server rollback is unnecessary for a local-only move.

## Backup follow-up

This repository documents recovery but does not yet schedule production
backups. Define and verify a separate encrypted backup/restore process for
runtime memory, accounts, interview recordings, configuration, and the server
before relying on the source repository as an operational recovery system.
