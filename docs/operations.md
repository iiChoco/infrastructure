# Operations

## Routing inventory

Verified through the deployed Cloudflare tunnel and Door on 2026-09-06:

| Host / path | Destination | Access |
|---|---|---|
| `yunhan.me/` | Door's public landing page | Public |
| `yunhan.me/toolbox` | Door's favorites-first launcher | Door account login |
| `yunhan.me/<word>` | Door's temporary short-link redirect | Public until its deadline, at most 24 hours |
| `tools.yunhan.me/qr`, `/color`, `/url`, `/convert`, `/image`, `/json`, `/pdf`, `/text`, `/password`, `/timer` | Door's private tools | Same shared Door login |
| `ciel.yunhan.me` | Ciel hub's Chart | Existing Cloudflare Access gate |
| `ciel.yunhan.me/interview` | Ciel Interview | Existing Access policy and application login |
| `auth.yunhan.me` | Door | Admin paths retain the additional owner Access gate |
| `math.yunhan.me` | Door's math static directory | Application login for per-user persistence |

The remotely managed `ciel-hub` tunnel sends apex, tools, auth, and math to
`http://100.118.127.52:8770`; Ciel stays on port 8765. Apex and tools have proxied
CNAME records to the same tunnel. Cloudflare automatically flattens the apex
CNAME; the three existing MX records and SPF TXT record were preserved and
verified unchanged. No Access policy was changed. Old apex `/tools/<slug>` URLs
redirect to the corresponding short path on the tools hostname.

The website deployment preserves the existing server paths, config, accounts,
and installed service unit. The pre-release source archive is
`/home/ciel/.cache/website-releases/before-tools-fi2eq4yp/source.tar.gz` on the VM;
it excludes the virtual environment and Git. Runtime state is outside that
archive. Roll back source independently of `~/.door`, particularly the reserved
short-link names in `shortlinks.sqlite3`. If removing this release's routing,
remove only the newly added apex/tools ingress and web CNAME records; preserve
all mail, Ciel, auth, math, and Access settings.

Validation: 25 website checks, 7 infrastructure checks, local browser checks for
cross-subdomain cookies and all ten tools, plus live HTTPS checks for the landing,
login redirects, private APIs, static assets, and Math. The VM resolves the new
apex normally; the Mac briefly retained a negative DNS cache from before the
record existed, so local HTTPS checks used a fresh Cloudflare DNS answer with
normal TLS verification. Production accounts were not modified for testing.

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

Website rsync excludes `/door/deploy/door.service` so a legacy service recovery
copy survives application deployments. It does not replace the installed unit
or the maintained definition in `services/systemd/door.service`.
