# BITGET MAKER MICROSTRUCTURE SOURCE V0.1.2 — CLASSIFIER CORRECTION

Date: 2026-10-05

V0.1.1 was too permissive: guessed depth page routes returning HTTP 200 can be generic SPA fallback pages and are not proof that a historical depth dataset is retrievable.

V0.1.2 tightens the source verdict:
- generic HTTP 200 route shells are not accepted as depth evidence;
- depth transport is accepted only if an official Bitget bundle exposes a concrete API path, downloadable file URL, or download route string tied to depth data;
- diagnostic bundle contexts/API paths/file URLs are emitted for audit.

Unchanged:
- frozen four-candidate set;
- burned source date;
- public trade source;
- no signal join;
- no fill model;
- no PnL;
- no microstructure outcomes opened.
