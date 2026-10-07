# BTC-OPTIONS-VRP-001 V2 — 30D LINEAR USDC TWO-LEG LIQUIDITY WITNESS FREEZE V0.1
Date: 2026-10-07
Status: SOURCE-ONLY / NO ECONOMIC OUTCOMES

Purpose: determine whether 2025 public BTC_USDC option trade history contains real trades on both legs of a deterministic approximately-30D same-strike call+put pair, regardless of aggressor direction.

This does NOT assume the operator could obtain a passive fill. A BUY-direction public trade is only evidence that a seller existed on the other side. Therefore PASS here means LIQUIDITY_WITNESS_PRESENT, not executable strategy PASS.

Frozen anchors: every Thursday 08:00 UTC in 2025.
Frozen entry window: 08:00–12:00 UTC.
Frozen expiry: 25–35 DTE, choose nearest 30.
Frozen pair: same expiry, same strike, strike nearest contemporaneous index using only trade-time index fields.
Minimum observed trade amount: 0.01 contract on each leg.
Selection: first qualifying real trade per instrument regardless of BUY/SELL.

Retain only source identity/timestamp/direction/amount/trade ID/metadata and hashes.
Do not retain price, IV, settlement, future path, returns or PnL.

Classification:
- LIQUIDITY_WITNESS_PRESENT if >=24/52 anchors have a deterministic two-leg pair;
- LIQUIDITY_WITNESS_SPARSE otherwise.
No performance claim is allowed.
