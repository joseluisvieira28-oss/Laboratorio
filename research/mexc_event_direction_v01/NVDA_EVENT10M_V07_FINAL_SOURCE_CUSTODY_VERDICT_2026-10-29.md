# NVIDIA Event-10M — Scientific and Operational Closeout V0.7
**Dated 29 October 2026 | Branch-only research, no live orders or capital**

## Outcome
- **SOURCE_READY (LIMITED):** NVIDIA cash 1m Yahoo + MEXC standard index Min1 + exact MEXC NVIDIA_USDT Event Futures ONLINE/10m payout + public NVIDIA index tick were available with strict as-of source timestamps simultaneously in a source-only smoke.
- **PRE-OUTCOME GITHUB ARTIFACT CUSTODY (SYNTHETIC): PASS.** A real uploaded synthetic JSON was retrieved from GitHub Actions API, verified against its workflow run, server created_at, server-reported zip SHA256 and exact archived decision bytes. The synthetic mode cannot be promoted to a real forecast/expiry receipt.
- **OFFLINE SHADOW-EXPIRY GUARDS: PASS** on synthetic data only; strict first public MEXC index tick at/after 10min target and <=5sec lateness; not the actual Event Futures order-lock and settlement prices.
- **FORWARD FORECASTS:** 0; **forward resolved event-shadow outcomes:** 0; **live trades:** 0; **verified economic advantage:** NONE.
- **Scientific verdict: PAPER-INFRASTRUCTURE-PREPARED / ECONOMIC_EDGE_NOT_TESTED / NO-LIVE-GO.**

## Evidence and defects
1. Existing integrated clock [#40905997541](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40905997541): cash/index/product/event_tick=true, one sample, no forecast.
2. Frozen Nov 2026 paper rule [PR #283](https://github.com/joseluisvieira28-oss/Laboratorio/pull/283): 3m cash NVDA >=10bps, cash minus MEXC index gap >=5bps in same direction, otherwise ABSTAIN, only fixed post-US-open 10m decision slots; no parameter edits.
3. New offline custody/unit [#40907754711](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40907754711): 8/8 synthetic tests PASS (server metadata, ZIP bytes, wrong run, late archive, missing/altered source, unsupported anchor).
4. Initial **real GitHub upload** [#40908128772](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40908128772): artifact stored but Python HTTP signed redirect returned HTTP400; custody FAILED. It is not counted as PASS.
5. Corrected **real GitHub upload/download** [#40908308812](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40908308812): GitHub API metadata + curl signed redirect downloaded immutable artifact ZIP, SHA256 and original JSON verified. Output `SYNTHETIC_CUSTODY_TEST_ONLY` and isolated protocol name. Genuine operational proof, no real market signal.
6. Gh artifact `created_at` UTC second precision vs decision millisecond time: pre-outcome V0.7 precision errata permits <=999ms archive-timestamp rounding; both original bytes and exact server-created-before-expiry remain mandatory. [#40908585854](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/40908585854) offline precision regression+ blueprint guard PASS.
7. The one-shot no-trade workflow `.github/workflows/nvda-event10m-one-shot-operator-v07.yml` is **DORMANT** on a research branch: GitHub `workflow_dispatch` only works for workflows registered in the default branch. No default-branch merge authorized or performed. It must NOT be described as scheduled or running.

## What an actual scientific forecast would require
Starting 2026-11-02, and only in frozen 09:35–11:25 America/New_York 10m slots, an authorized runner must collect all four causal observations as-of, compute immutable paper decision, upload it as GitHub artifact before expiry, independently verify server-created_at and byte identity, and then collect a strictly valid public index tick within 5secs of the 10m deadline. If one step fails: BLOCK/ABSTAIN with archived reason. The original Oct05–30 NVDA regular-session protected V0.6 forward remains unread until closed; September 2026 protected holdout remains untouched.

Before any claim of positive PnL from MEXC Event Futures, the research must additionally prove real Event Futures server-assigned openPrice and expiry settlement index parity; point-in-time official cash data availability; actual direction-specific contract payouts; sufficient >60 outcome samples in >15 distinct sessions, robust time-block intervals, chronological thirds and controlled multiple testing. A shadow-index directional win is NOT a MEXC payout receipt.

No default main change, automatic future scheduler, exchange accounts, orders, crypto leverage, wallets, private exchange endpoints or money spent.

**Decision:** archive V0.7 as operational-readiness research. Scientific **GO only for independently anchored November paper observations after activation**. Economic **NO-GO today** (no forward observations; not a negative edge determination).
