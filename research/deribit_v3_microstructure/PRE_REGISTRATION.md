# Deribit V3 — Microstructure eligibility study (PRE-REGISTRATION)
Date: 2026-11-05 UTC. Status: PROTOCOL ONLY; no observations collected under V3.
Parent: draft PR #340 Economic Proof Engine V1; original V2 FREEZE remains immutable.
Safety: READ-ONLY market-data research. No orders (including testnet), API credentials, paid services, scheduling, workflows, merges, or changes to V2 collector.

## Research question
Does V2's <=8% instantaneous round-trip liquidity gate systematically reject otherwise economically plausible hold-to-expiry BTC_USDC daily ATM long straddles? This study diagnoses eligibility and execution only. It cannot prove alpha or authorize LIVE.

## Frozen primary cohort
Collect 20 *technically valid* daily snapshots at the V2's original 08:05–08:10 UTC window, next-day 08:00 UTC expiry, ATM strike, 0.01 BTC per leg, <=1s leg skew, <=1% moneyness, and depth >=5x size, preserving original V2 definitions. Count all attempted sessions separately. Do not replace invalid sessions without retaining their rejection records. Use a fixed, deterministic single snapshot selection rule from V2. No backfilling missing snapshots as prospective. Persist raw public responses and SHA-256; record timestamp, quote age, instrument IDs, expiry, strike, best bid/ask, full book depth, contract specs, fee schedule version, and validity reasons.

## Paired diagnostics per valid snapshot
A. V2 control: compute and record frozen full spread + four trading fees, denominator premium ask, <=8% pass/fail. Do not edit original code/threshold.
B. Hold-to-expiry cash-flow: ask fill for both legs + entry fees + tick/slippage assumption; terminal intrinsic value less actual applicable delivery/settlement fees. Distinguish observable quote from future settlement. Flag unresolved linear daily delivery fee as BLOCKER rather than assuming zero.
C. Shadow combo: log whether a genuinely tradable combo quote/book exists at timestamp and sufficient depth, with fees and atomic execution; absent quote = NO_QUOTE, never invented savings.
D. Shadow maker: record post-only limit price, quote and book changes needed to infer queue priority, and fill status UNKNOWN/NOT_FILLED unless demonstrable from conservative evidence. Never count a theoretical bid fill as executed.
E. Stress: 0/1/2 ticks adverse per leg, fees as published, +25%/+50% spread widening, stale quote and depth failure; separate mechanical diagnostics from admissible P1 trades.
F. Controls: paired unconditional C0 at identical date/size/quotes and actual settlement; no lookahead in forecast, no cherry-picked snapshots.

## Minimum fields
session_utc, source_hashes, valid_technical, reject_reason, call/put IDs, bid/ask and size/depth, quote_timestamp, quote_age_ms, skew_ms, spot, strike, expiry, ask_premium_usdc, full_spread_usdc, entry_fees_usdc, hypothetical_exit_fees_usdc, v2_friction_pct, v2_gate_pass, delivery_fee_status, hold_to_expiry_cost_usdc, settlement_value_usdc, net_pnl_usdc, combo_quote_status, combo_executable_cost_usdc, maker_fill_status, maker_cost_if_filled_usdc, stress_results, P1_signal, C0_result, precommit_hash.

## Decision rules (precommitted management thresholds, NOT alpha significance)
At 20 technically valid sessions:
- <4/20 pass the original <=8% V2 gate: mark current V2 operationally TOO_RARE and stop prioritizing a six-month V2 run pending review. This is not evidence of no alpha.
- >=4/20 pass: continue prospective V2 under original scientific gates, without promoting to live.
- Any unresolved contract settlement/delivery fee or unverified combo economics: BLOCK relevant economic conclusion.
- Combo/maker alternatives remain exploratory unless verified executable; no automatic V3 strategy promotion. Any candidate change requires new freeze and fresh OOS cohort.
At 60 technically valid liquidity sessions, estimate P1 selection rate and feasibility of collecting >=60 independent OOS P1 observations within 365 calendar days; document uncertainty and correlation. If implausible, stop prioritizing for insufficient opportunity rate.
Original V2 validation (20+20 development/confirmation, >=120 OOS, >=60 P1, >=180 days/six months, positive lower confidence bound vs C0 and drawdown/cost stress) remains authoritative.

## Required deliverables
Machine-readable per-attempt ledger; immutable raw-response hashes; paired per-session cost decomposition; reject-reason waterfall; scenario sensitivity; maker/combo evidence quality; fee reconciliation citing product-specific Deribit terms; sample-size/selection-rate intervals; audit against Economic Proof Engine V1; clear KEEP / PIVOT / KILL recommendation. No PASS based on software tests alone.

## Known baseline (not part of V3 cohort)
03 Nov 2026 invalid synchronization; 04 Nov 13.959579% V2 friction; 05 Nov 17.599301%, both >8%; 0 eligible P1 and 0 settlement. Exploratory 02 Nov is excluded from prospective results.
