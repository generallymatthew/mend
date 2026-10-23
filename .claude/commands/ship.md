---
description: Update STATUS.md with this session's work, commit, and push to origin
---

Do all three of these, in order, without asking for confirmation between steps:

1. **Update STATUS.md.** Read the current top of the file (`**Last updated:**` line and the paragraph after it). Write a new top entry summarizing what was actually built/fixed/verified in this session — specific enough that someone picking the project back up cold (including Matt on his other Claude account) understands what changed and why, not just a file list. Follow the file's own established voice and level of detail (see existing entries). Push the current `**Last updated:**` entry down to `**Previous update:**`, and if a `**Previous update:**` already exists, push that one down to `**Earlier:**` (further `**Earlier:**` entries below that already repeat the label — don't renumber them). Insert the new entry as the new `**Last updated:**`, dated today.

2. **Commit.** Review `git status` and `git diff --stat` first. Stage everything relevant (`git add -A` unless something looks like it shouldn't be committed, e.g. secrets — flag that instead of silently excluding it). Write a commit message in this repo's own style: a short summary line, then 1-2 short paragraphs on what changed and why (not a file-by-file list). If the working tree has unrelated pending changes from other sessions already sitting there, it's fine to bundle them into the same commit (this repo's own convention), but say so plainly in the commit body rather than claiming them as this session's work. Append the attribution line from the system reminder if one is present this session.

3. **Push.** Run `git push origin main`. `origin` (GitHub) is the only remote and the live deploy source; `gitlab` was retired as a remote on 2026-10-23 and no longer exists in this repo.

If there's nothing uncommitted and nothing to add to STATUS.md, say so instead of inventing a no-op entry/commit.
