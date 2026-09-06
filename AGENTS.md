# Working on infrastructure

Read [the collaboration policy](docs/collaboration.md) before editing.
The app repositories carry the same five rules in their own guides so they
work without this checkout.

## Scope and style

- Own deployment tooling, service definitions, routing/configuration examples,
  and operations documentation. Ciel and website behavior, authentication
  implementation, and design assets stay in their application repositories.
- Python tools use Python 3.12 and the standard library. Follow the existing
  argparse, pathlib, tomllib, explicit validation, and subprocess argument-list
  patterns. Keep pure command construction separate from command execution.
- Validate source, destination, and mode before a destructive command can run.
  Preserve exit codes. Quote remote shell arguments explicitly; never interpolate
  arbitrary paths or secrets into shell text. Do not introduce dependencies or
  a new deployment platform during routine maintenance.
- Match neighbouring formatting. Give functions descriptive names and type
  hints; comments explain constraints. Use TOML for target configuration and
  plist templates plus the existing renderer for Mac launch agents.
- Keep template placeholders portable. Machine-specific installed files and
  secrets do not become templates by copying them into Git. Keep generated
  output, backups, credentials, and live application state untracked.
- Write direct operational instructions with preconditions, actual commands,
  expected results, and recovery steps. Keep examples executable and clearly
  distinguish planned configuration from verified live state. Match the existing
  sentence-style commit titles when a commit is requested.

## Preserve the command contracts

| Command | Default | Harmless local preview |
|---|---|---|
| `python3 scripts/deploy.py ciel` or `website` | Print only | The default |
| Ciel `scripts/push_hub.sh` | Deploy | `--preview` |
| Website `scripts/push.sh` | Deploy | `--preview` |

`--dry-run` contacts the server for an rsync comparison. `--sync` adds dependency
synchronization to an applied deployment. Do not infer that a forwarding script
shares the underlying command's default. Change these contracts only within an
explicitly requested behavior change; update both wrappers, docs, and checks.

Server paths are configuration. Read `config/deploy.toml`, service units, and
`docs/operations.md`; do not infer them from local directory names or old chat
history. Changing a template does not install it. A cloud connection does not
constitute permission to deploy or change DNS, tunnels, or Access policies.

## Verification and handoff

For changes to executable tooling or templates, run:

```sh
python3 -m unittest discover -s tests -v
```

Add checks for meaningful failures such as wrong-source selection, argument
quoting, unintended remote execution, and template rendering. Use mocked commands
and temporary paths; checks must not deploy, restart services, or use live secrets.
Validate rendered plists with `plutil -lint` when applicable. Rendering a file
is not a service-installation test; report that distinction.

For documentation-only changes, check references against code and run
`git diff --check`; do not run a deployment to validate prose. Update the README
and operations guide when the documented behavior changes. Work on the assigned
branch; no branch changes, commits, pushes, or live mutations unless authorized.
Stage explicit files when committing. Handoffs distinguish local edits, rendered
configuration, installed configuration, and verified running services.
