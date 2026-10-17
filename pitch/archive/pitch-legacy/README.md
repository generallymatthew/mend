# Pitch page — legacy exports

Both subfolders are old bundled/minified exports of the pitch page, superseded
by [`../../Mend Pitch/`](../../Mend%20Pitch/), which is the canonical source
to build on now (editable `.dc.html` + `.jsx`/`.js`, not a single-line bundle).

- `standalone-1/` — was `Mend Pitch standalone/`. Has its own `README.md`
  with the two confirmed bugs that led to moving off it (iframes don't load
  over `file://`, and the "How it works" steps render stacked instead of in
  sequence).
- `standalone-2/` — was `Mend Pitch standalone 2/`. A separate export,
  undocumented at the time; kept for reference alongside `standalone-1/`
  rather than discarded, since no one had confirmed it's safe to delete.

Neither is referenced by any app or build script. Kept for reference only —
don't develop against either.
