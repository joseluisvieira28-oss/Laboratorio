# Crypto Lab — Telegram private alert reconnection and cost guard V0.1
2026-10-10 | OPERATOR HANDOFF | STATUS: CODE_READY / NOT_CONNECTED_UNTIL_SECRET_PREFLIGHT_AND_REAL_SEND / NO_NEW_LIVE_AUTHORITY

## Identity and purpose
- Previously selected channel: private **Crypto Lab Fishing Bot** delivering to **Crypto Lab - Fishing Room**. The existing chat destination is NOT hard-coded to the repository, workflow or tests.
- This is **outbound notifications only**, through Telegram Bot API `sendMessage`. The bot cannot send an authenticated command to the Radar or the exchange. No `getUpdates`, webhooks, admin buttons, remote execution or chat-to-order conversion.
- Scientific research remains source-first and frozen. Telegram delivery, receipt or runtime uptime creates **zero additional scientific credit**.
- The only inspected runtime is the existing canonical **Render PUBLIC_SHADOW_ONLY**, not Windows MEXC Trading Supervisor. MEXC account/positions/fees/TP-SL remain independent and unverified.

## Cost-neutral wiring
- Reuse existing `.github/workflows/radar-v09-keepalive.yml` with the existing `*/8 * * * *` cron. **No additional scheduled workflow or paid service**. No pushes trigger a new production keepalive. Only `workflow_dispatch` manual probes.
- Replace two retrying 90-second cURL attempts (observed cancelled 2026-10-10 09:03) with one bounded `/api/state` read (105 seconds). The 503 response is parsed to preserve source-failure information.
- A new standard-library-only Python notifier sends a bounded plain-text, incident-code-only Telegram message; no external paid SDK or service. Token read only from Actions secret in the send step. The token is never printed, stored in source, included in file output or passed to Radar.
- An `actions/cache` artifact suppresses repeated notices for a **same UTC-day + same reason set** after successful `sendMessage`. This is best effort, **not exactly once** (cache eviction, races, cron scheduling can duplicate or delay).
- On a normal healthy probe there is no Telegram message. On degraded state the workflow attempts an alert, then fails itself to preserve operational visibility. If secrets are absent it cannot send and logs `TELEGRAM_DELIVERY_NOT_CONFIGURED`.
- Dispatch `telegram_test=true` sends one private harmless connectivity test; the smoke test **fails if either secret is missing**.
- Github Actions schedules may be late or skipped; these pings **do not prove 24/7 trading or source continuity**. Render Free spins down after ~15 minutes idle and has shared monthly quotas. Telegram reduces notification cost, **not compute, exchange fees, missed data, or broker risk**.

## Safety and observable blockers
- Freshness > 20m, wrong canonical service ID, invalid JSON/mode, missing shadow flags, failed `CED1D`, unresolved history or failed source => `DEGRADED` to notifier. Alerts carry no raw user data, account data, trading instruction, symbol/side/price, secret or position identifier.
- Do not expose the API bot token in chat, an issue, a commit, PR comment, Render logs or Telegram.
- Never put the BOT token in Render env to make keepalive appear healthy; credentials belong in Github Actions secrets or locally encrypted operational agent when it is reviewed.
- The previously documented `Crypto Lab - Fishing Room` destination must be configured as `TELEGRAM_CHAT_ID` secret. Do not embed it in public code. `TELEGRAM_BOT_TOKEN` is an independent secret from BotFather.
- `Privacy Mode` stays enabled for group; bot requires group membership and permission to post.
- A future Windows MEXC supervisor notifier can be added with isolated read-only status. **Do not connect it to private trading endpoints or orders without a distinct authority.**

## Minimal operator activation (NO token in chat)
1. GitHub repository `joseluisvieira28-oss/Laboratorio` → Settings → Secrets and variables → Actions → add `TELEGRAM_BOT_TOKEN` (existing token from private BotFather) and `TELEGRAM_CHAT_ID` (previous private group ID). Never place token in repo files.
2. Review the draft PR based on main. The workflow on this branch is **not** a scheduled live connection until it is merged to default branch; no main merge was performed during this task.
3. After controlled activation, Actions → Radar V0.9 Keepalive + Telegram private alarms → Run workflow → `telegram_test=true`. Require a real message in the group and action SUCCESS before classifying CONNECTED.
4. Verify a synthetic degraded source fixture in hermetic CI and perform a **read-only** real-health failure exercise. No disabling protective systems or failing live host deliberately.
5. Measure real uptime separately from Telegram status; to make forwards continuous switch to a genuinely always-on single writer after cost/risk review; upgrading Render, adding paid compute or changing deployment **is not authorized by this document**.

## Production truth, pre-existing
- Latest native Render deploy was recorded as live Oct10 05:19 UTC but last Supabase heartbeat Oct10 09:15 UTC, 17+ runtime gaps, one worst recent gap 12,841.725s, and collector archive 404. Existing keepalive 09:03 GitHub run cancelled after two 90s timeouts.
- Telegram is explicitly not a substitute for a market-data collector.

## Release
- Code: `.github/scripts/radar_telegram_health_v01.py`.
- Unit tests: `.github/scripts/test_radar_telegram_health_v01.py`, hermetic.
- Existing scheduler: `.github/workflows/radar-v09-keepalive.yml` (edited in feature branch only).
- QA: `.github/workflows/radar-telegram-test-v01.yml` (push branch, offline).
- Allowed mutation in this work: new isolated GitHub branch and draft PR only. No main merge, real alert dispatch, live trading, account access, wallet, Render plan upgrades, Telegram token reads, scientific retuning or capital spend.

## Render cost inventory / avoid accidental spend
- Read-only Render inventory at 2026-10-10: **8** services under `Laboratorio` workspace, **7 Free**, **1 paid plan `0.5c-512mb`**, the separate `Laboratorio` service (not the canonical public-shadow Radar).
- The paid `Laboratorio` service points at `main` with `autoDeploy=yes` and `rootDir=Dream-Account-OS-v2.3-PARTIAL`. A merge to main may provoke an unintended build/deploy of this independent service depending on deploy filters; no merge was attempted.
- The seven Free web services may use shared Free instance hours when awake; presence is **not proof of actual charges** or of simultaneous compute consumption. Do not suspend canaries until owner/purpose and forward coverage have been independently reconciled.
- Render publicly documents idle spindown after 15 minutes and a workspace Free-hours quota; moving Telegram from separate infrastructure to existing Github Actions alerts can save *notification* infrastructure but **never** makes the free compute always-on.

## 2026-10-10 13:06 UTC — Telegram delivery VERIFIED
- User manually added the two previously missing GitHub Actions **repository secrets**: `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. Their values were never fetched or printed.
- Isolated one-shot push/QA run: [Actions #38054434640](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38054434640), commit `edc194c6eca596b0105d0de3aea6b4edd8f4fdfe`.
- GitHub presence-only receipt: `TELEGRAM_BOT_TOKEN=PRESENT`, `TELEGRAM_CHAT_ID=PRESENT`.
- 12/12 hermetic tests PASS. One actual Telegram Bot API `sendMessage` call returned `TELEGRAM_DELIVERY_SENT`, step SUCCESS. This confirms Telegram API accepted test message to configured destination; human-read receipt was not separately verified.
- Ephemeral push-triggered test sender **removed immediately** in commit `b5b122423da96ebd93968024b8137497e9410140`. Regular QA workflow is back to safe offline-only + secret-presence checks.
- App source examined against canonical `forward_web.py`: `/api/state` is an existing public read-only endpoint; `checked_at_utc`, `mode`, `runtime_identity.service_id`, `ced1d_render_shadow`, and all four safety booleans are top-level fields. Current Render public shadow does NOT yet have `runtime_gap_history` which is proposed in distinct **draft PR #173**; notifier will consequently classify historical continuity as UNVERIFIED until that is reviewed/deployed.
- **State distinctions:** TELEGRAM_PRIVATE_TEST_SENT ✅; AUTO_RADAR_ALERTS_ON_DEFAULT_BRANCH ❌; VERIFIED_ALWAYS_ON_24_7 ❌; LIVE_TRADING_PERMISSION ❌.
- Controlled deployment still needs approval and guard for paid Render `Laboratorio` auto-deploy on `main`. No such merge/deploy occurred.

## 2026-10-10 15:06 Switzerland — Operator confirmed private Telegram receipt
- Operator supplied an authenticated UI screenshot showing the **Crypto Lab Fishing Bot** smoke-test message in **Crypto Lab - Fishing Room**, date October 10 at 15:06 Europe/Zurich (time shown in Telegram).
- This closes **DELIVERY_CONFIRMED** beyond the prior GitHub `TELEGRAM_DELIVERY_SENT` API acknowledgment; does **NOT** grant trading authority.
- Tested code now has one-shot sender removed. Existing workflow QA shows success after clean-up. 
- **AUTOMATED_SCHEDULE_NOT_ACTIVE**: GitHub `schedule` events run only on default branch; PR #174 remains draft/unmerged. Do not claim hourly/eight-minute Telegram monitoring is active.
- **PAID_SERVICE_DEPLOY_RISK**: Render `srv-dafgofv40ujc73b7o6og` tracks `main`, `autoDeploy=yes`, plan `0.5c-512mb`. A merge to `main` must not proceed until independent deploy-filter/plan risk review and explicit scoped owner authorization to alter main. This is separate from `crypto-edge-radar-v05-canary`, which tracks `crypto-edge-radar-postgres-v0.5` and `autoDeploy=no`.
