# AMM-LVR-CROSSVENUE-001 — AUTHORITY RECONCILIATION V0.1

**Date:** 2026-09-23  
**Purpose:** resolve conflicting pre-outcome forward documents without changing the controlling scientific protocol.

## Authority order

Under Governance V4, the exact frozen protocol controls over a later implementation note when the two conflict.

The controlling economic protocol is:

**FORWARD_ECONOMIC_PROTOCOL_V0.1**
- commit 9994d109f6530069b480ce4bddbb34870e2155b0
- committed 2026-09-23T05:16:07Z

Earlier/later documents remain evidence but cannot override conflicting protocol fields:
- FORWARD_ECONOMIC_FREEZE_V0.1 — 2026-09-23T05:06:54Z
- FORWARD_ENGINE_IMPLEMENTATION_FREEZE_V0.1 — 2026-09-23T05:17:33Z

## Conflicts resolved

The controlling protocol requires:
- notionals 500 / 1,000 / 5,000 USDT;
- prospective DEX events, not synthetic quote-grid states, for economic adjudication;
- latency buckets T0 / +250ms / +1000ms / +3000ms;
- >=500 eligible events and >=14 calendar days before a scientific economic verdict;
- full required cost stack or event exclusion.

Therefore:
- the 100 USDT bucket in the implementation freeze is diagnostic only;
- the 48-state Quoter sweep is engineering diagnostics only;
- its candidate-state signs are not eligible events and carry zero adjudication or promotion credit;
- no protocol threshold, pair, direction, latency, fee, cost or venue may be changed because of that sweep.

## Engineering sweep contamination receipt

GitHub Actions run 35821948135 executed after the implementation note:
- 48/48 synthetic candidate states executable;
- 0 BASE known-cost positive states;
- 0 STRESS known-cost positive states;
- 0 independent events counted;
- 0 full-cost survivors claimed.

This result is preserved but **SCIENTIFICALLY NON-ADJUDICATING** for FORWARD_ECONOMIC_PROTOCOL_V0.1.

No rescue or tuning may use its sign.

## Token/pair universe

To prevent post-observation token selection, the protocol implementation inherits the already-frozen pre-economic pair set from FORWARD_ECONOMIC_FREEZE_V0.1:

- WETH-USDC
- WETH-USDT
- WBTC-WETH
- LINK-WETH
- PEPE-WETH
- SHIB-WETH

This is a conservative restriction of the broader protocol scope, not an outcome-selected amendment.

The controlling notionals remain only 500 / 1,000 / 5,000 USDT.

## Next valid evidence

Only prospective events satisfying FORWARD_ECONOMIC_PROTOCOL_V0.1 after this reconciliation may enter the protocol economic ledger.

The current source/classifier evidence is allowed as engineering/source evidence:
- public recent trace route PASS via dRPC;
- 17/17 frozen registry touches traceable;
- 6/17 contained activity in the pre-frozen Uniswap V3 pool set;
- 11/17 had a positive direct fee-recipient transfer;
- no CEX-Dex arbitrage was claimed.

No live trading, wallet mutation, paid data or main merge is authorized.
