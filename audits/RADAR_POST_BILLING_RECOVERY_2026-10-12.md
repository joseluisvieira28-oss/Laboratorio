# Radar post-billing recovery — 2026-10-12
Workspace confirmed: tea-daffqvgu01pc73a9sad0. Service: srv-dalqkpu1egvs73fhiehg.

## Verified
Render official events service_resumed evt-db6ak6n40ujc73d7p22g and suspender_removed evt-db6ak6n40ujc73d7p220 (Billing), 2026-10-12T09:36:26.966384Z. get_service now not_suspended / suspenders empty. No deploy, billing or infrastructure action by this task.
Original app logs from 09:46–09:48 show genuine checked_at advancing every 30 seconds, one instance ID srv-dalqkpu1egvs73fhiehg-hibernate-6b74b644f9-6jdj6, commit d645891a588c594b69f41938263cc4066652aa9b. Runtime chain verified 2737 events / 2659 keys; sequence 2737. This is original runtime proof, not independently replayed Postgres evidence.
Canonical watchdog PASS_CANONICAL_SUPABASE_SINGLE_WRITER. This validates this service's authority/configuration; it does NOT independently enumerate all potential external writers. No second writer was created or cut over. Existing local SQLite node is not promoted.
OPTIONS/BINANCE/ETF source statuses OK; ETF exact scheduler WAITING_EXACT_TARGET. All reviewed trading/account mutation flags false. Outcomes Q4 remain sealed.
Read-only public diagnostic run 38224423382 attempt 2 / job 114757650904 completed, with original monitor inspect only; no Telegram send.

## Health is NOT PASS
health=DEGRADED_FAIL_CLOSED; CED1D collector FAIL_CLOSED on exact original archive:
https://data.binance.vision/data/futures/um/daily/bookDepth/AVAXUSDT/AVAXUSDT-bookDepth-2026-10-08.zip
HTTP 404. Historical liveness gaps still require review (31 persisted receipts). Resumption does not repair missed source windows or prove continuous historical uptime.
Deployment SHA is older than current branch head; no automatic redeploy justified until scientific writer/risk/continuity preflight.

## Safe disposition
Transport/persistence resumed; overall operational health remains degraded by source and historical-continuity gates. Preserve missing bookDepth evidence; no alternate source/candle interpolation or retrospective execution fill. No real orders/accounts/wallets, paid resource, deploy, infrastructure change or main merge.
Next action: exact original archive availability/checksum source-only audit; global writer proof requires read-only enumeration and cannot be claimed solely from a watchdog label.
