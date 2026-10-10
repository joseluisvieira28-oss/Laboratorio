# HYPE-BUYBACK-FLOW-001 — SOURCE ECONOMICS / RETENTION CENSUS FREEZE V0.1.3
2026-10-10 UTC; PRE-CENSUS, SOURCE-ONLY.

After 42-character official Assistance Fund system-address correction in commit 6b634e8, corrected official `userFillsByTime` transport returned 451 exact @107 BUY fills in trailing 24h (run 38042643639); 90-day ago slice returned empty, consistent with 10k fill retention. `userFills` returned 2,000 recent rows, not the full history. The 451 is a 24-hour *fill count*, not 451 independent market-impact episodes. No fills from the old truncated 36/40-character address count. No prices/returns looked up.
GitHub source probe receipt raw sha256 of 24h: 4a9346a4d54a5d815bf2b60fe518c253d05e34b102bc7429b417b2405cc2b66b.

**PRECOMMITTED SOURCE-ONLY FOLLOWUP, BEFORE CALLING ENDPOINTS**
- Evaluate fixed, non-overlapping UTC last 7 daily windows [d-1,d], ... [d-7,d-6] based on probe UTC now; source path `userFillsByTime` exact 42-char official fund and `aggregateByTime=false`. Do not paginate beyond 2000 in a day; a 2000-response is CENSORED. Dedupe by (tid, hash), reject unknown side/coin/missing sz,px.
- Retention sentinel noncontiguous windows day indexes 14, 21, 28, 35, 60, 90 UTC days ago, one 24h window each. A zero count at age 90 means unavailable under the 10k cap, NOT no buys.
- Causal source descriptive counts: accepted BUY fills, sum(sz) HYPE, sum(sz*px) USDC **historical transaction notional**, median inter-fill seconds, time range, maker/taker `crossed` split; fraction 2k limit and duplicates. No price trend, no future outcomes, no alpha thresholds.
- Current public `spotMetaAndAssetCtxs` to read full-market spot day notional volume for *same exact @107 pair* and confirm dynamic mapping; single `l2Book` snapshot for @107 recording precise capture time, ordered bid/ask and shares available at best 5 levels (market-feasibility only). No quote-based profits; snapshot not historical route.
- Market comparison: trailing 24h AF buy notional vs spotCtx dayNtlVlm ONLY as contextual ratio with potential windows mismatch warning. Liquidity at quote snapshot doesn't prove capacity at every time.
- Preserve raw HTTP bodies with SHA256, first-seen wall-clock, HTTP status/latency, immutable GitHub Action artifact; no private API/wallet/keys, paid S3, orders, cash spend or Render.
- Same fixed 90d/60 active-day, provenance, historical executable quote source, and PIT historical latency PASS gates as SOURCE_GATE_AUTHORITY_V0_1.md. This source-only followup cannot change them or promote Discovery.
- 2026 protected market PRICE outcomes not touched; if later constructing a hypothesis freeze, start fresh untouched forward clock.

This correction does not reopen unrelated old closed economic MVEs. Transport is now proven recent, not historical.
