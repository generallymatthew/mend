# manager-app

UI mockup for a conflict-case manager tool for people managers, not employees. See `STATUS.md`'s "New product idea sketched and mocked: `manager-app`" entry for the full writeup of the flow and design decisions.

- `App.dc.html` — the mockup itself: a two-pane chat UI (conversation list left, one continuous thread right) with a right-side "plan so far" checklist panel.
- `canvas.json` — layout metadata from the Claude Artifact (Design canvas) these were authored in.

These are `.dc.html` files from the Claude Artifact design-canvas format (they reference `./support.js`, a runtime the Artifact page provides) — they won't render standalone by opening `App.dc.html` directly in a browser. View/edit the live version at the original artifact: https://claude.ai/artifact/8HrMPhjifgqAUiKVzPHx2L

Static mockup only. No backend, not wired into any other app in this repo.

- `PHILOSOPHY.md`: the product philosophy behind this app: conflict as task/process/relationship, why task conflict mutates into personal conflict, why peer-led resolution outlasts managerial arbitration, and the core reframe (action plan, not "conflict resolution").
- `WORKFLOW.md`: the concrete manager-facing flow: the step-by-step action-plan pattern, case-state persistence without breaking anonymity, and the decoupled hand-off into a peer-to-peer session.
- `THIMBLE_MINDSET.md`: draft system-prompt material for this app's facilitator, written to be integrated once there's a real backend here (none of it is wired into a running prompt yet).
