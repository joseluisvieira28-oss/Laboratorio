# COMPOUND-REALIZED-DISPOSAL-FLOW-001 — SOURCE / MECHANISM FREEZE V0.1

Date: 2026-09-27
Status: FROZEN_SOURCE_FIRST / MARKET OUTCOMES LOCKED
Primary family: CREDIT
Secondary family: MICRO / FLOW

## 1. Frozen question

Can Compound III's realized seized-collateral disposal flow be reconstructed reproducibly from public on-chain evidence, including enough transaction-path information to distinguish a protocol sale from a mere residual inventory state?

This is a source/mechanism question only.

## 2. Source authority

Canonical market for V0.1 source diagnostics:
Ethereum mainnet / Compound III USDC Comet
`0xc3d688B66703497DAA19211EEdff47f25384cdc3`.

Primary public source:
Blockscout indexed Ethereum logs plus Ethereum JSON-RPC transaction/receipt reads.

Official protocol semantics:
- underwater collateral is absorbed onto protocol accounts;
- `BuyCollateral` buys protocol collateral using base token and increases reserves;
- Compound's public Comet repository includes a liquidator implementation that can absorb, purchase collateral and attempt an external sale.

## 3. Frozen historical source corpus

2023-01-01 through 2024-12-31 only for the transaction-path diagnostic.

Known source canary from the already validated parent census:
- expected `BuyCollateral` logs: 999;
- event signature: `BuyCollateral(address,address,uint256,uint256)`.

No market price endpoint is permitted.

## 4. Frozen fields

For every BuyCollateral log:
- block number;
- transaction index;
- log index;
- transaction hash;
- buyer from indexed topic 1;
- collateral asset from indexed topic 2;
- baseAmount from event data word 0;
- collateralAmount from event data word 1.

Corpus-level diagnostics:
- unique transactions;
- unique buyers;
- unique assets;
- buyer concentration;
- per-asset counts.

## 5. Deterministic receipt probe

To avoid outcome-driven sampling, choose up to 64 unique BuyCollateral transaction hashes by:
1. lowercase transaction hash;
2. SHA-256 of that string;
3. ascending SHA-256 order;
4. first 64.

For each selected transaction:
- fetch transaction and receipt;
- require successful receipt retrieval;
- match its BuyCollateral logs;
- infer a recipient only from a collateral-token `Transfer` log with:
  - token address = BuyCollateral asset;
  - from = Comet;
  - amount = BuyCollateral collateralAmount;
  - nearest qualifying transfer before the BuyCollateral log in the same receipt;
- after the BuyCollateral log, inspect whether the same collateral token has a `Transfer` whose from address equals the inferred recipient.

The latter is a source-only **same-transaction onward-transfer diagnostic**.
It is not automatically a DEX sale and earns zero edge credit.

## 6. Source PASS gates

`SOURCE_REALIZED_FLOW_PASS` requires all:
1. exactly 999 historical BuyCollateral logs, matching the validated parent canary;
2. >=1 unique buyer and >=1 unique asset;
3. deterministic receipt sample size = 64 unless fewer than 64 unique transactions exist;
4. >=95% selected transactions return usable transaction + receipt evidence;
5. >=90% probed BuyCollateral events permit recipient inference under the frozen exact-amount transfer rule.

If gate 1 fails: `SOURCE_CORPUS_DRIFT`.
If gates 2–5 fail: `SOURCE_REALIZED_FLOW_PARTIAL`.

The onward-transfer rate has **no pass threshold** and cannot rescue or kill the source gate by itself.

## 7. Mechanism adjudication after source receipt

After the source run, a separate source-only adjudication may decide whether the direct realized-flow mechanism is strong enough to justify an economic freeze.

No price return, direction, holding period or PnL may be selected from market outcomes.

## 8. Protected evidence firewall

2025+ market outcomes remain unopened.
2023–2024 sibling market outcomes carry zero credit.
No Binance price archive, CEX API, return, funding, basis, volatility or PnL endpoint is permitted in this source run.

## 9. Operational firewall

market_prices_opened=false
returns_computed=false
pnl_computed=false
protected_2025_market_outcomes_opened=false
live_trading=false
orders=false
exchange_mutation=false
capital=false
paid_data=false
main_merge=false
post_outcome_tuning=false
