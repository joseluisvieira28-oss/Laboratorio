# OPTIONS-SPOTPERP-002 — TIER 1 ADJUDICATION CLOSEOUT V0.1

Date: 2026-09-16
Repository: joseluisvieira28-oss/Laboratorio
Branch: options-spotperp-002-tier1-2025-v01
Candidate: UP_LOW only
Governing authority: OPTIONS-SPOTPERP-002 — TIER 1 ADJUDICATION AUTHORITY V0.1
Authority commit: 2a8e90de37c3edb17549c8862c9382619b50f9aa
Promotion policy: ND-PROMOTION-POLICY-V2.0-FROZEN-2026-09-14

## FINAL ADJUDICATION

**TIER4_REJECTED**

The exact prospectively frozen OPTIONS-SPOTPERP-002 / UP_LOW candidate is not promoted and is scientifically rejected under the pre-existing Tier 1 adjudication authority.

This closeout does not rewrite the earlier Tier 2 Discovery classification. That historical evidence remains valid for its original sample. The independent 2025 one-shot OOS result answers the subsequent replication question and materially fails the frozen base-cost economics.

No rescue, rerun, threshold change, regime change, cost reduction, horizon change, asset selection, quarter selection, sign inversion, or post-outcome parameter modification is authorized.

## CANONICAL 2025 OOS EXECUTION

GitHub Actions run: 34885494558
Execution HEAD: e4a1e929b30a2eddaf8b3e090d56843dc558f866
OOS artifact ID: 10366279850
OOS artifact digest: sha256:e0b06751c58b9ff9f9dcffcc573653e7d1f6f9a345eed3f278cdbd4c504a8b0c
Source gate status: SOURCE_AUDIT_PASS
OOS classification: OOS_FAILED
OOS runner exit code: 3
2026 accessed: false
Live trading: false
Exchange mutation: false

## FROZEN OOS RESULTS

Regime observations / entered trades: 166 / 166
Frozen minimum entered trades: 80 — PASS

Regression beta: +0.0004199974
One-sided HAC p-value for beta > 0: 0.3261377311

### BASE — 10 bps round trip

Net mean: **-1.893223 bps/trade**
Profit Factor: **0.972063**
Cumulative net return diagnostic: **-3.093879%**
Maximum drawdown: **-23.399513%**
Implied gross mean before the frozen 10 bps cost: **+8.106777 bps/trade**

Quarter results:
- Q1: n=28; NET10 mean +0.967637 bps
- Q2: n=67; NET10 mean -7.508890 bps
- Q3: n=53; NET10 mean -20.282898 bps
- Q4: n=18; NET10 mean +68.706688 bps

Largest single-quarter share of positive gross PnL: 74.930262% — passes the frozen <=75% concentration gate.
Qualifying quarters with n>=15 and non-negative NET10: 2 — passes the frozen minimum of 2.

### STRESS — 20 bps round trip, diagnostic only

Net mean: **-11.893223 bps/trade**
Profit Factor: **0.837394**
Cumulative net return diagnostic: **-17.916035%**
Maximum drawdown: **-32.836790%**

## FROZEN GATE ADJUDICATION

PASS:
- adequate sample: 166 >= 80 entered trades;
- beta sign remains positive;
- at least two qualifying quarters have non-negative NET10;
- no single quarter exceeds 75% of positive gross PnL;
- 2026 remained locked;
- source/provenance gate passed.

FAIL:
- 10 bps net mean > 0;
- 10 bps Profit Factor > 1.0;
- required independent replication classification = OOS_REPLICATED.

Observed independent classification: **OOS_FAILED**.

The prospectively frozen Tier 1 authority states that adequate-sample independent OOS which materially destroys the frozen base-cost effect maps to **TIER4_REJECTED**. That rule is therefore applied mechanically here.

## SCIENTIFIC INTERPRETATION

The historical Discovery signal was real enough to justify the independent test, but it did not replicate economically in 2025 after the unchanged 10 bps cost. The direction coefficient remained positive, yet its uncertainty widened materially and the gross effect fell below the execution-cost hurdle. Positive performance was temporally uneven: Q4 was strong, while Q2 and Q3 were negative. These are post-outcome diagnostics only and must not be converted into a Q4 filter, seasonal filter, volatility-threshold change, or any other rescue of OPTIONS-SPOTPERP-002.

## GOVERNANCE CLOSEOUT

- Preserve the historical Tier 2 Discovery evidence as historical evidence only.
- Current scientific status of the exact UP_LOW candidate: **TIER4_REJECTED / OOS_FAILED**.
- Do not rerun the 2025 economic test to seek a different result.
- Do not use 2025 quarter/subperiod information to redefine the same candidate.
- 2026 remains unopened for this rejected exact candidate.
- No live trading, alerts, webhooks, orders, exchange mutation, deployment, or merge to main is authorized.
- Any future options/spot-perp research must be a materially different, prospectively frozen mechanism with its own MVE identity and cannot rewrite this result.
