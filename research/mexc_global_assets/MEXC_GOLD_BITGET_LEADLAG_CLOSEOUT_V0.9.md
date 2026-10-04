# MEXC-GOLD-BITGET-LEADLAG-001 — DISCOVERY CLOSEOUT V0.9

Date: 2026-10-04
Run: 37193998503
Rule SHA256: `6213dffe21dafd3903341a7093e4dba057577898822c35bd15224d83094cb649`
Artifact ZIP SHA256: `77dc6ab1a9a78f79da4387cbdf07f87f47606c8c0719b28557cccddf2e70bec3`

## Governance

- pre-outcome freeze: PASS
- discovery only
- no retrospective OOS
- no data at/after 2026-10-04T09:00:00Z
- no parameter rescue
- no accounts/wallets/private endpoints/orders/mutation
- no live trading

## Coverage

- exact clock coverage ratio: 0.9989711934
- source alignment: operationally valid

## Frozen result

- 36 cells tested
- pre-Holm eligible: 0
- Holm-selected: 0
- verdict: `NO_GOLD_CROSSVENUE_DISCOVERY_CANDIDATE_AT_FROZEN_V09_GATE`

## Diagnostic matrix summary

Widest gate: 3 bps Bitget shock / 2 bps lag gap.

- 1m: N=17, win rate 47.06%, mean gross +1.1948 bps
- 2m: N=15, win rate 46.67%, mean gross +1.4277 bps
- 5m: N=14, win rate 50.00%, mean gross +1.1678 bps
- 15m: N=13, win rate 7.69%, mean gross -8.1015 bps

5 bps shock / 2 bps gap:
- 1m: N=9, mean gross +2.0023 bps
- 2m: N=8, mean gross +2.2089 bps
- 5m: N=7, mean gross -0.6386 bps
- 15m: N=7, mean gross -10.2723 bps

10 bps shock cells had at most N=2.

The family failed because event counts were below the frozen N>=20 gate and directional/stability evidence was not sufficient. The longer 15m horizon was materially adverse.

## Scientific verdict

`NO_EDGE_AT_FROZEN_V09_GATE`

Do not lower thresholds or cherry-pick the small positive cells on this already-opened window.

## Campaign implication

Among the four initial Global Asset targets:
- SP500 MEXC contract/index basis remains the only replicated signal survivor;
- SP500 Hyperliquid 1m lead-lag: no edge;
- NAS100 Hyperliquid source binding: blocked;
- NVIDIA Bitget 1m lead-lag: no edge;
- GOLD Bitget 1m lead-lag: no edge.

Next legitimate work should focus on execution feasibility and future-forward validation of the replicated SP500 basis signal, not post-outcome retuning of failed cross-venue families.
