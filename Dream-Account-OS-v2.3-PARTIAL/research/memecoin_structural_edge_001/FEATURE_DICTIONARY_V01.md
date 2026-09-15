# MSEL-001 — FEATURE DICTIONARY V0.1

Status: PRE-OUTCOME FEATURE FREEZE
Branch: `memecoin-structural-edge-v0.1`
Date: 2026-09-15

## 1. Scope

Freeze the first transparent feature set for the T+5m Killer Filter before future outcomes are opened. All features must be computable using information timestamped <= T+5m.

No feature below is evidence of edge by itself.

## 2. Core buyer-diffusion features

- `unique_buyers_1m`, `unique_buyers_3m`, `unique_buyers_5m`: distinct economic buyer wallets observed by snapshot.
- `new_buyers_3_to_5m`: buyers first appearing after T+3m and by T+5m.
- `buyer_arrival_rate_5m`: unique buyers / elapsed seconds.
- `buyers_per_trade_5m`: unique buyers / buy transaction count.
- `repeat_buyer_share_5m`: share of buy transactions from wallets that have already bought this mint earlier in the first 5m.
- `buyer_size_median_quote_5m`: median quote amount per economic buyer.
- `buyer_size_p90_p50_ratio_5m`: concentration of buyer size distribution.

## 3. Raw-holder concentration

Computed at the snapshot after excluding protocol-owned bonding-curve/pool accounts under the frozen exclusion rule:
- `top1_holder_share_5m`
- `top3_holder_share_5m`
- `top5_holder_share_5m`
- `top10_holder_share_5m`
- `holder_hhi_5m`
- `holder_gini_5m`

Creator holdings are NOT automatically excluded; they are separately flagged.

## 4. Economic concentration / wallet linkage

Only point-in-time relationships are allowed:
- `same_funder_cluster_share_5m`: token share held by wallets linked through a common funding wallet visible before T+5m.
- `largest_funder_cluster_share_5m`
- `linked_top10_share_5m`: top-holder share after merging only approved point-in-time wallet links.
- `creator_linked_holder_share_5m`: holdings in wallets linked to creator using funding/activity evidence available by T+5m.
- `cluster_count_5m`: number of independent approved economic clusters among holders.

Hard prohibition: do not build clusters using transactions occurring after T+5m or later launches.

## 5. Creator/deployer history

All historical statistics use only launches strictly prior to current launch time and only outcome windows already fully elapsed before current launch.

- `creator_prior_launch_count`
- `creator_prior_completed_curve_count`
- `creator_prior_completion_rate`
- `creator_prior_early_sell_count`
- `creator_wallet_age_seconds`
- `creator_prior_distinct_mints_interacted`

If creator identity is ambiguous, all creator-derived features are NULL and accompanied by a missingness flag. Never substitute payer/signature wallet.

## 6. Flow-quality features

- `buy_count_5m`
- `sell_count_5m`
- `unique_sellers_5m`
- `gross_buy_quote_5m`
- `gross_sell_quote_5m`
- `net_quote_flow_5m`
- `buy_sell_notional_ratio_5m`
- `volume_per_unique_buyer_5m`
- `top1_volume_share_5m`
- `top5_volume_share_5m`
- `round_trip_wallet_count_5m`: wallets that both buy and sell by T+5m.
- `rapid_round_trip_share_5m`: share of volume in same-wallet buy->sell sequences within a frozen short interval, interval to be set from parser precision before outcome opening.

## 7. Curve-state features

Derived from authoritative curve account/event state at or immediately before T+5m:
- `curve_complete_5m`
- `real_token_reserve_fraction_5m`
- `real_sol_reserves_5m`
- `virtual_token_reserves_5m`
- `virtual_sol_reserves_5m`
- `curve_progress_5m`: mechanically defined from remaining real token reserves relative to initial real reserves for that historical schema regime.
- `buy_price_impact_reference_5m`: deterministic quoted impact for a pre-frozen reference notional under the historical curve formula.

No future migration flag is allowed.

## 8. Creator / insider activity in current launch

- `creator_token_share_5m`
- `creator_net_token_change_5m`
- `creator_sell_flag_5m`
- `creator_linked_sell_flag_5m`
- `early_buyer_top5_share_5m`: holdings share of first five independent buyers/clusters.
- `first_minute_buyer_share_5m`: share held at T+5m by buyers first entering in T+1m.

## 9. Simple control features

Included only to test whether structural features add value beyond chart-like information:
- `price_return_1m_to_5m`
- `price_return_create_to_5m`
- `trade_count_5m`
- `raw_volume_5m`
- `curve_progress_5m`

No RSI/MACD/Bollinger family in MVE.

## 10. Missingness flags

For every feature family that can be unavailable due to source/schema limitations, create explicit missingness indicators. Missing values must never be silently imputed from future state.

## 11. Forbidden features before T+5m outcome opening

Forbidden in the T+5m Killer Filter:
- eventual graduation/migration status
- post-T+5m holder counts/balances
- later social follower/engagement snapshots
- later wallet profitability labels
- later creator reputation
- DEX liquidity created after T+5m
- future token price/high/low/market cap
- manually curated rug/winner lists created after outcomes
- any feature whose source timestamp cannot be proven <= decision time

## 12. Baseline model freeze

Primary comparison families after data gate:
1. price/volume-only control;
2. transparent structural rules;
3. regularized logistic regression;
4. shallow decision tree.

Complex ML remains LOCKED until the simple structural feature set demonstrates temporal OOS value.

## 13. Feature promotion rule

A feature can enter the production MVE only if:
- exact formula is documented;
- required raw fields have timestamp authority;
- historical schema compatibility is known;
- unit test exists on manually reconciled pilot launches;
- missingness is explicit;
- no future-derived labels/clusters are used.
