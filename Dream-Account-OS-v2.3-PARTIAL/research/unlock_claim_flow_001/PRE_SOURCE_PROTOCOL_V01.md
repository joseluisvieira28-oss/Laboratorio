# UNLOCK-CLAIM-FLOW-001 — PRE-SOURCE PROTOCOL V0.1

LAB_ID: `UNLOCK-CLAIM-FLOW-001`
MVE_ID: `UCF-VESTING-OUTFLOW-24H-001`
BRANCH: `unlock-claim-flow-001-source-gate-v01`
POSTURE: RESEARCH ONLY / FAIL CLOSED / NO LIVE TRADING

## 1. Anti-duplication and independence

This is a new mechanism, not a rescue of `TOKEN-UNLOCK-EVENT-001 / TUE-CLIFF-ADV30-001`.

The exact prior MVE remains closed under its official `NO_EDGE` verdict. Its pressure threshold, outcome behavior, alternative horizons and post-outcome information are forbidden inputs to the design or qualification of this MVE.

This lab is also distinct from `STABLECOIN-EXCHANGE-FLOW-001`, which tested generic USDT net flow into a prospectively frozen Binance address basket and is closed `NO_STATISTICAL_EDGE`.

This MVE asks a different causal question:

> After a scheduled unlock has become claimable, does the fraction of that scheduled supply that actually leaves prospectively defensible vesting/distributor wallets within 24 hours predict weaker subsequent token performance?

The mechanism was explicitly reserved before the prior unlock outcomes as a separate future hypothesis: scheduled unlock is not the same information as actual post-unlock distribution.

## 2. Economic mechanism frozen before outcomes

A scheduled unlock only makes supply available. Actual circulating/sellable pressure depends on whether beneficiaries or distribution contracts move the unlocked tokens.

Primary signal:

`claim_ratio_24h = net_attributable_outflow_24h / scheduled_unlock_tokens`

where:
- `scheduled_unlock_tokens` is the PIT-qualified scheduled amount for the event;
- `net_attributable_outflow_24h` is token outflow from the prequalified source-wallet set to addresses outside that source set during `[unlock_timestamp, unlock_timestamp + 24h)`, minus token inflow from outside the source set during the same window;
- transfers between addresses inside the same qualified source-wallet set are internal and contribute zero;
- values are not clipped at 0 or 1. Ratios above 1 or below 0 are retained and flagged, not silently removed after seeing market outcomes.

Frozen expected direction:

`higher claim_ratio_24h -> weaker subsequent BTC-adjusted token return`

No inverse rescue is allowed if the observed sign is opposite.

## 3. Event universe

The starting event population is restricted to 2023–2024 PIT-qualified discrete unlock events already established in the pre-outcome source corpus inherited from commit `58bc91d8b83ddb1a0d0b6fae5cfd32279d46c15d`.

Only event identity, token identity, unlock timestamp, scheduled amount, allocation/source metadata and source provenance may be reused. The prior unlock-pressure signal, threshold calibration, forward outcomes and Discovery artifacts are not scientific inputs to this lab.

2025 and 2026 event/outcome rows remain locked and forbidden.

Initial technical scope is EVM-compatible token transfers only. A chain may enter only if historical logs/state can be retrieved reproducibly for the required source window without opening 2025/2026.

## 4. Source-wallet provenance hierarchy

A source wallet/contract is eligible only when its vesting/distribution role can be proven independently of later market outcomes.

Priority A — strongest:
- immutable vesting/distributor contract deployed before the event;
- verified source code or immutable bytecode semantics proving vesting/distribution function;
- deployment/constructor/factory/event evidence binding beneficiary/allocation/token and dates where applicable.

Priority B:
- official project/foundation/governance documentation published before the event naming the exact wallet/contract or an objectively derivable factory/deployment route.

Priority C:
- archived historical public source snapshot created before the event and containing the exact address plus vesting role.

Forbidden as final evidence:
- current exchange/entity labels learned after the event;
- present-day Tokenomist/Arkham/Nansen heuristic labels without historical PIT proof;
- addresses selected because their later transfers looked predictive;
- addresses inferred from post-outcome price behavior.

Current third-party claim products may be used only as discovery aids unless their event-level address provenance independently satisfies A/B/C.

## 5. Attribution rules

For each event, the source-wallet set must be frozen before any market outcome is opened.

An event is excluded fail-closed if:
- no qualifying source wallet can be tied to the relevant allocation/scheduled tranche;
- a source wallet mixes unrelated token distributions such that the event-specific numerator cannot be defended prospectively;
- token identity or chain identity is ambiguous;
- required historical Transfer-log/state coverage is incomplete;
- timestamp precision cannot support the 24h signal window.

Multiple allocations unlocking at the same timestamp for the same token may be aggregated only when their qualified source sets and scheduled amounts are all known prospectively. No event is split or merged based on subsequent returns.

## 6. Source/Data Gate — no outcomes

During Source/Data Gate it is forbidden to open:
- token prices;
- BTC prices;
- forward returns;
- PnL / profit factor;
- win rate;
- alternate horizons;
- 2025 or 2026 data.

The gate may inspect only schedule/provenance, contracts, addresses, token Transfer logs, timestamps, block metadata, and source transport integrity.

Hard PASS conditions:
1. >= 40 fully attributable event instances;
2. >= 8 distinct tokens;
3. both calendar years 2023 and 2024 represented;
4. 100% included events have PIT schedule proof and PIT-defensible source-wallet proof;
5. 100% included events have complete 24h on-chain source-flow coverage;
6. no token contributes >25% of eligible events;
7. no event/source selection uses market outcomes;
8. no 2025/2026 access;
9. reproducible hashes/commit/block identifiers persisted for provenance;
10. a prospective Binance market-data route exists for each eventual outcome token, but price values remain unopened until the Source Gate passes.

Allowed terminal classifications:
- `SOURCE_DATA_FEASIBLE`
- `SOURCE_WALLET_PROVENANCE_INCOMPLETE`
- `SOURCE_DATA_INADEQUATE`
- `SOURCE_AUTH_BLOCKED`
- `TECHNICAL_FAILURE`

## 7. Frozen Discovery definition — dormant until Source Gate PASS

If and only if Source/Data Gate = `SOURCE_DATA_FEASIBLE`, the following single outcome specification becomes eligible. It may not be modified after outcome inspection.

Signal closes: `T + 24h`.

Outcome entry: first Binance 1h candle open at or after `T + 24h + 15m`.

Outcome exit: exactly 48 hours after the selected entry timestamp.

Primary outcome:

`token_log_return_48h - BTC_log_return_48h`

Primary statistical test:
- continuous regression of BTC-adjusted 48h return on `claim_ratio_24h`;
- expected beta < 0;
- token-clustered robust inference;
- token-cluster bootstrap, 5,000 replications, fixed seed `240915`;
- Spearman rank association as predeclared secondary mechanism check.

No alternate signal window, holding horizon, benchmark, threshold, recipient subgroup, chain subgroup or inverse-direction rescue is authorized inside this MVE.

This first Discovery is a mechanism test, not an executable strategy. Trading costs/PnL cannot rescue or defeat the primary mechanism test because no trading rule is defined. If the mechanism survives, any executable strategy must be a new prospectively frozen MVE with its own untouched validation data and explicit cost model.

## 8. Promotion gates

`SURVIVES_DISCOVERY` requires all of the following:
- >= 30 outcome-resolved events after all predeclared availability filters;
- >= 8 tokens;
- both 2023 and 2024 represented;
- regression beta < 0;
- clustered 95% CI upper bound < 0;
- token-cluster bootstrap 95% CI upper bound < 0;
- Spearman correlation < 0;
- year-specific mean BTC-adjusted return among above-median claim-ratio events is non-positive in both 2023 and 2024;
- largest token share <=25%;
- all provenance/availability guards pass.

Otherwise the exact MVE closes under the appropriate scientific classification and is not rescued.

## 9. Governance locks

- 2025: LOCKED / FORBIDDEN.
- 2026: LOCKED / FORBIDDEN.
- no live trading;
- no exchange mutation;
- no merge to main;
- no Render deployment;
- no post-outcome tuning;
- no cherry-picking;
- no current-label hindsight repair;
- no use of prior TUE Discovery outcomes to select wallets, tokens, thresholds or horizons.

## 10. Immediate authorized action

Execute Source/Data Gate only:
1. enumerate eligible EVM events from the inherited PIT schedule corpus;
2. resolve source-wallet/contract provenance outcome-blind;
3. prove historical 24h Transfer-log/state transport;
4. build a source-only manifest and exclusions ledger;
5. apply the hard 40-event / 8-token / 2-year / 25%-concentration gate;
6. persist immutable receipts in GitHub and Google Drive.

Market outcomes remain closed until the source receipt proves `SOURCE_DATA_FEASIBLE`.
