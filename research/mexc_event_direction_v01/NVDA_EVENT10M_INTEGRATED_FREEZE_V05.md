# NVIDIA Event10M V0.5 — read-only integrated decision receipt

Frozen 2026-10-29 BEFORE any November signal/outcome.
**SCOPE**: collect source receipts for exact four public legs and instantiate the ALREADY frozen V0.1 model only if all four source gates and date/time gates pass. No change to threshold, horizon, session, side, baseline, target or September protected holdout. Historical NVDA V0.6 Oct05-30 forward stays SEALED until Oct31.

Sources:
1. Unofficial publicly available Yahoo NVDA cash equity 1m chart range=1d, raw hash and receive timestamp, at most previous 4- and 1-minute *completed* bars.
2. MEXC NVIDIA_USDT public standard futures INDEX Min1, same. Not the executed Event Futures price.
3. MEXC exact public Event Futures product detail, using anonymous GET-only Chromium, 10m MINUTE rate up/down and ONLINE state, hashed; require within 10secs of decision.
4. MEXC public NVIDIA_USDT push.index.price tick, hashed; within 2secs of decision.
Model uses same frozen 3m cash vs index impulse thresholds 10bps/5bps. All prices and data snapshot receipts must be acquired before decision timestamp (actual wall clock). A single source-lag or bad time => BLOCK; never substitute data, retry into later window, interpolate, or invent payout.

**--source-smoke** must never call forecast or produce any signal, regardless of date. **--decision** is effective only in frozen November 2026 NY 09:35-11:25 every 10m at seconds 05–30, otherwise fails closed. The code never submits or mutates exchange orders/accounts/private endpoints. Script is not automatically scheduled on branch; workflow push triggers source-smoke only. Synthetic unit tests establish mechanics, not source integrity/market edge.

Every FORECAST decision receipt must be externally timestamp-anchored before opening its expiry target, e.g. a completed GitHub artifact upload with resulting artifact ID/digest. This collector does NOT automatically evaluate expiry or construct an Event Futures PnL. There is no expiry clock parity proof or independently calibrated probability; current status remains SOURCE_READY_PREP / NO_EDGE / NO_LIVE.
