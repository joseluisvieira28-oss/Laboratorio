# CRYPTO LAB — EMPTY TERRITORY HUNT V1 — CAMPAIGN REPORT

Date: 2026-09-17  
Repository: `joseluisvieira28-oss/Laboratorio`  
Branch: `empty-territory-hunt-v0.1`  
Governance: research-only / fail-closed / outcome-blind until source pass

## Executive conclusion

The laboratory is not short of branches; it is short of materially independent economic mechanisms with reproducible point-in-time sources.

After collapsing remediation branches, threshold/timeframe variants and superseded implementations into their underlying mechanisms, the highest marginal-value frontier is concentrated in:

1. economically anchored redemption/convergence;
2. latent DeFi liquidation inventory rather than observed liquidation events;
3. structural short-sale access changes;
4. order-book liquidity resilience/replenishment rather than raw flow imbalance.

Four candidates survive the severe novelty filter. None is called an edge. One was selected for an immediate source gate: `STETH-REDEMPTION-BASIS-001`. Its public-RPC source gate terminated as `SOURCE_ACQUISITION_TECHNICAL_FAILURE` with zero outcomes opened.

## 1. Territory map

| Family | Coverage | Current classification | Marginal-value view |
|---|---|---|---|
| TREND | High / over-covered | SATURATED / STONE-HEAVY | Stop generating timeframe/indicator variants. |
| MR | Medium | MODERATELY COVERED; anchored MR still UNDER-EXPLORED | Only mechanisms with explicit equilibrium/redemption anchor deserve new work. |
| CARRY | Medium | GENERIC IMPLEMENTATIONS SATURATED / some SOURCE-BLOCKED | Funding/basis threshold variants have low value. |
| RV | Medium-high | MODERATELY COVERED / COST-FRAGILE | Only new cash-flow or access constraints justify expansion. |
| EVENT | High | HIGH COVERAGE / SOURCE-HEAVY | Headline-only event studies are low marginal value; true surprise/access changes remain useful. |
| MICRO | Medium | UNDER-EXPLORED but SOURCE-LIMITED | Forced flow and liquidity-state mechanics remain attractive; raw imbalance does not. |
| LEADLAG | Medium-high | GENERIC FORM SATURATED / some DATA_FAILURE | Do not create more BTC-alt timing variants. |
| VOL | Low-medium | UNDER-EXPLORED / POSITIVE EVIDENCE EXISTS / EXECUTION-SOURCE LIMITED | VRP existence is established internally; new work must solve executable structure or materially new vol economics. |
| FLOW | Medium-high | MIXED / GENERIC RAW FLOW SATURATED | Predictive state variables may remain, but contemporaneous taker-flow confirmation is not enough. |
| SUPPLY | Medium | SAMPLE-CONSTRAINED | Structural unlock/migration tests remain event-limited. |
| MACRO | Medium-high | EXPECTATIONS LAYER UNDER-EXPLORED / SOURCE-PROVENANCE SENSITIVE | `actual vs point-in-time consensus + rates reaction` is already an active/recently identified frontier, not a new Empty Territory candidate. |
| CREDIT | Low | UNDER-EXPLORED / SOURCE-BLOCKED | Best empty territory is borrower-level liquidation eligibility and contagion, not another borrow-rate threshold. |
| ACCESS | Medium | ACTIVE FRONTIER | New shorting/collateral/trading access mechanisms can be independent if event identity is clean. |

## 2. Saturated / do-not-clone mechanisms

The campaign rejects as low marginal value:

- Donchian/breakout/trend timeframe variants;
- RSI/EMA/VWAP/ADX indicator mutations;
- raw funding-rate thresholds;
- raw open-interest/taker-imbalance thresholds;
- generic spot/perp cash-and-carry fee rescues;
- generic BTC-to-alt lead-lag variants;
- headline-only CPI/NFP direction;
- direct replay of actual DeFi liquidation shock definitions;
- direct replay of stablecoin USDCUSDT peg-cross definitions;
- additional options skew/risk-reversal discovery under a new name;
- additional DVOL term-structure discovery under a new name.

## 3. Surviving hypotheses

### H1 — STETH-REDEMPTION-BASIS-001

- EDGE FAMILY: MR / RV
- MECHANISM: executable secondary-market stETH discount versus explicit Lido protocol redemption value.
- ECONOMIC COUNTERPARTY: stETH holders paying for immediate ETH liquidity instead of waiting through the asynchronous withdrawal queue and bearing queue/protocol risk.
- EXPECTED PAYOFF SHAPE: convergence / cash-flow arbitrage; no ETH directional forecast.
- PREDICTOR: point-in-time executable Curve 10 ETH -> stETH quote minus expected Lido claim, queue opportunity cost, gas and frozen risk reserve.
- OUTCOME: realized net ETH from buy stETH -> request Lido withdrawal -> claim ETH.
- HORIZON: endogenous queue finalization time, hard-capped at 14 calendar days under V0.1.
- DATA SOURCE: Ethereum mainnet Lido + Curve contracts/events via archival RPC.
- HISTORICAL COVERAGE: 2023-05-15 through 2024-12-31 only.
- EXECUTION MODEL: fixed 10 ETH notional, Curve legacy ETH/stETH pool, Lido WithdrawalQueue, one position at a time, no leverage.
- COST MODEL: Curve deterministic quote plus 2 bps fill haircut; 800k gas at 1.25x block base fee; foregone stETH rewards; 10 bps protocol-risk reserve. Stress = 5 bps fill haircut, 1.5x gas, 25 bps risk reserve.
- MAIN FAILURE MODE: secondary discount is too small/rare after queue opportunity cost and gas; source route can also fail historical-state requirements.
- NEAREST EXISTING LAB: `ETH-STAKING-FLOW-001`; `STABLECOIN-PEG-DISLOCATION-001`.
- MATERIAL DIFFERENCE: explicit asset-specific redemption cash flow, not validator entry/exit pressure and not fiat peg reversion.
- SOURCE FEASIBILITY: economically/source-defined, but current public archival transport failed the frozen gate. Status = HIGH-INTEREST / SOURCE-BLOCKED.
- EXPECTED SAMPLE: 597 daily source snapshots; promotion requires >=30 completed non-overlapping hypothetical redemptions.

### H2 — AAVE-LIQUIDATION-OVERHANG-001

- EDGE FAMILY: CREDIT / MICRO
- MECHANISM: latent forced-sale inventory implied by borrower-level collateral positions near liquidation eligibility, measured before actual liquidation occurs.
- ECONOMIC COUNTERPARTY: leveraged Aave borrowers close to HF=1; liquidators are economically incentivized to repay debt and seize collateral when the threshold is crossed; market makers must absorb collateral/hedging flow.
- EXPECTED SIGN / PAYOFF SHAPE: higher ex-ante liquidation overhang should increase subsequent liquidation notional and downside-tail/volatility pressure in the directly exposed collateral asset.
- PREDICTOR: borrower-level collateral/debt state converted into a continuous liquidation-distance/eligible-collateral curve using point-in-time Aave reserve parameters and oracle prices. A minimal fixed adverse-shock definition must be frozen before Discovery; no threshold sweep.
- OUTCOME: primary mechanism validation = next-period canonical Aave liquidation notional; a later execution layer may test ETH downside-tail/perp returns only after its own costs/timing are frozen.
- HORIZON: provisional 24h mechanism horizon, to be frozen before outcome access.
- DATA SOURCE: Aave V3 Ethereum Pool events/UserReserve/Reserve state, reserve parameters and point-in-time oracle prices; official Aave subgraph supports historical block queries, with direct-chain reconstruction as provenance fallback.
- HISTORICAL COVERAGE: V3 Ethereum history through 2024, with 2025/2026 locked.
- EXECUTION MODEL: not yet authorized; if promoted beyond mechanism validation, ETH perp/spot execution must be frozen separately.
- COST MODEL: none for liquidation-notional mechanism validation; any directional trade layer must freeze conservative round-trip fees/slippage/funding before outcomes.
- MAIN FAILURE MODE: borrowers self-deleverage before eligibility; health factor is endogenous to the same price move being forecast; collateral mix/correlation and oracle mechanics can make aggregate overhang misleading.
- NEAREST EXISTING LAB: `AAVE-CREDIT-STRESS-001`; `DEFI-LIQUIDATION-SHOCK-001`.
- MATERIAL DIFFERENCE: borrower-level latent liquidation inventory before forced flow, not USDC variableBorrowRate and not realized liquidation events.
- SOURCE FEASIBILITY: MEDIUM-HIGH technically, MEDIUM operationally; historical block queries are documented, but large user-state reconstruction and endpoint/provenance must pass a dedicated source census.
- EXPECTED SAMPLE: roughly 900-1,000 daily state snapshots over a 2022-2024 design; effective high-overhang event count unknown until source-only census.

### H3 — BINANCE-MARGIN-BORROW-ACCESS-001

- EDGE FAMILY: ACCESS
- MECHANISM: relaxation of the short-sale/hedging constraint when an already spot-listed asset becomes newly borrowable on Binance Cross Margin.
- ECONOMIC COUNTERPARTY: holders/long-biased participants facing newly enabled borrowers, short sellers, basis arbitrageurs and hedgers.
- EXPECTED SIGN / PAYOFF SHAPE: newly enabled borrowing should reduce a pre-existing short-sale constraint; provisional expected effect is negative abnormal pressure and/or compression of positive spot premia after access becomes effective.
- PREDICTOR: official timestamped Binance announcement that explicitly adds an asset as borrowable on Cross Margin, restricted to assets already spot-listed before the event.
- OUTCOME: cross-sectional residual return and/or spot-perp basis change after the access event; exact horizon must be frozen before Discovery.
- HORIZON: provisional 24h primary, 72h diagnostic only; not yet authorized.
- DATA SOURCE: Binance official announcements for event identity/time; Binance market archive for prices; historical margin interest-rate endpoint for borrow costs.
- HISTORICAL COVERAGE: many documented 2023 events and expected additional 2024 coverage; 2025/2026 excluded.
- EXECUTION MODEL: borrow asset on Cross Margin, sell spot after effective access, cover at frozen horizon; no event qualifies if same-day spot listing/perp launch creates an inseparable access confound.
- COST MODEL: spot round-trip fees/slippage plus actual point-in-time borrow interest; the historical margin interest-rate endpoint is signed `USER_DATA`, so cost reconstruction is currently credential-bound.
- MAIN FAILURE MODE: borrow inventory may be scarce at launch; announcement/effective time may differ; events can be bundled with new pairs/listings; borrow cost may erase the effect.
- NEAREST EXISTING LAB: `PERPETUAL-LAUNCH-SHOCK`; MSEL / access-event programs.
- MATERIAL DIFFERENCE: changes the ability to create short inventory in an already traded asset, rather than opening the asset/perpetual market itself.
- SOURCE FEASIBILITY: event census HIGH; fully executable cost source MEDIUM/credential-bound.
- EXPECTED SAMPLE: dozens of candidate asset-events across 2023-2024, exact independent census required before freezing Discovery.

### H4 — ORDERBOOK-RESILIENCE-001

- EDGE FAMILY: MICRO
- MECHANISM: liquidity-provider replenishment after a local aggressive-flow/depth shock. The state variable is how quickly near-market depth returns, not raw taker direction.
- ECONOMIC COUNTERPARTY: aggressive takers versus market makers/liquidity providers managing inventory and adverse-selection risk.
- EXPECTED SIGN / PAYOFF SHAPE: persistent depth depletion / slow refill after a one-sided shock should imply greater impact persistence; rapid refill should imply absorption/reversion.
- PREDICTOR: frozen pre-event depth baseline and post-shock refill ratio/half-life computed only from already-observed order-book snapshots; any shock definition must be frozen before outcome access.
- OUTCOME: short-horizon signed impact continuation/reversion and realized impact conditional on refill state.
- HORIZON: candidate 5m primary; exact event clock not yet authorized.
- DATA SOURCE: Binance USD-M Futures public `bookDepth` daily archive plus canonical aggTrades/mark/price data.
- HISTORICAL COVERAGE: evidence indicates BTCUSDT `bookDepth` archive starts around 2023-01-01; 2023-2024 is the natural protected-safe source period.
- EXECUTION MODEL: BTCUSDT perpetual after the refill state is observable; no sub-snapshot latency claim.
- COST MODEL: standard perp round-trip fees plus measured/explicit slippage; must be frozen before Discovery.
- MAIN FAILURE MODE: public `bookDepth` appears sampled at roughly 30 seconds and uses aggregated percentage-depth bands rather than a full reconstructable L2 book; archive semantics/data-quality issues may make true refill half-life unidentifiable.
- NEAREST EXISTING LAB: generic taker/OI flow studies and `DEFI-LIQUIDATION-SHOCK-001`.
- MATERIAL DIFFERENCE: market-maker liquidity replenishment/capacity is the causal state, not order-flow sign, OI level or liquidation-event identity.
- SOURCE FEASIBILITY: MEDIUM. Public source exists; exact schema/frequency/provenance must pass before this can become P1.
- EXPECTED SAMPLE: about 731 protected-safe daily files for 2023-2024 and order-of-millions of 30s depth observations for BTCUSDT; independent shock count unknown until source-only census.

## 4. Severe novelty rejections

Rejected from this campaign:

- OPTIONS SKEW / 25D RISK REVERSAL: already formalized under `OPTIONS-SPOTPERP-001`; duplicate.
- BTC OPTIONS VRP variant: positive historical VRP already established under the existing frozen definition; new threshold/horizon is not new territory.
- DVOL / options term structure: already has an existing source/term-structure lineage; not new.
- MACRO SURPRISE DIRECTION: already explicitly identified as `actual vs point-in-time consensus`, yields/rates reaction and flow confirmation; not new.
- DERIBIT LIQUIDATION IMPACT DECAY: same forced-deleveraging economic participant/mechanism as existing historical/deFi liquidation research; source change alone does not pass novelty.
- BINANCE COLLATERAL-HAIRCUT FORCED DELEVERAGING: economics are interesting but protected-safe pre-2025 independent downward-haircut event batches appear too sparse for a robust first lab.
- STABLECOIN PEG variants: direct lineage already exists; changing stablecoin/threshold/horizon would be a mutation, not new mechanism.

## 5. Priority attack map

Priority is research information value, not expected profitability.

### P1 — HIGH INFORMATION VALUE

**AAVE-LIQUIDATION-OVERHANG-001**

Reason: genuinely new credit state, direct forced-flow mechanism, borrower-level point-in-time data model, large potential source sample. Needs source census before any outcome.

### P1-BLOCKED — HIGH-INTEREST RESEARCH TARGET

**STETH-REDEMPTION-BASIS-001**

Reason: strongest explicit cash-flow/equilibrium anchor and execution math, but the first frozen Source Gate could not obtain a public archival transport that reproduced all required historical receipts/state calls. Do not weaken the gate to rescue it.

### P2 — WORTH TESTING

**ORDERBOOK-RESILIENCE-001**

Reason: materially independent microstructure mechanism and public archive, but the source may be too coarsely sampled/aggregated to identify replenishment rigorously.

**BINANCE-MARGIN-BORROW-ACCESS-001**

Reason: clean structural access mechanism and point-in-time official announcements; exact executable borrow-cost reconstruction is credential-bound and event confounding must be controlled prospectively.

## 6. First lab selected and executed at Source Gate

Selected: `STETH-REDEMPTION-BASIS-001`.

Why selected before the source result:
- explicit economic counterparty and cash-flow anchor;
- predictor observable before outcome;
- fixed execution path rather than directional forecasting;
- no overlap with existing ETH validator-queue signal;
- 597 protected-safe daily source snapshots available in principle;
- costs can be expressed directly in ETH.

Frozen before source execution:
- 2023-05-15 through 2024-12-31;
- 12:00 UTC daily snapshot;
- 10 ETH notional;
- Curve legacy ETH/stETH only;
- Lido WithdrawalQueue only;
- 14-day max queue wait;
- 2 bps base / 5 bps stress quote-to-fill haircut;
- 800k gas at 1.25x baseFee, 1.5x stress gas;
- foregone rewards from trailing point-in-time rebase history;
- 10 bps base / 25 bps stress protocol-risk reserve;
- one position at a time;
- exit only by Lido claim;
- >=30 completed non-overlapping redemptions and frozen promotion gates;
- 2025/2026 locked.

Source Gate result: `SOURCE_ACQUISITION_TECHNICAL_FAILURE` after initial 3-route probe and a 7-route transport-only remediation. No source-rule or economic-rule rescue was made.

## 7. Safety / outcome receipt

During this campaign:
- no live trading;
- no orders;
- no exchange mutation;
- no wallet use;
- no execution webhooks;
- no merge to `main`;
- no protected holdout opened;
- no future prices/returns/PnL opened for the selected lab;
- no post-outcome parameter selection occurred.

## 8. Recommended next research action

Because `STETH-REDEMPTION-BASIS-001` is source-blocked rather than economically rejected, do not weaken its source gate.

Next highest-information source-only attack should be `AAVE-LIQUIDATION-OVERHANG-001` with a strict borrower-state census/provenance gate. `ORDERBOOK-RESILIENCE-001` should run a schema/frequency/data-quality probe in parallel only if governance permits multiple source-only fronts; it should not open outcomes until its own definitions are frozen.
