# CRYPTO LAB — LIVE READINESS V2
## Supervised Automated Execution — architecture and auditable NO-LIVE-GO program
**Date:** 2026-11-04 (Europe/Zurich)  
**Classification:** DESIGN ONLY · DEFAULT DISARMED · PAPER ONLY · NO ORDERS · NO SECRETS · NO EXCHANGE AUTHENTICATION  
**Repository:** joseluisvieira28-oss/Laboratorio  
**Independence:** This is an isolated operations architecture proposal. It does not amend, unlock or merge any prior scientific strategy / cost / holdout / outcome protocol.

## Executive decision
**NO_LIVE_GO.** There is no currently certified independently positive net edge that authorizes automated execution. Source-window proof, synthetic risk tests, historical bar-proxy returns, quote freshness, compilation, Telegram delivery and CI are not profitable trade execution proof.

The requested operating model is *supervised automatic trading*: human pre-authorizes a SHORT-LIVED session policy and can instantly DISARM future entry intents; eligible deterministic signals may be actioned only under that frozen policy by a dedicated executor *after* all independent safety and economics gates pass. Telegram is a reporting channel, not a stop-loss engine or an unrestricted order gateway. At this stage no action path may touch a real broker.

## Prior evidence: preserve original authority and state
- PR #333 LIQUIDATION EXHAUSTION ECONOMIC FORWARD V1: dual Bybit/MEXC source-window causal check independently PASS on one BTC liquidation event, **zero eligible strategy decisions, ECONOMIC_FORWARD_INSUFFICIENT**. Freeze 88e7632c remains authoritative to that strategy. No change to 5/15/30s delay, 60s outcome, costs or 60 episodes across 14 dates.
- PR #107 LICP-001 BTC cascade continuation: original terminal **NO_EDGE**, reported mean base -16.374554bps; do not reverse old trade labels or search horizons to rescue.
- PR #223 independent offline monotonic-stop risk engine and early profit policy: synthetic stop and sizing invariants, real native stops/fills NOT demonstrated; a separate historical 50%-early close study lost modeled return vs its parents in all four examined strategies. Do NOT make early-harvest compulsory.
- PR #200 OPTIONS V2.1 stop ACK / recovery preconditions: offline safety framework, no broker stop-ACK/amendment proof, proposed entries still blocked.
- PR #226 three-canas 100USDT 10x Windows package: synthetic/read-only fail-closed, account balance and netting not broker-verified; **NO_LIVE_GO**, not proof of 3 separately protected positions.
- PR #162 governance / power gate: keep SOURCE_BLOCKED, UNDERPOWERED and economic NO_EDGE distinct and do not infer edge from non-significance.

## Logical architecture — enforce separation of duties
```
[Raw market data / provenance / clock]
               |
         [FROZEN SIGNAL ENGINE]     no broker keys
               |
      [INDEPENDENT RISK FIREWALL]   separate code/policy owner
               |
       [SESSION AUTHORISATION]      human ARM with expiry and scope
               |
      [IDEMPOTENT INTENT QUEUE]     durable journal + dedup
               |
       [EXECUTION ADAPTER]         PAPER ONLY at this stage; production adapter absent
               |
 [ORDER & NATIVE STOP VERIFICATION] broker receipts required in later separately authorised phase
               |
     [RECONCILIATION / TELEMETRY]    append-only receipts + Telegram alerts
```
Signal logic NEVER calls broker transport directly. The independent firewall can veto but not relax immutable strategy criteria. Any future production adapter is separately code-reviewed, permissioned and unavailable by default.

## Mandatory session state machine
`DISARMED -> PAPER_VALIDATED -> (future) LIVE_ELIGIBLE -> ARMED_SHORT_TTL -> DISARMED`.
- Current installation remains hardcoded `DISARMED / PAPER_ONLY`; there is **NO LIVE_ELIGIBLE** implementation and no broker order transport.
- Human approval of a future session must be explicit, authenticated out of band, time-bound (e.g. <=2h), scoped to one strategy SHA, symbol, account, quantity/risk ceilings and maximum simultaneous positions. Arbitrary Telegram text or a webhook is not authorisation.
- Expired TTL, revoked arm, policy hash mismatch, process restart, unreconciled state, stale data, clock drift, missing stop or account uncertainty => `DISARMED` / reject NEW entries.
- Telegram may show `STATUS`, `DISARM`, hypothetical `ARM` confirmation and receipts. No general-purpose `TRADE` endpoint. Commands must be authenticated, nonce-bound, single-use and rate-limited if later implemented.
- The emergency DISARM stops NEW submissions only. It cannot guarantee stopping an in-flight or broker-native order; cancel/close/reconcile are separate explicit procedures with broker acknowledgements.

## Risk firewall design — proposals for later operator signoff, NOT applied trading parameters
- Example upper-bound initial policy only: modeled planned cash risk <=0.25% of **verified available equity** per trade, aggregate planned open-stop risk <=0.5%, daily realized+unrealized loss stop <=1%, weekly <=3%. Operator must formally agree later; if min contracts make limits impossible, SKIP trade. Numbers are not guaranteed actual loss boundaries.
- Simultaneous physical positions: **one per instrument by default**, max one total initially. A long and short from distinct logical strategies cannot silently net/hedge. Verify account one-way/hedge mode and position identity before any expansion.
- Isolated margin only if supported, account-verified and explicitly allowed; initial **no high leverage**. Leverage does not define stop loss; gap/slippage/liquidation and maintenance margin may exceed modeled exposure. No pyramiding/martingale or averaged-down entries.
- Size: Decimal math, venue contract multiplier, min step, tick, min notional, depth-aware expected market impact, maker/taker fees, entry+exit spread, signed funding reserve and liquidation buffer; rounded DOWN. Never assume free commission or API fee parity with app/web.
- Reject if expected *lower-bound* model net edge / risk-reward cannot cover verified fees + full bid/ask spread + conservative execution impact. Edge and tail-loss assumptions must be frozen before paper outcomes.
- Before any future live entry, prove a native broker-side protective stop policy is valid for symbol and signed side; quantity/price tick exact; stop is server-hosted, direction-correct and independent of Windows/Telegram. Entry-and-stop atomicity, if unavailable, has **exposure gap** that must be quantified and authorised; unproven => NO_GO.
- Never treat a locally requested stop as an ACK. Verify independently (broker-side order ID, position ID, filled volume, stop volume and trigger semantics) and reconcile on partial fills or adds/reductions.
- Trailing rules can only tighten relative to broker-ACK stop: LONG stop cannot decrease, SHORT stop cannot increase. Never silently remove a stop to amend it without independently proven replacement semantics.
- Disallow any extra entry with broker status unknown, partially filled orders unresolved, >max source age, API rate limits, incorrect exchange/strategy price units, conflicting open stops, or account money/positions inconsistent.
- Circuit breaker on max slippage, stale book, rising error counts, raw source sequence gaps, broker rejects, stop-ACK timeout, unexpected position, replayed intent, uncontrolled duplicate, API access revoked, unusual mark/last/index divergence.
- Operator key security (future only): least privilege, no withdrawals, IP allow-list, rotation/revoke; secrets never in Telegram, GitHub artifacts, committed code or screenshots; use secret storage with auditable access.

## Hard independent GO gates — not interchangeable
1. **G0 SCIENTIFIC EDGE**: independent prospective after-cost lower-bound profitability on strategy-specific frozen unseen data / adequate predeclared power. Absent => NO_GO (applies to all current strategies).
2. **G1 SOURCE & EXECUTION PATH**: native source custody, cross-venue quote causal receive-time, fees by *actual accessible API route and account*, eligibility (region/KYC), symbol/min contract, stop/position semantics. MEXC API may not provide a sandbox; offline mocks do not count as live broker proof.
3. **G2 PAPER SHADOW**: prospectively log every intent and would-be fill, actual exchange bid/ask and depth, manual/automatic delay alternatives, full fee/slip/funding scenarios, cancellations/missed fills, daily variation, max drawdown, tail gaps, source invalidations; no policy drift. Reject returns computed from post-event prices unavailable at decision.
4. **G3 OFFLINE ADVERSARIAL FAILURE INJECTION**: independent tests of all failure scenarios below, order/stop state machine + idempotency, robust journal/restart reconciliation with no double submission.
5. **G4 READ-ONLY ACCOUNT VERIFICATION (separately authorised)**: actual mode, equity, permissions, exchange policy, existing positions/stops and current fees, with no writes. Existing connected data is not proof of account state unless read and attested.
6. **G5 CONTROLLED INTEGRATION REVIEW**: secure production adapter code review, broker stop ACK/partial-fill/crash recovery protocols; if no safe test environment or permitted non-live proof, remain blocked rather than risk money to test. A future distinct explicit signoff is mandatory before any real-order attempt.
7. **G6 GO/NO_GO SIGNATURE**: dated human approval referencing strategy SHA, risk-policy SHA, target account and capital limit, report hashes, rollback and time-to-live. No implicit approval from broad research authorisation.

## Adversarial mandatory test matrix (mock only at this stage)
- stale Bybit liquidation, crossed/stale MEXC bid/ask, missed depth sequence, publisher/local clock mismatch => reject.
- order arrives twice / worker restarts after queue ACK / ambiguous response => never blind resend; reconcile by idempotency key.
- process crashes after entry intent, between theoretical fill and stop placement, while changing stop, and during cancellation => state UNKNOWN, block entries; broker reconciliation required.
- partial fills and min contract rounding => no unprotected remainder / no "3 strategy slots" on one physical netted position.
- protective-stop request not accepted, ACK missing, wrong direction, wrong size, stop already triggered => FAIL CLOSED; any future emergency close is contingent on live broker capability, not guaranteed.
- Telegram offline/late/forged commands, network split, credential rotation/revocation, VPN/IP change => no autonomous limit escalation.
- gap through stop, extreme spread, 10x liquidation, min order > budget, API outage, rate limits => simulate losses beyond modeled planned risk, disable further entries, escalate to human.
- same symbol simultaneously signaled by different models => one unique physical exposure and independent risk arbitration.
- user disables entries while order in flight => prevent NEW orders and reconcile ambiguous pending commands; do not claim cancellation without broker ACK.

## Operational phase plan (no automatic recurring runs configured)
**P0 Spec and adversarial design**: THIS branch, pure docs. Preserve earlier freezes unmodified.  
**P1 Offline broker-mock and threat-model tests**: implement pure policy / state-machine tests only, no API keys, no network order path, no deployment.  
**P2 Source-only and paper shadow**: only by separate explicit time-bounded request and independent forward protocol; source snapshots alone not enough.  
**P3 Risk/cost/account attestations**: only future explicit read-only account permission and external documentation.  
**P4 Future signoff review**: candidate may advance to LIVE_ELIGIBLE only if every gate passes. Current terminal label: `NO_LIVE_GO / ECONOMIC_EDGE_UNPROVEN`.

## Authoritative references and limitations
- Internal GitHub research PRs #333, #107, #223, #200, #226, #162, preserved untouched.
- MEXC public information: Futures API trading announced 2026-03-31 for eligible KYC users; API fee structure distinct from web/app and availability may vary by region. This dated announcement is **not a verified current fee tier for this operator**: https://www.mexc.com/announcements/article/introducing-api-futures-trading-on-mar-31-2026-17827791534551
- MEXC states their API is live-facing and has no sandbox in public FAQ: https://www.mexc.com/mexc-api — technical non-live testing must be mocked and rigorously bounded.
- MEXC TP/SL support article notes partial/entire stop volume behavior and market execution slippage; this is retail product documentation, **not proof that a Futures API order will atomically attach broker stop**: https://www.mexc.com/support/article/mexc-futures-take-profit-and-stop-loss-faq-350096811661177856

**Non-negotiable:** creation of this architecture does NOT authorize real orders, any trading adapter, exchange authentication, new funded services, deployment, schedules or merging to main. No keys or private account access requested. No claim that stops or daily risk ceilings guarantee maximum realized losses.
