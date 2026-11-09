# Final preflight — 2026-11-06 (research only)

Status: **NO prospective session started (0/20)**. First future allowed window 2026-11-07 08:05:00–08:09:59 UTC (09:05–09:09:59 CET).

## Before operator starts
- Confirm the same validated Python environment and V3 commit, integrity/test suite PASS, working internet connection, UTC clock synchronized (observe timestamps explicitly).
- Choose a persistent single-writer output root for all sessions with sufficient disk space and backups. The current GitHub interaction has not verified any user's computer, clock, network or storage.
- Follow `MANUAL_FORWARD_RUNBOOK_2026-11-06.md`. The CLI is diagnostic only; prospective uses explicit `collect(...,mode='prospective')`.
- Run strictly within the frozen window; do not backfill, rerun rejected days, switch roots, or count the Nov 6 controlled 09:05 UTC diagnostic.
- Retain raw evidence, error attempts, manifest, SHA-256 and decision receipt. Until independent auditing and fee resolution, `net_pnl=null`; no trading.

## Unresolved support question (NOT SENT)
Official fee schedule: https://support.deribit.com/hc/en-us/articles/25944746248989-Fees
Official linear USDC options guide: https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options
Official support form: https://support.deribit.com/hc/en-us/requests/new

Subject: Clarification of expiry delivery fee for daily BTC_USDC linear options

Message:
Hello Deribit Support,
We are conducting non-trading research on BTC_USDC linear European options with next-day 08:00 UTC expiry (e.g. BTC_USDC-7NOV26-76000-C and -P). Your fee schedule lists BTC/ETH Daily Options at 0% delivery fee, but separately lists USDC Linear Options at 0.015% (capped at 12.5% of option value). The Linear USDC Options guide says an ITM option pays the usual delivery fee when it converts into an expiring futures contract.
Please confirm in writing which rule takes precedence specifically for BTC_USDC **daily** expiries; the exact effective fee formula/quantity units and cap, whether ATM/OTM contracts are charged, and whether the generated future incurs any additional fee. Is the answer the same for Saturdays, weekdays and Fridays, and effective on 6–7 November 2026?
We have not traded and do not need account-specific information. Thank you.

No support ticket was submitted and no private message/email was sent. This text is for operator review and submission only.
