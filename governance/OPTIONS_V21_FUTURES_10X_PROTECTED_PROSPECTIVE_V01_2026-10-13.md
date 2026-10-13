# OPTIONS V2.1 Futures — Prospective 10x Protected Execution Fork V0.1

**Date:** 2026-10-13
**Status:** PRE-OUTCOME ENGINEERING PROTOTYPE / NO LIVE TRADING AUTHORITY
**Parent:** OPTIONS-SPOTPERP-001-V2.1 scientific signal unchanged
**Execution fork:** OPTIONS-SPOTPERP-001-V2.1-FUTURES-10X-PROTECTED-PROSPECTIVE-V0.1
**Operator request:** Explicit request in chat to pursue 10x and LIVE GO; recorded as intent, NOT a declaration that risk, profitability, stop semantics, and on-exchange execution have passed certification.
**Main merge:** PROHIBITED
**Account mutation:** NONE in this audit.

## Prespecified scope

- BTC_USDT MEXC USDT perpetual Futures only; LONG and SHORT accepted only for valid immutable OPTIONS V2.1 canonical direction.
- 10x isolated leverage **exactly**, automatic margin addition disabled, HEDGE mode only.
- **Maximum 10 USDT notional**, scaled DOWN by frozen signal weight (this is not a 10 USDT margin allowance). Concurrency cap 1 position, no auto-size escalation.
- Daily realized loss kill 2 USDT and 7-day loss kill 5 USDT; separate safety override requires new freeze, NEVER silent relaxation.
- 24h timed exit when possible; no chasing signals after existing 300s TTL.
- Precommitted protective stop mandatory on each opening order. Proposed gate: stop within 200bps of current appropriate BBO, correct LONG/SHORT direction and contract price tick alignment; live protection verified with matching exchange order position ID, volume, side and price, otherwise emergency-close path.
- No stop price currently derived from the frozen canonical signal, so the present prototype MUST NOT enter any trades; a forward-looking, independently frozen stop policy and original timestamps must be established before outcomes are opened. This 200bps max distance is an engineering safety ceiling, not an optimized strategy stop.
- The existing on-disk 1x authority receipt cannot authorize this 10x fork; distinct execution_contract & authority string. A new live authority is NOT to be synthesized from this document.

## Economic reality

The pre-existing 2025 independent OOS V2.1 trade-level bridge reported NET10 +5.0427663334 bps, NET20 -4.6759378383 bps, implied sensitivity at 16bps full-notional ~-0.7884561696 bps/opportunity, before spread/slippage/funding. These OOS numbers do not validate a new 10x execution fork. Holding nominal capped at 10 USDT means 10x leverage does not lower the proportional taker fees or manufacture positive expectancy; it increases liquidation sensitivity and operational risk.

## Mandatory before any real live consideration

1. Immutable prospective protective-stop algorithm: verified tick rounding, trigger conditions and account-independent signal freeze; no tuning against subsequent outcome.
2. Broker test evidence proving creation, state querying, partial fill, triggered execution, cancellation after normal exit, crash/restart reconciliation, and no naked interval after entry; a mock-only CI run is NOT enough.
3. Execution readiness: accurate own-positions/order/stop reconciliation, risk budget and capital, market minimum, account fee schedule, spread/slippage/funding, current source quality, operator notifications and emergency shutdown.
4. Defensible **positive net** forward edge for this exact 10x stop-protected execution policy; old 1x OOS cannot be promoted. Fees 16bps MARKET round trip per frozen conservative official rate before other friction.
5. Explicit distinct authority after review; no overwrite of installed 1x production bundle, no task auto-enablement by installer.

## GO/NO-GO

**Engineering implementation and synthetic unit testing only.** Live order placement **NO-GO** until all blockers close and independently documented. Do not edit or install this branch as a substitute for the currently disabled Windows executor.
