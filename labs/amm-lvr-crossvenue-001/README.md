# AMM-LVR-CROSSVENUE-001

Research question: after searchers, builders, gas, latency, CEX hedge costs and competition take their share, is there a repeatable economically accessible CEX-DEX/LVR opportunity for a non-integrated participant?

## Current state — 2026-09-23

- Laboratory: OPEN / protected prospective research
- Controlling authority: FORWARD_ECONOMIC_PROTOCOL_V0.1 + AUTHORITY_RECONCILIATION_V0.2
- Scientific verdict: **NOT OPEN**
- Source feasibility: PASS prospectively; free full historical full-cost route BLOCKED
- Frozen science:
  - six pair families: WETH-USDC, WETH-USDT, WBTC-WETH, LINK-WETH, PEPE-WETH, SHIB-WETH
  - notionals: 500 / 1,000 / 5,000 USDT
  - latency buckets: T0 / +250 / +1000 / +3000 ms
  - no economic adjudication before >=500 eligible events AND >=14 UTC calendar days
- Live capital: prohibited
- Main merge: prohibited without separate authorization

## Prospective evidence

### Canonical headroom pilot
Run 35823661252 / artifact 10734341315:
- 60 real DEX transaction events
- 43 unique block×pool states
- 129 notional states
- 100% causal Binance depth coverage at all four frozen latency buckets
- 0 positive PRE_INCLUSION_HEADROOM states
- full-cost PnL not computed
- zero scientific event credit

### Day-1 sequence 3
Run 35824550686:
- 60 real transaction events / 64 swap logs
- 60/60 traces
- 41 unique block×pool states / 123 notional states
- 100% depth coverage at T0 / +250 / +1000 / +3000 ms
- 20 events with positive direct fee-recipient transfer
- 0 runtime/source errors
- 0 positive PRE_INCLUSION_HEADROOM states
- zero scientific event credit

### Day-1 sequence 4 — persistent ledger validation
Run 35824869702:
- 60 real transaction events / 65 swap logs
- 60/60 traces
- 42 unique block×pool states / 126 notional states
- 100% depth coverage at T0 / +250 / +1000 / +3000 ms
- 22 events with positive direct fee-recipient transfer
- 0 runtime/source errors
- 0 positive PRE_INCLUSION_HEADROOM states
- persistent ledger snapshot + rollup committed successfully

Research-branch ledger commit:
- 520c9320eee676f04ff6fa6ee0da1b164745b6c9
- forward_ledger/2026-09-23__seq-4__run-35824869702.json
- forward_ledger/ROLLUP_V0.1.json

The persistent rollup currently starts at sequence 4:
- 1 persisted snapshot
- 60 deduplicated raw transaction candidates
- 65 deduplicated swap keys
- 1 UTC day
- **eligible_event_count_claimed = 0**

Earlier canonical/sequence-3 evidence remains preserved in immutable workflow artifacts and is not silently counted into the persisted rollup.

## Interpretation

Three prospectively observed Day-1 batches have shown zero positive PRE_INCLUSION_HEADROOM across every evaluated frozen notional and latency bucket.

This is a **strong negative diagnostic**, but it is **not NO_EDGE** because the controlling protocol requires >=500 eligible events AND >=14 UTC calendar days before adjudication, and the full accessibility stack remains unbound.

For any state whose PRE_INCLUSION_HEADROOM is already <=0, adding non-negative priority/builder/failure costs cannot make that state full-cost positive.

Missing accessibility layers for a hypothetical independent participant:
- priority fee required for competitive inclusion;
- direct/private builder payment required for inclusion;
- failed-inclusion probability / opportunity cost.

## Operations

The Forward Protocol + Headroom Daily workflow now:
1. captures protocol-compliant real swaps;
2. records causal Binance depth;
3. evaluates frozen pre-inclusion headroom;
4. creates an immutable compact ledger snapshot;
5. aggregates a deduplicated rollup;
6. persists the snapshot and rollup on this research branch;
7. uploads the evidence artifact.

The existing Radar Fishing Watch contains the AMM-LVR daily guard. At most once per UTC day it may trigger a missing daily capture and repair technical/source plumbing only. It may not change frozen science, create a rescue variant, use capital, mutate an exchange, purchase data or merge main.

## Current next action

Accumulate genuinely new UTC-day evidence under the unchanged protocol. Do not spam same-day captures for promotion credit. If a future state has positive PRE_INCLUSION_HEADROOM, immediately bind the remaining competitive-inclusion costs for that exact prospectively observed candidate before it can receive positive scientific credit.

Read:
- PRE_DISCOVERY_FREEZE_V0.1.md
- FORWARD_ECONOMIC_PROTOCOL_V0.1.md
- AUTHORITY_RECONCILIATION_V0.2.md
- FORWARD_HEADROOM_PILOT_CLOSEOUT_V0.1.md
