# Local repository migration — September 6, 2026

## Result

- Ciel: `/Users/choco/Projects/ciel`; original GitHub remote and all history preserved.
- Website: `/Users/choco/Projects/yunhan.me`; original remote and history preserved.
- Infrastructure: `/Users/choco/Projects/infrastructure`; new independent local Git repository.
- Existing application repositories use branch `codex/repository-organization`.
- Ciel's pre-migration working tree was checkpointed as `18d088c` before organization edits.
- Old local source paths are compatibility symlinks to the moved repositories.
- Deployment service definitions now live in infrastructure. Existing application
  deployment commands forward here and preview by default; `--apply` deploys.
- Server checkout paths, deployed source, and domain routing were left unchanged.

## Local state

Private backups: `/Users/choco/Projects/.migration-backups/20260906T203558Z`.

Both environments were recreated from existing lockfiles; Ciel retained all
extras. The first spoke restart exposed downloaded openWakeWord support models
that are absent from a newly installed environment. The cached model files were
restored from the old environment and verified by SHA-256, and the configured
custom wake detector successfully initialized before the final restart.

Installed launch agents now point to the new checkout. Only the previously
running spoke was restarted; the all-in-one service stayed unloaded and the
sections-refresh service stayed disabled. Its script reference and the sections
refresh command in Ciel's live config were updated. Runtime memory, accounts,
recordings, and model paths under `~/.ciel` were preserved.

New Claude project-state directory names alias the original state directories;
new project settings entries copy the original settings while preserving the
old entries for active sessions. Historical transcripts were not rewritten.
Session continuation in a newly opened Claude window has not been exercised.
Reopen saved development workspaces at the new paths; the current Codex task
still has its old path registered as a sandbox root.

## Verification

- Before and after relocation: hub-import probe 2 checks, turn probe 71,
  spoke probe 52, world-state probe 121 — all 246 passed.
- Infrastructure tests cover source validation, preview behavior, remote dry-run
  isolation, destination validation, and launcher rendering with special characters.
- Both deployment forwarding commands resolve the correct application source
  and preserve the existing remote destination. Preview commands made no network calls.
- Ciel and Door CLI entry points and bundled assets resolve from the new paths.
- Piper, speaker verification, audio, AppKit, and the configured custom wake detector initialize/import.
- Installed launch-agent files pass `plutil -lint`.
- The final spoke launch reports running, one run, no exits, with source and
  interpreter under `/Users/choco/Projects/ciel`; its log reports ready.
- Read-only SSH checks report both `ciel-hub` and `door` active on the server.

## Existing issue and separate work

The spoke logs connection timeouts to its configured hub endpoint. The same
endpoint and timeout appear in pre-migration logs. The local Tailscale CLI reports `BackendState: Stopped` and the local node
offline. Tailscale was left in its existing state. This is not a verified
end-to-end voice conversation; the local tailnet connection must be restored
before the spoke can reach the hub.
No server restart, deployment, routing change, or authentication refactor was
performed. The Door/Ciel authentication divergence remains separate work.
