# CRYPTO LAB — TIER 2 AUTO-MICROLIVE EXECUTION POLICY V2 — 2026-09-25

**Policy ID:** TIER2-AUTO-MICROLIVE-POLICY-V2.0-FROZEN-2026-09-25  
**Status:** FROZEN / PROSPECTIVE / SUPERSEDES V1 GOVERNANCE WAITING RULES  
**Purpose:** make legitimate Tier-2 candidates automatically eligible for bounded real-money micro-live execution without per-trade human confirmation or additional governance waiting gates, while preserving frozen science.

## 1. Core rule

A candidate that legitimately holds Scientific Tier 2 under frozen science is automatically admitted to the AUTO_MICROLIVE lane.

No additional Tier-1, Diamond, first-N-forward, calendar-time, observation-count, or governance-review wait is required solely to begin micro-live execution.

Tier-2 AUTO_MICROLIVE admission is a governance consequence of the scientific tier; it is not a new scientific verdict.

## 2. Automatic means automatic

For a Tier-2 candidate whose exact execution mapping exists and whose current signal and operational gates pass:

- no per-trade operator click is required;
- no per-trade human reconfirmation is required;
- no new candidate-specific governance amendment is required for each signal;
- no separate future activation authority is required for each trade;
- the executor may create the candidate-specific immutable order authority mechanically from the frozen policy + frozen execution mapping + canonical signal;
- entry and exit are both automated according to the frozen candidate horizon.

Human interaction is not part of the signal-to-order path.

## 3. What may still block an order

AUTO_MICROLIVE does not waive actual execution correctness.

A live order is allowed only when ALL are true:

- scientific tier is exactly Tier 2 or higher;
- candidate is not terminal / NO_EDGE / source-invalidated;
- immutable candidate identity is known;
- canonical source is healthy;
- current canonical signal exists;
- signal is inside its frozen TTL / timing window;
- exact venue / instrument / symbol / direction mapping matches the parent science;
- current market state is fresh;
- current authenticated account state is fresh;
- hard account firewall passes;
- venue minimum fits the frozen notional cap;
- exactly-once order intent is durable before transport;
- duplicate signal/order detection passes;
- no conflicting open position/order exists;
- restart/recovery reconciliation is clean;
- exit path is pre-bound and executable;
- global kill switch is absent.

Unknown, stale, mismatch, duplicate, missing mapping, or failed reconciliation = NO_ORDER.

These are execution gates, not additional scientific waiting gates.

## 4. Default V2 live envelope

Unless a stricter frozen candidate rule exists:

- maximum notional per live position: 10 USDT equivalent;
- maximum total live account exposure under this program: 10 USDT equivalent;
- maximum simultaneous live positions: 1;
- futures leverage: exactly 1x;
- futures margin: isolated only;
- Auto Margin Add: OFF;
- daily realized-loss halt: 2 USDT;
- rolling 7-day realized-loss halt: 5 USDT;
- cross margin: forbidden;
- averaging down: forbidden;
- martingale: forbidden;
- revenge sizing: forbidden;
- automatic size escalation: forbidden;
- late-entry chase: forbidden;
- venue minimum above 10 USDT: NO_TRADE;
- emergency global kill switch: required.

Sizing may only increase under a separate future policy after evidence is reviewed prospectively.

## 5. Tier-1 / Diamond gates are promotion gates only

For an already-valid Tier-2 candidate, later first-N-forward, 60-event, 8-week, first-25, first-50, or other strengthening gates remain fully binding for Tier-1 / Diamond adjudication.

They are not AUTO_MICROLIVE blockers unless the gate is itself part of the frozen parent scientific signal definition.

Micro-live outcomes:
- do not automatically promote Tier;
- do not change thresholds;
- do not permit rescue tuning;
- do not justify size escalation;
- are preserved as prospective execution evidence only.

## 6. Protected / no-peek lanes

A protected no-peek or sealed promotion experiment no longer blocks AUTO_MICROLIVE for a valid Tier-2 candidate.

Instead:
- the sealed scientific lane remains unchanged;
- a separate execution fork is created prospectively;
- all live execution outcomes are explicitly excluded from the sealed lane's promotion evidence;
- the execution fork receives zero promotion credit from the protected lane;
- the operator may see live PnL without invalidating the historical existence of the sealed experiment, because the execution fork is analytically separate.

No post-outcome parameter change is allowed in either lane.

## 7. Current Tier-2 candidates under V2

### OPTIONS-SPOTPERP-001-V2.1
State: AUTO_MICROLIVE_ELIGIBLE.
Frozen parent mapping:
- position > 0 = LONG BTCUSDT Spot;
- position < 0 = SHORT BTC_USDT perpetual;
- entry = 00:00 UTC t+1;
- exit = 00:00 UTC t+2;
- frozen risk scaling preserved;
- BASE10 / STRESS20 science unchanged.

No first-50 wait is required for micro-live. First-50 remains Tier-1/Diamond evidence only.

### BNB-LAUNCHPOOL-DEMAND-001
State: AUTO_MICROLIVE_ELIGIBLE.
Exact parent identity remains LONG BNBBTC SPOT, no leverage, 24h hold.
No futures substitution.
BNB Diamond first-25 remains promotion evidence only.

### CED1D-0031
State: AUTO_MICROLIVE_ELIGIBLE.
A live order still requires a current healthy source and a frozen exact execution mapping. Source failure or missing mapping = NO_ORDER.
The 60-event / 8-week gate remains promotion evidence only.

### ETF-CME-INSTFLOW-001
State: AUTO_MICROLIVE_ELIGIBLE_VIA_EXECUTION_FORK.
The Q4 V0.1A sealed lane remains unchanged.
Any live trade is attributed to the execution fork and receives zero promotion credit from the sealed Q4 lane.
Current signal/route direction mismatch still blocks an order.

## 8. Future candidates

Any future candidate that legitimately reaches Tier 2 under frozen science automatically inherits this policy.

No separate policy vote, governance amendment, or generic additional wait is required.

The implementation registry only needs to bind the exact frozen execution mapping and technical executor contract. That binding is implementation metadata, not a new scientific or governance approval gate.

## 9. Safety and authority

This V2 authorizes automatic micro-live governance for Tier-2 candidates under the hard envelope above.

It does not authorize:
- changing scientific rules;
- fabricating a signal;
- entering after a missed window;
- direction substitution;
- venue substitution that changes economic identity;
- leverage above 1x;
- exposure above 10 USDT;
- bypassing stale/failed gates;
- withdrawals or transfers;
- wallet mutation;
- post-outcome tuning.

