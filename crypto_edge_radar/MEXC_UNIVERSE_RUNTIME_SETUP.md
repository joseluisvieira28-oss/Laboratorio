# MEXC Universe component — Crypto Edge Radar

Public/read-only integration of scout V0.1, based on `253910a644f9a1f8c0a83f4ebe9d30c2f55683f6`.
The inherited universe (20m USDT turnover, top 60) and strategy thresholds are preserved.
This is a dedicated canonical Radar component, not a live execution strategy.

## Runtime and source of truth
From `crypto_edge_radar`, use `python -m radar mexc-universe scan --run-id UNIQUE_ID`
(or the focused entrypoint `python -m radar.mexc_universe_runtime scan`).
`status` reads the current view and suppresses expired candidates; `notify` reports a committed run.
The existing ETF-CME shadow engine is independent. This module's `runtime/mexc_universe/status.json`
is the MEXC universe Radar state: `RADAR_EMPTY` or `TRADEABLE_CANDIDATE`.
Always inspect `source_health`: BLOCKED is a technical failure, not a clean empty-market result.

`runs/<run_id>.json` and `events/<run_id>.json` are exclusive-create append-only receipts.
`status.json` is a replaceable current view; `notifications.json` is the durable signal ledger.
Git history retains every state transition. The workflow commits receipts on the isolated integration
branch before sending. A failed push stops the notifier; artifacts are retained for diagnosis.
Do not remove the ledger, restore older state, force-push, or run parallel external writers.
Malformed state fails closed. Run IDs include the Actions run ID and attempt.

The public scanner requires current closed and contiguous 15m/1h candles, finite OHLCV,
and source timestamps within 60 seconds (maximum future skew five seconds).
Ticker/depth/funding timestamp absence, schema errors, or partial source failures suppress all candidates.
Each operational candidate expires 60 seconds after the source order-book timestamp. A delayed
workflow may therefore persist a candidate but suppress Telegram because it has expired.
The status reader prevents expired candidates appearing actionable.

Fees inherit V0.1's 8 bps/fill assumption, not an authenticated account fee verification.
Net RR inherits fees/spread/visible depth impact; future funding and future slippage are not measured.
The payload explicitly exposes these limitations. No execution or fill guarantee.

## Scheduler
Workflow: `.github/workflows/crypto-edge-radar-mexc-universe.yml`.
UTC cadence: minute 02, 17, 32, 47, every hour; two minutes after a 15m close.
Concurrency serializes all state writers. GitHub may delay scheduled runs; source freshness gates
still apply. Push validation is restricted to code/test/workflow paths, avoiding receipt-trigger loops.

GitHub runs cron schedules only from the default branch:
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
**This isolated branch has a configured schedule, but cron is NOT ON.** Activating the cron requires
separate authority to publish the workflow to the default branch, which this task forbids.
No main change, external scheduler, paid service, or self-dispatch loop is used to bypass that boundary.
The push-triggered integration run performs self-tests and a public scan on this branch.
`workflow_dispatch` availability also depends on GitHub registering the workflow on the default branch.
The workflow has `contents: write` solely for receipts on the isolated state branch.
If repository policy makes its GITHUB_TOKEN read-only, the receipt push fails and no message is sent.

## Optional Telegram
Operator supplies GitHub Actions repository secrets with these exact names:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

Set them under repository Settings > Secrets and variables > Actions. Do not place values in files,
issues, logs, or workflow inputs. The bot must have permission to send to the supplied chat.
Both values present enables the notifier automatically on subsequent runs; either absent gives
`DISABLED_MISSING_SECRETS` without failing the scanner. No credentials are generated or fetched.
The run receipt records only readiness, never values. NO_TRADE never sends a Telegram message.

Only new TRADE signal IDs are reserved. Identity is SHA256 of strategy version, symbol, side,
setup family, and closed 15m candle open timestamp; price changes do not create duplicate signals.
Reservations are durably committed before HTTPS POST to Telegram Bot API `sendMessage`:
https://core.telegram.org/bots/api#sendmessage
A successful response records SENT. An ambiguous/error response records UNKNOWN_NO_RETRY or
FAILED_NO_RETRY. A reservation left by a crashed process also suppresses future sends.
This provides at-most-one attempt across runs, favoring no duplicate over guaranteed delivery:
Telegram has no client idempotency key, so exactly-once delivery cannot be promised.
No raw HTTP exception/response bodies or token-containing URLs are logged; redirects are disabled.
A local invocation of `notify` requires the caller to persist reservations before invoking it;
the GitHub workflow enforces this order. Do not run local notification concurrently with Actions.

## Verification
`python -m unittest discover -s tests -p test_mexc_universe_runtime.py -v`
Tests use synthetic candles and mocked Telegram only. Integration receipts distinguish offline
validation from actual public-source runs and actual GitHub Actions notifier readiness.
No real orders, private exchange endpoints, accounts, wallets, exchange mutation, merge, or spending.
