# Mend pitch

Open `Mend Pitch v2.dc.html` in a browser. Keep all files in this folder together: the page loads the others by relative path.

- `Mend Pitch v2.dc.html`: the pitch page (layout A/B switch, bottom right)
- `Mend Workflow Video.dc.html` + `mend-flow.jsx`: the one-minute workflow video
- `Mend Session Opening.dc.html` + `mend-opening.jsx`: the intake / joint session / caucus video
- `animations-v3.jsx`: animation engine used by both videos
- `support.js`: runtime for the .dc.html files
- `_ds/…/styles.css`: Organic design tokens (the pitch overrides colors at the top of its `<style>` block)

Serve the folder over a local web server rather than double-clicking, since browsers block some file loads from `file://`:

    cd "Mend Pitch"
    python3 -m http.server 8000

Then visit http://localhost:8000/Mend%20Pitch%20v2.dc.html

Copy lives inline in the HTML; video dialogue and timing live in the .jsx files (the `useLines` list in mend-opening.jsx, `msgs`/captions in mend-flow.jsx). Fonts (Caprasimo, Figtree) and React load from the internet.
