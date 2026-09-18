# LOCAL OPERATOR NODE V0.12

Status: **PUBLIC SHADOW ONLY / NO CAPITAL / NO ORDERS**

V0.12 makes the Windows PC the redundant local shadow node for all five active/gated engines.

## Local runtime

- DH03 12H: dedicated Binance USD-M 1m/15m/mark-price collector.
- BNB Launchpool: official Binance CMS + BNBBTC public market binding, 30s loop.
- TFG Regime: MEXC Spot public watcher on new certifiable 12H boundaries.
- OPTIONS-SPOTPERP V2.1: Deribit public daily watcher and frozen forward metrics.
- ETF-CME EXEC-V2: hourly public Spot/Perp mapping and friction preflight.

The four non-DH03 engines share an isolated local forward evidence database and status file. DH03 remains isolated because its minute-path collector has different timing and reconciliation requirements.

## Local files

- data/forward_local_evidence.sqlite3
- data/forward_local_status.json
- data/forward_local_notifications.jsonl
- data/forward_local_supervisor_status.json
- DH03 market/evidence files under the existing CryptoEdgeRadar local-data path.

## Hard safety

- no API keys
- no authenticated exchange API
- no orders or POST trading endpoints
- no wallet access
- no live capital
- no automatic micro-live authorization
- all scientific forward gates remain unchanged

V0.12 improves observation redundancy and timing. It does not remove account-specific fee/state, execution-authority, forward-sample, or micro-live gates.
