# BTC OPTIONS VRP V2 — Canonical public-forward source integrity patch 2026-10-10
Status: **OPERATIONAL SOURCE QUALITY ONLY** · PRE-THURSDAY · SCIENCE UNCHANGED

Independent frozen technical source audit branch `audit/vrp-usdc-forward-bank-integrity-2026-10-10` produced [successful 40-case synthetic CI run 38047149845](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38047149845). Its source script and tests were tested without any live market source call, without creating `data/vrp_usdc_forward/entry_source_bank.jsonl` or `receipts/vrp_usdc_forward/`, and without fetching any settlement/returns.

## Fixed technical weaknesses against existing frozen source V0.1
1. A selected 0.01 BTC_USDC call or put missing `ask`, crossed/locked BBO, bid/ask size below minimum, invalid zero/NaN/Inf price, timestamp > request receive time, stale >30 sec, or current contract instrument minimum >0.01 cannot be labelled valid.
2. The prospective hedge BTC_USDC-PERPETUAL BBO witness requires finite positive bid+ask, noncrossed and <=30sec causal freshness; **does not** require size in option-contract units because this is only a source witness, not executed hedge order.
3. Original bank JSONL must have exactly one record per `capture_date_utc`, valid schema `BTC_VRP_USDC_FORWARD_ENTRY_SOURCE_V0.1`, source-valid Boolean, all outcomes/secrets/order flags false, and matching receipt `receipts/vrp_usdc_forward/{date}.json`. Malformed/duplicate/invalid historical ledger = **FAIL_CLOSED** before new append.
4. If fresh public selected quotes fail source validation, keep the frozen single-capture receipt explicitly marked `source_valid:false` for audit and do not promote it. No option/expiry/strike fallback, no missing Thursday backfill, no post-outcome adjustment.
5. Original source selection, DTE 14–60 closest30, same strike nearest log-moneyness, 0.01, Thursday 08:05 UTC nominal window 08:00–08:15, quote and future outcome seal, fee/power science **unchanged**. This patch only covers quote and ledger correctness and never creates income/option PnL.

## Implementation
Copy exact code at `labs/BTC_OPTIONS_VRP_001/usdc_forward_entry_bank_v01.py` and test `test_usdc_forward_entry_bank_integrity_v01.py` from the successful independent audit branch to this canonical branch. Re-run same synthetic CI after copy. **Do not edit** `research/btc_options_vrp_v2/TRIGGER_WEEKLY_CAPTURE.txt`; no Saturday entry backfill and no GitHub cron on main. The bank remains manual source-only, no automatic Thursday capture guaranteed.

**Current gate:** One-shot Saturday source [38036299950](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/38036299950) showed a legitimate fresh BTC_USDC 0.01 call+put quote at ~298.65 USDC naked standard initial margin and ~1.9927 USDC instantaneous roundtrip modeled spread/fee cost. **Not a Thursday frozen forward entry and not tradable after-all-costs proof**. The basic weekly V2 execution question remains statistically underpowered before outcomes.

No merge to main, no orders, wallets, account reads, payment, exchange mutation or trading authority.
