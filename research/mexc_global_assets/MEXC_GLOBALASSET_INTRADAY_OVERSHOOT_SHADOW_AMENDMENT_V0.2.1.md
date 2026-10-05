# MEXC GLOBAL-ASSET INTRADAY OVERSHOOT — SHADOW TECHNICAL AMENDMENT V0.2.1

Date: 2026-10-05
Branch: `mexc-globalasset-intraday-overshoot-shadow-v0.2.1-remediation-2026-10-05`
Parent authority: `MEXC_GLOBALASSET_INTRADAY_OVERSHOOT_SHADOW_FREEZE_V0.2.md`
Status: FROZEN TECHNICAL REMEDIATION BEFORE ANY VALID IN-SESSION SHADOW OBSERVATION

## Authority boundary

This amendment changes execution-capture mechanics only.
The scientific signal remains exactly the V1.0 frozen rule:
- 13:30–20:00 UTC session authority; closed-candle scan remains 13:35–19:55 UTC;
- 5 minute lookback;
- Binance/Bitget leader dispersion <= 10 bps;
- abs MEXC move >= 40 bps;
- abs MEXC excess >= 35 bps;
- same-sign excess;
- FADE_MEXC_EXCESS;
- +5 minute exit;
- 10 minute global cooldown;
- simultaneous signals form one equal-weight event basket;
- no asset-specific tuning.

No historical V1.0 outcome is reopened or retuned.

## Why V0.2.1 is allowed

At the time of this amendment, the V0.2 branch had zero retrievable workflow runs.
No valid post-freeze 13:35–19:55 UTC observation had been opened.
Therefore these corrections are pre-observation execution engineering, not post-outcome tuning.

## Frozen technical corrections

1. LATE_SCAN is fail-closed.
   A scan more than 30 seconds after its frozen closed-candle timestamp is recorded as an integrity error and is not scored.

2. Source acquisition is concurrent across the 35 frozen candidates.
   This reduces deterministic serial-delay contamination without changing any signal threshold.

3. Accepted-trigger evidence persists exact raw public response bodies plus SHA-256 hashes and request timing metadata for MEXC, Binance and Bitget.

4. MEXC contract metadata is fail-closed.
   `contractSize`, `volUnit`, `minVol` and `maxVol` must all be valid and positive.
   Missing/invalid metadata may not default to 1.

5. Executable quantities are contract-valid.
   Each target notional bucket 10/25/50/100 USDT is converted to an executable contract quantity using the public top of book and frozen public contract metadata, rounded up to `volUnit` and bounded by `minVol/maxVol`.

6. Exit closes the exact same contract quantity opened at entry.
   It is prohibited to simulate exit by independently spending the same quote notional.

7. Entry and exit books are timing-qualified.
   Entry book capture must complete 0–30 seconds after the signal timestamp.
   Exit book capture must complete 0–30 seconds after the exact +5 minute timestamp.
   Outside this window the observation is invalid.

8. Receipt state is atomically checkpointed during capture.
   Partial/pending state is explicit. Final aggregation fails closed on pending events.

9. Frozen 10 minute global cooldown is applied deterministically across all collected segments by the V0.2.1 aggregator before any execution verdict.

10. Execution PnL is computed from same-contract entry/exit quote values.
    Primary operational fee remains the frozen 16 bps round trip.
    No maker fill assumption is permitted.

## Frozen evidence gate

Unchanged from V0.2:
- >=30 admitted shadow event baskets;
- >=5 distinct session dates.

Per notional bucket:
- any timing/source/book incompleteness => `EXECUTION_SOURCE_BLOCKED`;
- insufficient valid sample => `EXECUTION_SHADOW_UNDERPOWERED`;
- sufficient sample but mean/median or either chronological-half daily net after measured book execution and 16 bps fees <=0 => `EXECUTION_FEASIBILITY_FAIL`;
- all gates pass => `EXECUTION_FEASIBILITY_PASS__MICROLIVE_STILL_NOT_AUTHORIZED`.

## Current scientific/operational status at amendment

Historical frozen V1.0 remains:
`ROBUST_API_FEE_SURVIVOR`.

Prospective V0.2.1 cannot yet produce an execution-feasibility PASS/FAIL because the required future sample has not occurred.

Current prospective classification:
`EXECUTION_SHADOW_UNDERPOWERED`.

No orders, account reads, private endpoints, wallets, exchange mutation or live trading are authorized.
