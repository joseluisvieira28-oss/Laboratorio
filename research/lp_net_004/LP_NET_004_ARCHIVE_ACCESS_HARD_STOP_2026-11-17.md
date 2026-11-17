# LP-NET-004 — Post-closeout historical pool feeGrowth archive access verdict
Dated 2026-11-17. **No trading or capital.**

After the nine-pool first frozen snapshot (run [44180139682](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44180139682)), the 9 fixed $1k/$5k/$20k × ±0.10%/±0.25%/±0.50% current-spot static scenarios, and 719 past closed hourly candles (run [44181037754](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44181037754)), we attempted a **more adversarial** check of actual Uniswap v3 pool GLOBAL 24h fee growth.

Implementation `research/lp_net_004/fee_growth_24h_block_pinned.py` probes two exact Arbitrum mainnet blocks approximately 24h apart; checks chain ID 42161, freezes each `eth_call` block tag, reads `feeGrowthGlobal0X128`, `feeGrowthGlobal1X128`, `slot0`, and active L, then compares cumulative feeGrowth **per raw L** with hypothetical $1k/$5k/$20k virtual minted L. This is deliberately **not** a `feeGrowthInside` simulation and even complete global data would not prove virtual fees: tick crossing, positions actually active, dilution and future state remain unknown.

GitHub run [44181851826](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44181851826), artifact 14372043069: **SOURCE_BLOCKED** — `https://arb1.arbitrum.io/rpc` returned historical state missing trie node for past `eth_call`. We did not invent fee growth or substitute market volume.

Retry in [run 44182150392](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44182150392), artifact 14373056722: **SOURCE_BLOCKED** again. Official Arbitrum public RPC responded `-32000 historical state ...` and `https://arbitrum-one-rpc.publicnode.com` responded HTTP **403 Forbidden**. No real feeGrowth per LP was computed. **23/23 offline regression tests PASSED; green CI means transport/code safety, NOT economic success.**

Original 719/720 historical candles' evidence remains intact in **artifact 14371173814**, run 44181037754; later independent public OHLCV retries sometimes returned HTTP 429 (provider quota), which cannot retroactively invalidate the earlier hashed source.

**Scientific verdict remains unchanged:**
- Blockchain contracts observed for 9/9 pool addresses, feeProtocol `0x44`, onchain active L and tick, gas price, and token identities; ETH/USD spot verified.
- Among frozen nine, only Arbitrum USDC/USDT 1bp passed market-and-contract **SOURCE** screen at original T0.
- Original T0 $5k static current-tick volume share: ±0.10% = **$11.49** gross fees/30 days (simple annual 2.795%), ±0.25% = **$4.60** (simple annual 1.120%), ±0.50% = **$2.30** (simple annual 0.561%). **Not fees actually accrued**; upper current-day fee assumptions are not promises or strict bounds over changing liquidity.
- 9/9 fixed static scenarios have fee-only simple annualised extrapolations below an assumed 4%/year cash comparison; additionally there are L1 posting fees and risk/IL not measured.
- **NO_LIVE_GO**. No proof of 7/30-day forward economic edge, no deposit, no capital.
- Further archived data requires a legitimate archive-capable RPC or independently extracted onchain tick events; do not procure paid services without a distinct user budget approval. If no source, terminate this lane and prioritize a different economic hypothesis.
