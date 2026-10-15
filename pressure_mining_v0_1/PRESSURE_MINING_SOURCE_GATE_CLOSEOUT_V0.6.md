# CRYPTO LAB — PRESSURE MINING PRE-OUTCOME CLOSEOUT V0.6

Date: 2026-09-28
Branch: pressure-mining-program-v0.1
Status: CANONICAL 30M DISCOVERY IMPLEMENTATION PREFLIGHT PASS / PROTECTED OUTCOMES LOCKED

This V0.6 extends V0.5 with final protected-boundary and implementation-readiness evidence. All prior receipts remain preserved.

## COMPOUND-REALIZED-DISPOSAL-FLOW-001

### Scientific state

- MATERIALLY_NEW_MECHANISM_PASS / ZERO INHERITED CREDIT
- SOURCE_REALIZED_FLOW_PASS
- DEX_ROUTE_EVIDENCE_STRONG
- PREDICTOR_SAMPLE_VIABLE
- CANONICAL_30M_PREDICTOR_READY
- PREOUTCOME_PREFLIGHT_PASS
- PROTECTED 2025 MARKET OUTCOMES UNOPENED
- NO EDGE CLAIM

### Canonical economic authority

First freeze wins.

Canonical authority:
`pressure_mining_v0_1/labs/COMPOUND_REALIZED_DISPOSAL_FLOW_001_2025_ECONOMIC_DISCOVERY_FREEZE_V0.1.md`

- freeze commit: 2191bbf741ced5f801d8ae4034bd126c3b91cbc8
- canonical Git blob: d36c24bffd8a0f16787e0b7cf72b2d7b60e2f430
- exact horizon: 30 minutes
- assets: WETH/ETHUSDT, LINK/LINKUSDT, UNI/UNIUSDT, COMP/COMPUSDT
- benchmark: BTCUSDT
- direction: short collateral / long BTC
- BASE hurdle: 20 bps
- STRESS hurdle: 30 bps
- deterministic same-asset 30m overlap suppression
- UTC ISO-week cluster bootstrap
- all original 12 PASS gates and no-rescue rules preserved.

The later 5-minute draft remains NON-CANONICAL / DO NOT EXECUTE / ZERO SCIENTIFIC AUTHORITY.

### Historical realized-flow evidence

Canonical source run 36347379578 / artifact 10940652459:
- 999 BuyCollateral logs
- 899 unique transactions
- 47 buyers
- 7 assets
- 64/64 deterministic transactions usable
- 68/68 recipients reconstructed
- 59/68 same-transaction onward collateral transfers

### Corrected DEX route evidence

Canonical route run 36381340442 / artifact 10953181513:
- DEX_ROUTE_EVIDENCE_STRONG
- 59/59 onward-transfer events also contained recognized DEX swap evidence after BuyCollateral
- no swap price or market-return claim
- recognized DEX interaction does not prove net sell or edge.

### 2025 predictor-only evidence

Run 36347729253 / artifact 10940993512:
- 1,573 BuyCollateral events
- 1,470 unique transactions
- 51 buyers
- 10 assets
- 35 ISO weeks
- top buyer share 26.5734%
- PREDICTOR_SAMPLE_VIABLE.

### Exact canonical 30m readiness

Run 36382234645 / artifact 10952818650:
- 1,157 eligible raw logs in the four primary assets
- 1,148 transaction+asset aggregated events
- 373 events kept after deterministic 30m same-asset overlap suppression
- 775 suppressed overlaps
- 35 ISO weeks
- ETHUSDT 167
- LINKUSDT 93
- UNIUSDT 78
- COMPUSDT 35

All frozen sample gates pass pre-outcome.

### Protected 2026 boundary audit

Run 36382920798 / artifact 10953536735:
- status BOUNDARY_AUDIT_PASS
- pre-outcome readiness fingerprint exact match
- kept pre-boundary: 373
- protected-boundary exclusions: 0
- final eligible: 373
- 35 ISO weeks
- 2026 market outcome access remains zero.

Receipt pre-self SHA256:
47f017c23bfdc936d44fd368f7eac8014b9f2ccbdb72d480b78c2a5466465dbd

### Final outcome-blind implementation preflight

Finalized runner:
`pressure_mining_v0_1/compound_realized_disposal_30m_discovery.py`

Protected workflow:
`.github/workflows/compound-realized-disposal-protected-2025-discovery-v0.1.yml`

The protected workflow triggers only on creation/update of:
`.github/authorities/compound-realized-disposal-flow-001-2025.authorized`

That authority marker does not exist.

Canonical final preflight:
- run 36383070884
- artifact 10953426771
- artifact digest sha256:f74fb986382190657722fd2439bdc7a3d5beb96f42df7608b0ebd4f7d30228b1
- receipt pre-self SHA256 1e7404a1639a0401c57039cdaa98d85c607a1f2a1b56b7b6f9087f85f50b8204
- canonical freeze identity exact
- 60/60 required 2025 Binance Spot monthly 1m ZIP objects available
- 60/60 matching CHECKSUM objects available
- 60/60 checksum tokens syntactically valid
- final Discovery runner compiles
- synthetic timing/direction/cost/overlap/PF tests PASS
- PROTECTED_OUTCOME_LOCK_PASS
- PREOUTCOME_PREFLIGHT_PASS
- zero kline ZIP content opened during preflight
- zero market price values opened during preflight.

### Runner scientific implementation frozen before outcomes

The finalized runner now contains the complete canonical implementation:
- source fingerprint fail-closed before price access
- protected 2026 boundary firewall
- exact Binance checksum verification
- exact 30m entry/exit calculation
- relative BTC log return
- BASE20 / STRESS30 net transformation
- PF
- ISO-week clustered bootstrap 10,000 / seed 20260927
- per-asset and per-quarter diagnostics
- leave-one-asset-out
- positive-event and positive-week concentration
- all 12 frozen PASS gates
- terminal DISCOVERY_FAIL_NO_PROMOTION if any gate fails
- DISCOVERY_PASS_NOT_YET_TIER2 only if all gates pass.

No scientific rule remains to be designed after outcome access.

## Exact next gate

Current state:
**DISCOVERY IMPLEMENTATION READY-BUT-LOCKED.**

The only next scientific action is:
create the exact authority marker and execute the already-frozen protected 2025 Discovery **only after separate explicit operator authority naming COMPOUND-REALIZED-DISPOSAL-FLOW-001 / the protected 2025 30m Economic Discovery**.

Until then:
- do not create the marker;
- do not open Binance kline ZIP contents;
- do not compute 2025 returns, PF, bootstrap performance or PnL;
- do not touch 2026 market outcomes.

## Other Pressure Mining tracks

COMPOUND-INVENTORY-PERSISTENCE-001:
DISCOVERY_FAIL_NO_SUPPORT / TERMINAL.

PENDLE-PT-MATURITY-CONVERGENCE-001:
MECHANISM_DESCRIPTIVE / CLOSED AS ALPHA QUESTION.

PENDLE-FIXED-VARIABLE-YIELD-PREMIUM-001:
SOURCE_COMPLETENESS_PASS / ECONOMIC_PROVENANCE_INCOMPLETE / DISCOVERY_BLOCKED_PRE_OUTCOME.

LIDO-WITHDRAWAL-QUEUE-PRESSURE-001:
SOURCE_PASS_PROSPECTIVE_ONLY.

## Governance

No main merge.
No live trading.
No orders.
No exchange/wallet mutation.
No capital.
No paid data.
No protected 2025/2026 market outcome opening.
No post-outcome tuning.
No fabricated promotion.
