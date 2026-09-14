# TOKEN-UNLOCK-EVENT-001 — PRE-SOURCE PROTOCOL V0.1

STATUS: FROZEN_PRE_OUTCOME / SOURCE-DATA-GATE ONLY
MODE: RESEARCH-ONLY / FAIL-CLOSED
2025: LOCKED
2026: LOCKED
LIVE TRADING: FORBIDDEN
EXCHANGE MUTATION: FORBIDDEN
MAIN MERGE: FORBIDDEN

## Anti-duplication boundary

This lab is NOT a replacement, rescue, or retune of SUPPLY-DILUTION-001 / SD-DILUTION-12W-001. The earlier MVE remains unchanged and SOURCE_AUTH_OR_ACCESS_BLOCKED. It used weekly realized 12-week circulating-supply dilution. No return outcome was opened.

This lab tests a distinct event mechanism: discrete scheduled token unlocks whose timing and amount were demonstrably public before the event.

LAB_ID: TOKEN-UNLOCK-EVENT-001
MVE_ID: TUE-CLIFF-ADV30-001

## Economic mechanism

A discrete scheduled cliff release creates newly transferable supply. If the released amount is large relative to the market's recent absorption capacity, recipients have greater potential to create sell pressure. The event is anticipated, so any effect may begin before the on-chain release. The existence, sign and timing of an exploitable effect must be demonstrated; unlock != automatic price decline.

## Frozen first-MVE event definition

Eligible event = discrete scheduled cliff unlock / discrete vesting release.

Excluded from MVE1:
- continuous emissions;
- mining/staking issuance;
- burns or buybacks;
- purely discretionary treasury transfers with no pre-announced release schedule;
- events whose schedule cannot be proven point-in-time;
- surprise schedule changes (reserved for a separate future hypothesis);
- post-unlock exchange-flow behavior (reserved for a separate future hypothesis).

## Frozen signal family and direction

Primary exposure metric after the source gate:

unlock_pressure_days = scheduled_unlock_tokens / trailing_30d_average_daily_Binance_spot_base_asset_volume

The denominator is measured in units of the same token, using only pre-event data. No future information is permitted.

Expected economic direction is frozen now, before outcomes:

higher unlock_pressure_days -> expected weaker subsequent return.

No inverse rescue is permitted if the observed sign is positive.

## Why this normalization is first

It avoids the unresolved PIT circulating-supply entitlement/provenance blocker that stopped SD-DILUTION-12W-001. It also measures the release relative to observable absorption capacity rather than headline USD size. Historical Binance spot klines contain base-asset Volume and are available in daily/monthly archives with checksums.

Alternative normalization unlock_tokens / pre-event_circulating_supply remains a separate candidate and is NOT the first MVE.

## Discovery-era boundary

Candidate source universe: 2021-01-01 through 2024-12-31 only.

2025 is an untouched holdout and MUST NOT be read by this lab.
2026 is forbidden.

No price, return, PnL, profit factor, drawdown, regression against future returns, or forward outcome may be computed during Source/Data Gate.

## PIT authority rule

An event may enter the candidate manifest only if the exact schedule can be proven public at least 30 calendar days before the scheduled unlock timestamp.

Acceptable PIT evidence, strongest first:
1. immutable/on-chain vesting contract state deployed/committed before the cutoff;
2. official project tokenomics/whitepaper/governance/GitHub document with a verifiable publication/commit timestamp before the cutoff;
3. official project/foundation announcement timestamped before the cutoff;
4. archived provider snapshot with a verifiable as-of timestamp before the cutoff.

Current reconstructed aggregator pages are discovery aids only unless their historical version/as-of provenance is independently proven.

Required event fields:
- token identifier + chain/contract where applicable;
- scheduled unlock timestamp UTC;
- scheduled unlock amount in token units;
- cliff/discrete classification;
- primary source URL/identifier;
- primary source publication/deployment/commit timestamp;
- known_at_utc;
- evidence hash or immutable block/commit identifier when available;
- source class;
- PIT status.

## Source/Data Gate — hard pass conditions

Before any outcome authorization:
1. >= 40 eligible events across >= 15 distinct tokens;
2. events span >= 2 calendar years within 2021-2024;
3. 100% of included events have PASS PIT evidence under the 30-day rule;
4. exact unlock amount + timestamp are reproducible from source evidence;
5. no event selection uses return/price outcomes;
6. Binance historical data route exists for pre-event base-volume measurement; archive integrity route/checksum is available;
7. no 2025 or 2026 source/event rows are opened;
8. no returns/PnL/PF/hit-rate/future-price values are computed;
9. no current-survivor-only rule is introduced after outcomes;
10. source provenance and exclusions are receipted.

Allowed Source Gate terminal states:
- SOURCE_DATA_FEASIBLE
- SOURCE_PIT_PROVENANCE_INCOMPLETE
- SOURCE_AUTH_BLOCKED
- SOURCE_DATA_INADEQUATE
- TECHNICAL_FAILURE

## Candidate MVEs considered pre-outcome

A — TUE-CLIFF-ADV30-001 (SELECTED): large discrete cliff unlock normalized by pre-event 30D base-token trading volume. Best balance of mechanism, PIT denominator, falsifiability and operational simplicity.

B — TUE-CLIFF-FLOAT-001: unlock_tokens / PIT circulating_supply. Strong direct dilution metric but inherits the unresolved PIT circulating-supply source/access problem from SUPPLY-DILUTION-001.

C — TUE-INSIDER-001: team/investor-only unlocks. Economic story plausible but recipient categorization is subjective and recent external evidence is mixed. Not first.

D — TUE-ONCHAIN-DISTRIBUTION-001: post-unlock wallet/CEX distribution. More causal but materially more complex and a different hypothesis. Not first.

## Execution semantics deliberately unopened

Entry timestamp, pre-vs-post timing, holding horizon, benchmark, portfolio construction, liquidity floor, borrow/shortability rule, BASE cost, STRESS cost and promotion thresholds are NOT authorized yet. They may be frozen only after Source/Data Gate proves the event universe and available trading instruments without opening outcomes.

## Hard prohibitions

No switching to another MVE after seeing outcomes. No filtering bad tokens/events after outcomes. No sign inversion. No horizon rescue. No recipient-category rescue. No bull/bear rescue. No 2025/2026. No live orders, alerts, webhooks, exchange writes, Render deployment or merge to main.
