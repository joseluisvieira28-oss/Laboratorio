# TVSC-001 — FOLLOW-UP NOVELTY SCREEN 01

Date: 2026-09-23
Authority: CRYPTO LAB Governance V4 / Death Policy
Outcome access used for this screen: only the already-closed TVSQZ-001 Discovery result.

## Purpose

Evaluate whether the next highly popular TradingView candidates are scientifically eligible as new Crypto Lab experiments before any new market outcomes are opened.

## TVATR-UT-001 — UT Bot

TradingView mechanism: ATR-based adaptive trailing stop / state flip.

Repository contamination:
- CIGL-ATR-01 is already prospectively frozen around Wilder ATR impulse-continuation.
- CIGL-SUPERTREND-01 is already prospectively frozen around ATR bands, recursive trailing state and direction flips.

V4 novelty decision: **REJECT AS NEW LAB IN CURRENT FORM**.

Reason: UT Bot is another price/ATR trailing-state transformation. Popularity and a different formula/name do not provide a materially new causal information channel. Testing arbitrary UT Bot parameters after seeing existing ATR/SuperTrend work would be generic indicator permutation, explicitly disfavored by V4.

## TVML-LOR-001 — Lorentzian Classification

TradingView mechanism: Approximate Nearest Neighbours with Lorentzian distance over a configurable feature set (default features include RSI, WaveTrend, CCI, ADX), plus volatility/regime/kernel filters.

V4 novelty decision: **DO NOT OPEN OUTCOMES / SOURCE-AND-METHOD REVIEW ONLY**.

Reason:
- the default feature space is composed predominantly of transformations of the same OHLC price history already heavily covered;
- multiple configurable features, filters, neighbor count, max-bars-back, kernel settings and exits create a large researcher's-degrees-of-freedom surface;
- TradingView's published defaults are stated by the author as selected/optimized from prior testing, so their historical backtest cannot be treated as fresh evidence for Crypto Lab;
- Lorentzian distance itself is algorithmic novelty, but V4 requires material causal novelty, not merely a different transformation, before a new lab may inherit protected validation resources.

A future Lorentzian experiment would need an independently justified causal feature space or a pre-registered benchmark question (Lorentzian vs Euclidean on an untouched corpus) that is not framed as a strategy rescue.

## TVSTACK-001 — QQE + SSL Hybrid + Waddah Attar Explosion

TradingView mechanism: stack of price-derived trend, RSI/ATR momentum, and volatility/explosion filters.

V4 novelty decision: **REJECT AS NEW LAB IN CURRENT FORM**.

Reason:
- direct indicator stacking;
- components overlap already-covered RSI/ATR/trend/volatility families;
- Classic Indicators Gap Lab explicitly forbids indicator stacking as a rescue;
- no materially independent information source is added.

## Consequence

After TVSQZ-001 closed NO_EDGE, the next legitimate TradingView mine should not be another rearrangement of OHLC-derived indicators.

Priority shifts to TradingView strategies/scripts whose signal depends on a materially independent information channel that can be sourced point-in-time, for example:
- open interest / derivatives positioning;
- funding / basis;
- volume delta / aggressive flow with defensible source semantics;
- liquidation mechanics;
- options surface / volatility state;
- venue/session auction state where the causal clock is reproducible.

These families must still pass anti-duplication against existing Crypto Lab lineages before a new LAB_ID is frozen.
