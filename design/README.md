# design/

The design deliverable of record for Cartograph, from Claude Design.

- `Cartograph.dc.html` — the clickable prototype. Open it in a browser. Real Cytoscape.js map, live PDBe Mol* (7DHG), the structural edge dossier, the eval-as-green-edges flow, node panel, confidence slider, layer toggles, compare mode, upload, and JSON export. This is the visual and interaction target for the real frontend.
- `support.js` — the Claude Design prototype runtime (the sc-* template framework). Not part of the production app; it powers the prototype only.
- `cartograph-data.js` — the reference dataset with real flagship names. Directly reusable in the build (subject to the carry-forward fixes).
- `cartograph-spec.js` — in-app spec / config.
- `wow_moment_mock.html` — the earlier hand-built North Star, kept for reference.
- `CARRY_FORWARD.md` — READ THIS before building the frontend. Four items that must move from illustrative design data to real, plus the good parts to preserve.

Build the real frontend to match this prototype and the direction in `../docs/Cartograph_Claude_Design_brief.md`, applying `CARRY_FORWARD.md`.
