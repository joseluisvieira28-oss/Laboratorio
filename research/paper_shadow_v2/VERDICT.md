# Paper Shadow Economic V2 — verdict 2026-11-04

**SOURCE_BLOCKED / ECONOMIC_INSUFFICIENT_SAMPLE / NO_LIVE_GO**.

Independent protocol frozen locally at d675c03 before the single new public capture; implementation at 99a27ad before capture. GitHub publication followed the capture, via the authorized connector because local git push returned 403 for a different cached identity. No successful local push and no main changes. Draft PR #335 is stacked on #334. #333 and prior protocols unchanged.

## Real pilot
180.234 seconds wall runtime; 179.453 seconds between first and last receipt. 5,490 total receipt rows. Bybit: 3,895 valid level-one snapshots, 3,394 executed trade children, ZERO liquidation children. MEXC: 230 valid full five-level snapshots in corrected replay; public contract detail certifies 0.0001 BTC per contract. ONE MEXC close code 1005; no retry or replacement session. No guaranteed liquidation census or uninterrupted joint source window.

ZERO qualifying decisions, ZERO simulated entries, ZERO completed returns. PnL, win rate and mean return are NOT assessed. This is not NO_EDGE: the required economic sample does not exist. The 60-completion / 14-date gate is unsatisfied. A short public pilot cannot establish profitability.

Original parser failed on all 230 MEXC depth frames because it expected data.timestamp instead of envelope ts. Original report.json retained, with 230 original parser errors plus transport closure. Corrected audit.json replays identical raw bytes in original receive order, with no new capture, no strategy/cost/threshold changes. Corrected source still SOURCE_BLOCKED due to the actual transport closure and absent liquidation observations. Parser correction is technical repair, not an economic result.

Raw SHA256: eb86dd41c9bdb87c84c66c8206dcb102139b5da3e38ea7ef58765add5e93f7e3
Protocol exact-byte SHA256: 2cce05580fd311c03e2953dfd8d0b87768868933c34df92df47867db4c173073
Raw bytes are losslessly retained as pilot-20261104/raw.jsonl.gz. audit.py extracts them if necessary and verifies the original raw SHA before replay. Original report and corrected audit are separate receipts. sampling.json records transport gaps/errors.

## Implementation and validation
Receive-order detector; bounded source timestamps; duplicate suppression; immediate quarantine/reset; one exposure and cooldown; delayed new-snapshot entry/exit; fixed BTC quantity rounded down to whole contracts; depth sweep limited to 10% displayed contracts; adverse spread/slippage and two-leg BASE/STRESS fees; failed entries and unresolved exits retained. Economic gate includes daily cluster bootstrap and never permits live-go. Fees/slippage and fill availability remain modeling assumptions; real account fees, queue priority, hidden liquidity, network order latency and actual fills are not certified. No funding-boundary entries.

21 offline adversarial tests plus 143 inherited PAPER tests pass locally on Windows. Initial remote CI on 26ebf8f passed the then-current 20 shadow tests and 143 inherited tests on Ubuntu and Windows. Final receipt/code CI status is recorded in the PR, separately from the economic verdict. Original floating-point equality assertion failure was corrected to a tolerance; whole-contract sizing exposed an invalid oversized synthetic contract fixture, repaired without relaxing economic rules.

This remains a standalone observer/replayer, not wired to arm #334's mock executor. No orders, keys, accounts, private endpoint, scheduler, protected holdout or main merge. No further capture under this authority. A multi-day study would require separately frozen bounded collection authority and a repaired transport path.

Reproduce offline: python -m unittest discover -s research/paper_shadow_v2 -v ; python research/paper_shadow_v2/audit.py
Capture dependency only: websockets==15.0.1. Offline replay/tests use standard library only.
