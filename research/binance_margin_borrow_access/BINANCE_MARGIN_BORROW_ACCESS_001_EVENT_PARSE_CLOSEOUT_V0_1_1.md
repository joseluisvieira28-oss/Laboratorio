# BINANCE-MARGIN-BORROW-ACCESS-001 — EVENT PARSE CLOSEOUT V0.1.1

Date: 2026-09-17  
Branch: `binance-margin-borrow-access-v0.1`

## Scientific verdict

**EVENT_PARSE_PASS**

This is a source-only/outcome-blind parser verdict. It is not an economic edge verdict and does not authorize Discovery by itself.

## Canonical evidence basis

Strict parser run: `35262413846`.

All four V0.1.1 deterministic parser shards completed successfully and resolved the complete frozen 69-article schema universe:

- shard 0: 18/18, artifact `10515520834`, digest `sha256:0e126c73c5c92db36bc81dcfd2824e92ef8726a4814a56ab2134f3bfb9869efa`;
- shard 1: 17/17, artifact `10515825572`, digest `sha256:8ea9c375882037198ed195a08d9063a99d2c036be4beb38ef87f0297a5a26a4c`;
- shard 2: 17/17, artifact `10514604287`, digest `sha256:c1756a174d8ad9ff47774695bc21fb6e6d686da2954d2626c6af94058219ea7e`;
- shard 3: 17/17, artifact `10515596133`, digest `sha256:7967406472c5eaeaf0d820b98befb6cc47cf78a4f3a104919299c16e719c608c`.

An independent deterministic aggregation of those four immutable JSON receipts using the frozen V0.1.1 aggregation invariants produced:

- resolved articles: 69/69;
- `ADD`: 54;
- `REMOVE`: 6;
- `OTHER`: 9;
- exact retained ADD asset mentions: 100;
- invalid retained ADD records: 0;
- duplicate/missing article identities: 0.

The nine non-ADD records consist of seven `NO_EXPLICIT_CROSS_BORROW_CLAUSE`, one `DIFFERENT_MECHANISM`, and one `ASSET_LIST_OPEN_ENDED` exclusion.

## Operational aggregate exception

The aggregate job of run `35262413846` failed before reading the shard data because its environment omitted the `requests` dependency imported transitively by the parser module. The job log records `ModuleNotFoundError: No module named 'requests'`.

This was an aggregation-environment defect, not a source/parser/reconciliation failure. The workflow was corrected in commit `5b4bcf0a0c2ac392cf329444543dca175e7b3320`; confirmation run `35262879137` was launched. No scientific rule or parsed record was changed by that operational correction.

## Safety

No market prices, returns, basis, abnormal returns, borrow rates, borrow inventory, authenticated exchange/account data, PnL, win rate, PF, drawdown, orders, wallets, alerts/webhooks, exchange mutation or live trading were opened in the parser evidence.

## Next permitted phase

The clean 54-event ADD universe may proceed to the frozen prior-Spot provenance gate. Each retained asset occurrence must obtain point-in-time proof that Binance Spot trading existed strictly before its borrow-access event-information time. Failure is fail-closed. Discovery remains forbidden until event-source adjudication is complete.