# EVENT-10M MU V0.4.1 — PRE-OUTCOME SOURCE HASH TRANSCRIPTION ERRATA
Recorded 2026-10-29, before any directional target or outcome was opened.

- Initial run #40908190805 failed on the **first MEXC index hash** (2026-10-26) after the stock source hash passed. The previously established two independent source-only jobs #40907599978 and #40907759684 both recorded exact correct opening index SHA256:
`6d263827363061ccb8f30a08b32a4472874b5a021ad16b1278f01fd4006a43db`.
- In the V0.4 freeze and code, the source hash was manually transcribed with `16f` instead of `16b` within the hash. This is a clerical copy error, NOT a new market-data change and NOT science tuning.
- Correct ONLY that one character in the runtime code; keep the incorrect original freeze text archived and this errata as immutable audit trail. Exact feature definition, decision times, 10min target, benchmarks, q assumptions, source dates/provider, stop-on-source-change and protected holdout remain unchanged. Update workflow step label solely to trigger the repeat.
- No actual price target, label, economic outcome, protected September, account/keys/real orders, main merge or live.
