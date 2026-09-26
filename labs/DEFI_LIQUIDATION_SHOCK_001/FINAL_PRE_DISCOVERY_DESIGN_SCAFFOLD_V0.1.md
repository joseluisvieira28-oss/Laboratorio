# DEFI-LIQUIDATION-SHOCK-001 — FINAL PRE-DISCOVERY DESIGN SCAFFOLD V0.1

Date: 2026-09-27
Status: PROSPECTIVE SCAFFOLD / NOT AUTHORITY / OUTCOME-BLIND

## Scientific question inherited from PRE-SOURCE AUTHORITY V0.1

Can successful, objectively identifiable on-chain DeFi liquidations create a causal forced-flow event population that is known before any tested future price window and supports a later prospectively frozen market-outcome Discovery?

This scaffold does NOT authorize market outcomes. It defines the structure that the final authority must freeze after GLOBAL_FIELD_COVERAGE_FINAL_PASS.

## Protected data

- 2025 market outcomes: CLOSED
- 2026 market outcomes: CLOSED
- no price/return/PnL access before final authority commit
- no post-outcome tuning

## Source event universe

Frozen protocol families:
- Save/Solend 0x0c
- Save/Solend 0x11
- marginfi v2
- Kamino Lend
- Drift v2 four frozen liquidation classes

Only realized successful events from terminal source authorities may enter the later experiment.
Failed liquidation attempts remain a separate control/descriptive ledger and never become realized forced-flow events.

## Canonical event identity

The canonical source event is the already frozen instruction identity:

protocol + instruction_class + signature + instructionAddress

Required causal time ordering:
timestamp UTC -> slot -> transactionIndex -> instructionAddress -> signature

No future market data may alter deduplication or event membership.

## Event-field precondition

Before this scaffold can become FINAL PRE-DISCOVERY AUTHORITY:

- GLOBAL_FIELD_COVERAGE_FINAL_PASS must exist;
- protocol account/asset/market identity coverage must be terminal;
- unit/precision metadata must be terminal;
- unresolved required source fields = 0;
- guessed decimals/mappings = 0.

## Cascade / clustering authority to freeze later

The final authority MUST define:
1. whether clustering is protocol-local, asset-local, or cross-protocol;
2. exact gap/window rule in source time;
3. deterministic cluster start/end;
4. treatment of multiple instructions in one transaction;
5. treatment of overlapping candidate clusters;
6. whether failed attempts may be used only as controls.

The rule may be calibrated only from source-event timing/identity distributions, never from future market returns.

If multiple source-only timing rules are retained as sensitivity analyses, they must be frozen before outcomes and multiplicity-controlled.

## Event-size / forced-flow semantics

Instruction argument values that are protocol request/max limits are NOT automatically realized economic flow.

Before any event-size analysis, final authority must distinguish:
- requested/max instruction argument;
- realized debt transfer;
- realized collateral transfer;
- protocol-native unit normalization;
- event-time notional if ever used.

No requested/max argument may be substituted for realized flow unless a separate source authority proves equivalence prospectively.

## Market mapping

The final authority MUST map each source event to an executable/research market without future return selection.

Allowed mapping inputs:
- source asset mint / protocol market index;
- historically valid unit metadata;
- prospectively frozen market availability rule.

Forbidden:
- selecting the exchange/pair after seeing which had the strongest response;
- dropping assets/protocols due weak outcomes.

## Price-source authority

Before Discovery, freeze:
- primary historical market-data source;
- fallback source;
- timestamp granularity;
- clock/timezone normalization;
- missing-candle policy;
- source conflict policy;
- corporate/token redenomination/symbol migration handling where relevant.

2025/2026 remains unopened.

## Event-to-price alignment

The final authority MUST use only price information available at or after the event timestamp for future-return windows.

It must freeze:
- event timestamp -> first eligible price observation rule;
- bar boundary treatment;
- event inside bar treatment;
- delayed/missing quote policy;
- no back-filling with future observations.

## Outcome family structure

Primary scientific outcome family should be compact.

Required categories to freeze before outcomes:
- signed future return aligned to the prospectively defined forced-flow direction;
- absolute / realized move as a direction-agnostic response;
- control/baseline comparison;
- optional volume/liquidity response only if source authority and multiplicity plan support it.

No outcome category may be added after seeing results.

## Horizons

No horizon is authorized by this scaffold.

The final authority must freeze a small horizon set prospectively.
If more than one horizon is tested, the family-wise multiplicity treatment must be frozen at the same time.

## Baseline / control

The final authority must freeze a control design that cannot use future outcome magnitude to select controls.

Possible admissible structures include:
- matched same-asset same-clock non-event windows;
- pre-event historical volatility matched windows using information strictly before T0;
- protocol/event-size strata if size authority is proven before outcomes.

The exact control rule remains PENDING until field coverage and market mapping are terminal.

## Overlap rule

A future-return observation may not be silently counted multiple times because events/cascades overlap.

The final authority must freeze one rule:
- cluster before outcome measurement; or
- deterministic first-event wins; or
- retain overlaps with an explicit dependence-aware inference method.

No overlap rule may be chosen after viewing returns.

## Statistical authority

Before outcomes freeze:
- primary estimand(s);
- minimum source sample gate;
- confidence interval/bootstrap design;
- null model;
- multiple-testing correction across horizons/assets/protocol strata;
- minimum effect-size criterion;
- missing-data exclusion rule;
- sensitivity analyses;
- PASS / FAIL / NO_EDGE / SOURCE_BLOCKED taxonomy.

Statistical significance alone must not be sufficient for promotion.

## Discovery / OOS / protected holdout

The final authority must partition time prospectively before outcomes.

Required structure:
1. Discovery period from the already source-audited historical window;
2. OOS period not used for tuning;
3. 2025/2026 protected holdout remains CLOSED until separately authorized by the frozen gate.

No protected-period peek is permitted to rescue a weak Discovery/OOS result.

## Promotion taxonomy

SOURCE_BLOCKED:
required source/field/market-data authority cannot be established.

NO_EDGE:
scientifically valid experiment completes but frozen economic/statistical promotion gates fail.

SURVIVES_DISCOVERY:
frozen Discovery gates pass; not equivalent to tradable edge.

SURVIVES_OOS:
frozen OOS gates pass; still not live-trading authority.

Any later "quase diamante" label must reference explicit governance criteria external to this scaffold.

## Finalization condition

This scaffold may be superseded by FINAL_PRE_DISCOVERY_AUTHORITY_V0.1 only after:

GLOBAL_FIELD_COVERAGE_FINAL_PASS

and after every remaining PENDING design field above is numerically/operationally frozen without market-outcome access.

## Firewall

prices=false
returns=false
pnl=false
directional_outcome=false
economic_outcomes=false
protected_2025_2026_market_outcomes=false
live_trading=false
orders=false
wallets=false
exchange_mutation=false
paid_source=false
post_outcome_tuning=false
merge_main=false
