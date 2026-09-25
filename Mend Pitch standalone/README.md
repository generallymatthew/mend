# Deprecated — do not build on this

This folder is the old bundled/minified export of the pitch page. It's superseded by [`../Mend Pitch/`](../Mend%20Pitch/), which is now the canonical source.

Two confirmed bugs, which is why we moved off it:

1. The two animations are embedded as `<iframe src="Mend Workflow Video.html">` / `<iframe src="Mend Session Opening.html">`. They don't load when the file is opened directly (`file://`, e.g. double-click) — only when served over `http://`. This is why the animation looked missing.
2. The "04 · How it works" numbered steps (1-8) render visually stacked/overlapping instead of laid out in sequence — a real CSS/scroll bug, not a preview artifact.

It's also a single-line bundled/minified export (~250KB, one line), effectively unpatchable by hand.

Keep this folder only for reference. Any further pitch-page work (content, animation timing, layout) goes in `../Mend Pitch/`.
