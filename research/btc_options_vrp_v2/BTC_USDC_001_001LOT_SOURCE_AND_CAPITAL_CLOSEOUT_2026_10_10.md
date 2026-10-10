# BTC OPTIONS VRP V2 — CURRENT BTC_USDC 0.01 PAIR SOURCE, FEE AND CAPITAL CLOSEOUT
2026-10-10 · `research/btc-vrp-usdc-paired-quote-capital-source-2026-10-10` · **RESEARCH/SOURCE-ONLY**

## Canonical executed source proof
Successful frozen CI [38036299950](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38036299950), commit `13762cbe5ff220854cf26588f258282c58873aa7`, artifact **11663907729** `btc-vrp-usdc-001-current-public-pair-source-v01` contains immutable request start/end and response SHA256, public best prices/sizes with source timestamps, cost/margin diagnostic, no future outcomes. First 2 CI runs (38036189216, 38036255856) failed *textual self-checks before public market queries* (strings `auth/` in comment and `.0003` instead of `0.0003`); CI fixed only those self-checks, no scientific selection/cost change.

FROZEN SELECTION: Deribit public linear `BTC_USDC` options, expiry nearest 30 DTE in 14–60 DTE, earlier expiry tie, nearest log-moneyness strike. At public snapshot observed approximately **2026-10-10 07:59 UTC**, the selected pair was:
- `BTC_USDC-30OCT26-83000-C` call + `BTC_USDC-30OCT26-83000-P` put;
- same expiry **2026-10-30**, strike **83,000 USDC**, ~**20.00 days remaining** (nearest actually available expiry, not a 30D guarantee), BTC_USDC index ~**82,747**.
- Each minimum trade `0.01`, contract size 1 BTC.
- Call BBO (USDC premium per 1 BTC): bid **2,500** / ask **2,540**, bid displayed amount **0.51**, ask displayed amount **16.01**, source quote age ~**1.561 seconds**.
- Put BBO: bid **2,480** / ask **2,540**, bid displayed amount **0.77**, ask displayed amount **0.77**, source quote age ~**1.784 seconds**.
- BTC_USDC-PERPETUAL hedge-source BBO: bid **82,747.6** / ask **82,747.7**, quote age ~**0.141 seconds**. This is source witness, *not simulated hedge fills or hedge margin*.
- Both option legs and perp fresh (<30 s), no crossed BBO, bid AND ask minimum visible size each >=0.01. **`PAIRED_ENTRY_BBO_SOURCE_PASS_ONLY_NOT_EXECUTION_OR_PNL`**. This one-shot Saturday diagnostic is NOT a valid Thursday 08:05 UTC prospective weekly entry-bank observation.

## Economic source arithmetic only (NO STRATEGY PnL)
| Non-trading hypothetical at observed snapshot | Amount USDC |
|---|---:|
| 0.01 call bid premium SELL | 25.00 |
| 0.01 put bid premium SELL | 24.80 |
| **Total option SELL bid premium** | **49.80** |
| Deribit STANDARD opening 2-leg fee (3bps of underlying, capped at 12.5% leg premium) | **0.49636** |
| Immediate option ASK-vs-BID crossing spread for both legs | **1.00** |
| Immediate hypothetical option ASK buyback fee for both legs | **0.49636** |
| **Total instantaneous marketable roundtrip friction** | **1.99272** |
| **Roundtrip friction / initially received option bid premium** | **4.00144%** |
| Estimated call short Standard initial margin | **149.36** |
| Estimated put short Standard initial margin | **149.29** |
| **Estimated gross short pair Standard initial margin** | **298.65** |

The premium is gross cash credited on sale, **NOT profit**. Immediate buyback numbers measure ONLY current source quote spread+fees as if immediately crossed in same snapshot; do not convert into future-expiry earnings, win probabilities, edge after hedging, or actual filled trades. Initial margin is a broker-specific time-varying constraint, **not a maximum loss**; short uncovered options may have large losses. No hedge margin, future perp financing/funding, collateral fees, liquidation/delivery fees, bid/ask depth-through-size, account eligibility or actual maker/taker tier verified. Official fee authority: https://support.deribit.com/hc/en-us/articles/25944746248989-Fees. Margin formula: https://support.deribit.com/hc/en-us/articles/31424932728093-Linear-USDC-Options .

## Frozen scientific verdict
- `PHENOMENON_SURVIVES`: original historical IV−RV ~+10.43 vol points, 192 weeks (discovery observation), NOT option strategy PnL.
- `CURRENT_BTC_USDC_PAIRED_BBO_SOURCE_PASS`: single snapshot. Original operator capital route ~301 USDC now corroborated ~299 USDC gross naked option pair margin before hedge.
- `HISTORICAL_PAIREDEXECUTION_SOURCE_INSUFFICIENT`: earlier 2025 source strict two-leg witness 0/52 for frozen 30D short-short anchors (and 1/52 any-direction).
- `DIRECT_WEEKLY_CAPITAL_NORMALIZED_CONFIRMATION_UNDERPOWERED_PRE`: existing revoked N=36/N_eff=30 and thousands-effective-weeks issue preserved. One fresh quote does not change power.
- `EXECUTABLE_AFTER_ALL_COSTS_NET_EDGE_UNPROVEN` / `NO_MICROLIVE_GO`. Neither SURVIVES_FORWARD nor NO_EDGE_AT_H justified.

Next legitimate action: source-only outcome-blind Thursday 08:05 UTC forward entry bank under `LINEAR_USDC_FORWARD_ENTRY_SOURCE_BANK_V0.1.md`, with no backfill, only when bank workflow is *actually* invoked within Thursday 08:00–08:15 UTC. Do NOT open settlement or return PnL. Independently design a better powered capital-risk estimand and ex-ante evidence rule **before** any future outcome is viewed. If this is not feasible, close exact route SOURCE/POWER_BLOCKED rather than manufacture profitability.

No orders, private account reads, paid data, wallets, trading, exchange mutation, merge to main, or protected holdout opening.
