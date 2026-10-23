# Mend

## Git remotes

GitHub account restored (2026-10-14). `origin`
(`github.com/generallymatthew/mend`) is the only remote and the live
deploy source.

- `git push` with no remote specified means push to `origin`. Just do it.
- `gitlab` was retired as a remote on 2026-10-23 (no longer in use) and
  removed from the repo. Don't re-add it or push to it.
- Never ask which remote to use.

---

Before doing anything else in this project, read `STATUS.md` in this
directory. It is the rolling log of what actually happened and what state
things are in right now (not every commit, only verified checkpoints).

Whenever `STATUS.md` gets a new entry (a real checkpoint, per its own
"not every commit" rule above), commit and push to `origin` right after.
Don't batch a STATUS.md update with more work before pushing it, and
don't push on every small commit in between checkpoints — STATUS.md
updates are themselves the natural push cadence (see git-remotes
section above on why: pushing is the thing to keep infrequent, not
committing, which is local and free).

Also read `ROADMAP.md` for the phase-level checklist of what needs to be
true next, and `README.md` for what the project actually is.
