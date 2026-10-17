# Design handoffs

Design-reference implementations (vanilla HTML/JS, dependency-free) handed
off for porting into the real apps — not meant to be dropped in unchanged.
Each subfolder has its own `README.md` with specifics (fidelity, anatomy,
state tables, etc).

- `mend_sessions/` — the Mend Intake / Joint Session design pass, plus the
  shared brand kit (`mend-brand-kit/`: colors, logos).
- `simple_agent_presence/` — an earlier, simpler agent-presence exploration.
- `thimble_avatar-new-mow/` — the current Thimble avatar reference
  (`thimble-avatar.js`), ported into `intake-app/static/index.html`'s
  `updateThimbleMotion`/`THIMBLE_SHAPES`.

Previously these three lived as separate `design_handoff_*` folders at the
repo root; grouped here so root isn't cluttered with one-off handoff drops.
