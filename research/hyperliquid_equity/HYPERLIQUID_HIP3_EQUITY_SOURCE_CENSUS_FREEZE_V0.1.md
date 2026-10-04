# HYPERLIQUID HIP-3 U.S. EQUITY TARGET SOURCE CENSUS V0.1

Date: 2026-10-04
Status: SOURCE-ONLY / PRE-OUTCOME

Purpose:
- enumerate every public Hyperliquid perpetual DEX via `perpDexs`;
- fetch public `meta`, `metaAndAssetCtxs`, `perpDexStatus` and `perpDexLimits` for each HIP-3 DEX;
- identify exact stock/equity perps matching the predeclared ticker set:
  NVDA, TSLA, AAPL, PLTR, META, AMZN, MSFT, AMD, NFLX, BABA, GOOGL, ORCL;
- verify current public L2 availability;
- verify public 1-minute candle transport on source-only date 2026-10-03;
- preserve raw fee/growth/deployer metadata when exposed by public info endpoints.

No account-specific info endpoint is allowed.
No wallet address is supplied.
No orders, signing, exchange actions or live trading.

No return, lead-lag, basis, direction, win/loss or PnL is computed.

The source-verification date 2026-10-03 is burned from any later outcome sample.

The census must not assume a coin exists from its name. Only returned Hyperliquid metadata can establish a binding.

Fee feasibility must distinguish:
- protocol/base fee schedule documented by Hyperliquid;
- DEX/deployer fee scale or growth mode when publicly exposed;
- unknown pair-specific effective fee when not provable without account-specific state.
