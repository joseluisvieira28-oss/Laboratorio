# MU Cash to MUSTOCK 10m — SOURCE + RULE FREEZE, October 30 2026

First validate data, with ZERO market returns or outcomes. Symbols: actual cash stock Yahoo MU, MEXC standard index MUSTOCK_USDT, and previously observed 10-minute Event Futures contract MUSTOCK_USDT. They are separate feeds; no historical parity with actual Event Futures server open/expiry price proven. Screenshot symbol MLIUSDT remains UNKNOWN and must NOT be mapped to MU.

TRANSFER hypothesis, without fitting on MU prices: identical frozen NVIDIA cash/index 3-minute impulse signal. Fixed NY times 09:35,09:45,...11:25, 12/day. Price features: 1m bar CLOSE at t-4min and t-1min, cash and index. Qualify if abs(cash return)>=10bps AND abs(cash minus index return)>=5bps AND same sign of cash and gap. Side follows cash. Otherwise ABSTAIN. H=10 minutes. 24 slots: Oct 28 and Oct 29 2026 (America/New_York EDT UTC-4).

SOURCE-ONLY stage: Yahoo MU cash 1m Oct28 00UTC to Oct30 00UTC, MEXC standard index MUSTOCK_USDT Min1 for Oct28 and Oct29 13:20–15:40 UTC. Two GETs each, raw response hashes and canonical timestamp, OPEN and CLOSE data for exact needed bars. 24 feature starts/day cash; index feature, entry and expiry 1m starts; positive finite, no interpolation, zero missing and exact repeated canonical hash. If blocked, no returns.

OUTCOME stage only after source hash freeze: index minute OPEN(t) and OPEN(t+10m) are minute-boundary approximations 10 seconds BEFORE intended decision/expiry, not actual Event Futures prices. Report all 24 slots and no-signal reasons, same-direction win/loss, matched baselines, q=0.80 hypothetical, secondary q=0.85; unknown historical real payout. No new data, day/time choice, thresholds or asset substitutions after opening prices.

Both dates are Discovery, not independent holdout. No Sept 2026 protected holdout, no reading NVDA Oct05–30 sealed forward, no orders/account/private keys/wallets/money/main merge. Previous CPI-surprise NO_EDGE and NVIDIA sparse signal remain unchanged.
