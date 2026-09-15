# MSEL-001 — Pilot25 Entry Authority Amendment V12A

Status: PRE-ECONOMIC-EVALUATION / RESEARCH-ONLY / FROZEN
Date: 2026-09-15

## Why this amendment exists

The original V12 entry clause required the last valid observed BUY in the final 60 seconds at or before T+5 with quote notional >=0.01 SOL. The outcome-blind V13B/V13C audits showed this exact clause covers only 2/25 frozen launches, so V14 is not statistically usable under that entry authority.

This amendment is NOT triggered by observed returns, winners, catastrophes, slice performance, or any future-price behavior. The future source bytes acquired by V13 remain sealed for economic evaluation: V13A recorded returns_computed=FALSE, labels_computed=FALSE, slice_statistics_computed=FALSE, verdict_computed=FALSE; V13C/V13D/V13E explicitly did not decode the future raw transactions.

## Frozen replacement entry authority

Decision time remains launch time +300 seconds (T+5).

For every frozen launch, the primary entry reference is a deterministic gross 0.01 SOL Pump bonding-curve BUY quote reconstructed from the latest reconciled Pump TradeEvent state at or before T+5.

State selection:
- use the latest reconciled TradeEvent for the target mint at or before T+5;
- use ALL semantic classes for reserve-state authority, including events excluded from economic-flow features, because V13E validated exact reserve transitions across all 1056 consecutive transitions;
- carry that post-trade reserve state forward to T+5 only because no later reconciled Pump TradeEvent exists before the decision time.

Historical quote authority:
- pump-fun/pump-public-docs commit e2b66e4fce2fc130955912315167dc41e56956ad;
- docs/bondingCurve.ts helper `getBuyTokenAmountFromSolAmount`;
- gross input = 10,000,000 lamports;
- total fee basis points = event fee_basis_points + event creator_fee_basis_points when the event-reported creator is non-default;
- input_after_fee = gross_lamports * 10,000 // (10,000 + total_fee_bps);
- tokens_uncapped = input_after_fee * virtual_token_reserves // (virtual_sol_reserves + input_after_fee);
- tokens_received = min(tokens_uncapped, real_token_reserves);
- entry reference is unavailable if the resulting token amount is zero.

Primary entry price:
`entry_price_raw = 10,000,000 lamports / tokens_received_raw`.

The 0.01 SOL is a fixed gross hypothetical order size used only to establish a common executable reference price. It is not a live order and does not authorize trading.

## Frozen evidence supporting the amendment

V13D:
- 25/25 latest-state coverage;
- 25/25 executable 0.01 SOL historical-curve quote coverage;
- zero T+5 states with real_token_reserves == 0;
- zero cases where the real-reserve cap changed the quoted token amount;
- manifest SHA-256: 0be1742b64425a1e2f5b4e15ad58ec0b4468af6d79b064f71579ad16d72c55e6.

V13E:
- 1081 TradeEvents across 25/25 target mints;
- 1056 consecutive reserve transitions checked;
- 1056/1056 exact reserve transitions;
- zero mismatches;
- manifest SHA-256: 95a308535275680d16f5b5ddeff3f14d582b9d33838ba0ae9b7715c84288971f.

## Everything else remains frozen from V12

No change to:
- V11 feature matrix, score, risk order or 5/13/5 slices;
- T+5 decision time;
- +15m / +1h / +6h / +24h future windows;
- SELL-only primary future evidence;
- >=0.01 SOL economic SELL floor;
- Pump/PumpSwap historical schema and canonical migration-link rule;
- no interpolation;
- -80% catastrophe threshold;
- +100% winner threshold;
- CATASTROPHIC_LIQUIDITY_ABSENCE rule;
- OUTCOME_SOURCE_UNRESOLVED fail-closed treatment;
- secondary 3.00% round-trip stress;
- research-only / no live trading / no exchange mutation / no merge to main / no post-outcome tuning.

## Scientific status

V12A repairs an entry-source adequacy failure before economic outcome decoding. It does not claim an edge and does not authorize a full-MVE verdict.

After a deterministic input-binding check that pins V11 + V12/V12A + V13 sealed source + V13D + V13E, V14 Pilot25 economic evaluation may open the sealed future transactions exactly once under these frozen rules.
