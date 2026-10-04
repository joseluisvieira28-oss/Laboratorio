# BITGET MAKER MICROSTRUCTURE SOURCE V0.1.1 — TECHNICAL AMENDMENT

Date: 2026-10-05

The first source-only probe confirmed public historical trade transport for all four frozen candidates but failed to discover the historical depth download route because the crawler only inspected HTML links and script URLs whose own names contained discovery keywords.

V0.1.1 changes source discovery only:
- fetches generic JavaScript bundles referenced by Bitget's official data-download page;
- searches those bundles for depth/download route and API strings;
- probes likely official route surfaces without downloading market-depth outcomes.

Unchanged:
- four-candidate universe;
- burned source date;
- trade source probe;
- no signal join;
- no fill model;
- no PnL;
- no microstructure outcome is opened.

A pre-outcome fill-model freeze remains mandatory before using any historical depth/trade outcomes.
