# PAYER-FIRST 002 — Treasury Risk Watch (read-only offline proof)

**Status:** Scientific/technical POC only, not a paying product, monitoring service or trading system.

## Evidence
A historical **Base Aave V3 LiquidationCall** event publicly displayed in [BaseScan tx 0x6f4c472b...](https://basescan.org/tx/0x6f4c472b846a2d5530ece4596a39c5cb9f088f0ad2e3804f80f95c8b2289d40a) dated **2026-05-12 14:33:51 UTC**, block **45,903,542**, log shown as **#29**, with Aave Base pool 0xa238dd80c259a72e81d7e4664a9801593f98d1c5.

Expected ABI event `LiquidationCall(address collateralAsset,address debtAsset,address user,uint256 debtToCover,uint256 liquidatedCollateralAmount,address liquidator,bool receiveAToken)`; first three addresses indexed in topics. Official explorer-decoded values: 42,061.674725 USDC debt (6 decimals), 19.415285763088108751 WETH collateral (18 decimals), a known user/liquidator, `receiveAToken=false`. The fixture preserves the event topic and ABI data displayed by the explorer. The chain raw receipt was **not fetched independently** and this transcribed fixture is not proof of point-in-time ingestion; freeze SHA-256 is computed locally.

## Run offline (Python stdlib only)
`python3 -m unittest -v test_monitor.py`
`python3 monitor.py --threshold 40000`
Opens `demo.html` and generates `results.json`. To run threshold negative control: `python3 monitor.py --threshold 45000` (0 alerts).

## Enforced checks
* Exact Base chain ID, emitting Aave contract, LiquidationCall topic0, expected token addresses and decimal precision, successful transaction status, fixed four-word ABI data.
* Reject malformed addresses, invalid boolean, bogus event topic, wrong chain/token and negative threshold.
* De-duplicate event ID, deterministic threshold, include public transaction link and limitations.

## Not provided
* No API calls, no realtime polling or webhook, no wallets/transactions, no pending-position risk detection, no archive-wide ground truth, no false-positive/latency study, no confirmation/reorg reconciliation, no independent RPC proof, no market/payout/earnings evidence, no client consent or payments.
* A liquidation is retrospective and cannot serve as an early warning of a future liquidation. Tokens of unknown decimals fail closed.

## Next economic gate
Before any deployment or outreach: (1) compare against free/open-source alert tooling and Forta, (2) identify a customer-specific problem they cannot already solve, (3) obtain permission for pilot/outreach, (4) demonstrate two real paid pilots with net contribution after support/infra. If no differentiating workflow or buyer found, **NO-GO commercial**.
