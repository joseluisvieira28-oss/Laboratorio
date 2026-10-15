# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — PRE-OUTCOME GOVERNANCE RECONCILIATION V0.1

Date: 2026-09-28
Status: CANONICAL AUTHORITY RESOLVED / NO OUTCOME OPENED

## Conflict discovered

Two pre-outcome economic documents exist on the feature branch:

1. **Canonical earlier freeze**
   `COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_ECONOMIC_DISCOVERY_FREEZE_V0.1.md`
   - commit: 2191bbf741ced5f801d8ae4034bd126c3b91cbc8
   - commit time: 2026-09-27T20:25:02Z
   - exact primary: four assets, 30-minute relative horizon, deterministic overlap suppression, BASE 20 bps, STRESS 30 bps.

2. **Later 5-minute draft**
   `COMPOUND_REALIZED_DISPOSAL_FLOW_001_ECONOMIC_DISCOVERY_FREEZE_V0.1.md`
   - commit: d7e870632faabe8c4c3b39bcbe9052d6cc3be228
   - commit time: 2026-09-28T05:22:54Z
   - created after later source-only route evidence and before any protected market outcome.

## Adjudication

**FIRST FREEZE WINS.**

The 30-minute V0.1 contract remains the only canonical protected 2025 economic authority.

The later 5-minute document is classified:
**NON-CANONICAL PRE-OUTCOME DRAFT / DO NOT EXECUTE / ZERO SCIENTIFIC AUTHORITY**.

Reason:
- no market outcome had been opened, so the later draft created no outcome contamination;
- however changing horizon, asset population, event clustering and inference after a canonical freeze would create avoidable governance ambiguity;
- source-only DEX route evidence strengthens the underlying mechanism but does not require changing the already frozen economic contract.

## Canonical test preserved exactly

Primary assets:
WETH->ETHUSDT, LINK->LINKUSDT, UNI->UNIUSDT, COMP->COMPUSDT.

Benchmark:
BTCUSDT.

Horizon:
30 minutes.

Entry:
first complete Binance Spot 1m bar whose open is strictly after Ethereum block timestamp.

Exit:
open exactly 30 one-minute bars after entry.

Event construction:
aggregate same Ethereum transaction + same collateral asset; deterministic same-asset 30m overlap suppression.

Costs:
BASE 20 bps round-trip total; STRESS 30 bps.

All PASS gates and no-rescue rules remain exactly those in the 2025 Economic Discovery Freeze V0.1.

## Route evidence treatment

Corrected DEX-route run 36381340442 is admissible **source/mechanism evidence only**.

It may strengthen the causal plausibility of the already-frozen 30m hypothesis.
It may not alter:
- horizon;
- direction;
- assets;
- costs;
- overlap rule;
- PASS gates;
- benchmark.

## Firewall

protected_2025_market_outcomes_opened=false
market_prices_opened=false
returns_computed=false
pnl_computed=false
canonical_economic_contract_changed=false
five_minute_draft_executable=false
live_trading=false
orders=false
capital=false
main_merge=false
post_outcome_tuning=false
