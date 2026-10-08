# manager-app

UI mockup for a conflict-case manager tool for people managers, not employees. See `STATUS.md`'s "New product idea sketched and mocked: `manager-app`" entry for the full writeup of the flow and design decisions.

- `App.dc.html` — the mockup itself: a two-pane chat UI (conversation list left, one continuous thread right) with a right-side "plan so far" checklist panel.
- `canvas.json` — layout metadata from the Claude Artifact (Design canvas) these were authored in.

These are `.dc.html` files from the Claude Artifact design-canvas format (they reference `./support.js`, a runtime the Artifact page provides) — they won't render standalone by opening `App.dc.html` directly in a browser. View/edit the live version at the original artifact: https://claude.ai/artifact/8HrMPhjifgqAUiKVzPHx2L

Static mockup only. No backend, not wired into any other app in this repo.
