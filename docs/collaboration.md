# Working together

These five rules also live in each app's `AGENTS.md` so fresh clones stand alone.

- One writer per checkout. Parallel implementation needs separate worktrees
  and agreed file ownership.
- Read status and diffs before starting; re-read each file immediately before
  editing and reconcile any changes.
- Preserve other tasks' uncommitted work. Never discard, stash, stage, commit,
  or reformat it as cleanup.
- Reviews provide findings, evidence, and proposed fixes; the assigned writer
  makes the changes.
- Keep settled decisions unless changed requirements or new evidence justify
  revisiting them; record the reason.

Each repository's conventions and configured checks govern style. Google's
[Python](https://google.github.io/styleguide/pyguide.html) and
[JavaScript](https://google.github.io/styleguide/jsguide.html) guides are optional
references, not review requirements. Permission covers the user's stated task
and scope; it does not carry over to unrelated work.
