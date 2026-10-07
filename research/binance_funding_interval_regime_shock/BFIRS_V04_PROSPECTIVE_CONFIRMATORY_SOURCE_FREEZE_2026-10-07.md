# BINANCE-FUNDING-INTERVAL-REGIME-SHOCK-001
## V0.4 PROSPECTIVE CONFIRMATORY SOURCE FREEZE
Date: 2026-10-07
Status: FROZEN BEFORE ANY PROSPECTIVE MARKET OUTCOME

### 1. Scientific state entering V0.4
Known evidence:
- V0.2 Discovery 2023-2025: SURVIVES_FUNDING_INTERVAL_DISCOVERY.
- V0.3 2026 Jan-Sep source gate: HOLDOUT_INSUFFICIENT_SAMPLE.
- V0.3 opened ZERO 2026 market outcomes.

This V0.4 does NOT reuse the six V0.3 source clusters as confirmatory observations.

### 2. Prospective boundary
The prospective universe begins strictly AFTER the GitHub commit timestamp of this freeze file.

Only official Binance announcements published after that commit timestamp are eligible.

No announcement published at or before this freeze commit may enter V0.4.

### 3. Event definition
Use the SAME source/event definition as BFIRS V0.1:
- existing USDⓈ-M USDT perpetual contract;
- official Binance publication precedes exact effective timestamp;
- old and new funding interval explicit;
- new interval strictly shorter than old interval;
- no launch/listing;
- no delisting/automatic settlement bundle;
- no generic dynamic-rule-only event without a fixed named-contract transition;
- public Binance Data Vision premiumIndexKlines and fundingRate capability required.

One independent shock cluster =
official article code + effective timestamp + old interval + new interval.

Multiple contracts in one announcement/effective transition remain ONE independent shock.

### 4. Prospective evidence accumulation
No market premium/funding/price outcome may be opened while source evidence accumulates.

PROSPECTIVE_SOURCE_READY requires ALL:
- >=12 independent NEW shock clusters published after the freeze boundary;
- >=20 eligible asset-events;
- >=8 unique contracts;
- no single cluster >35% of eligible asset-events;
- all required public archive capabilities pass for the eligible event months.

Before these gates pass:
VERDICT = PROSPECTIVE_ACCUMULATING.

If official source enumeration becomes non-defensible:
VERDICT = PROSPECTIVE_SOURCE_BLOCKED.

### 5. Confirmatory analysis when ready
When PROSPECTIVE_SOURCE_READY is reached, create a separate immutable execution receipt that confirms the source universe and then run the BFIRS V0.2 analysis specification WITHOUT CHANGE:

- T0 = official publication timestamp.
- Tm = first full minute strictly after publication.
- baseline = [Tm-65m, Tm-5m)
- post = [Tm+5m, Tm+65m)
- controls = BTCUSDT, ETHUSDT, BNBUSDT, excluding treated controls in same cluster.
- require >=2 valid controls.
- >=54/60 bars per window.
- B(s,W)=median(abs(premium-index close)).
- C_raw = B_baseline - B_post.
- C_e = treated C_raw - median control C_raw.
- C_k = median C_e within shock cluster.
- primary unit = shock cluster.
- median C_k >= 0.00020.
- exact one-sided sign test p<0.05.
- 10,000 cluster bootstrap; seed 26061007; 95% lower bound >0.
- chronological halves both median C_k >0.
- same missingness, concentration, aggregation and no-rescue rules.

### 6. Prospective confirmatory verdict
If every source, sample, economic, statistical and temporal gate passes:
VERDICT = CONFIRMED_FUNDING_INTERVAL_EDGE

Otherwise after lawful outcome opening:
VERDICT = FAILS_PROSPECTIVE_CONFIRMATION

### 7. No optional stopping on outcomes
The only stopping rule before outcomes is the SOURCE count threshold above.

Premium outcomes remain sealed until source readiness.

Once PROSPECTIVE_SOURCE_READY is reached and outcomes are opened:
- run the confirmatory test exactly once;
- do not wait for more shocks because the result is unattractive;
- do not add/remove events after seeing outcomes.

### 8. Tradeability boundary
Even CONFIRMED_FUNDING_INTERVAL_EDGE does not authorize trading.

Tradeability requires a later pre-PnL freeze defining:
- executable hedge / position construction;
- entry and exit;
- fees;
- slippage;
- funding cashflows;
- capital requirements;
- venue constraints;
- minimum economically viable PnL.

### 9. Governance
- research-only;
- fail-closed;
- no main merge;
- no live trading;
- no orders;
- no wallets;
- no account reads;
- no authenticated/private endpoints;
- no exchange mutation;
- no spending;
- no post-outcome tuning.

### 10. Outcome-access declaration
At the time of this freeze:
- no V0.4 prospective premium-index outcome has been opened;
- no V0.4 prospective funding value has been opened;
- no V0.4 prospective price return/PnL has been opened.
