# MEME-DIAMANTE-003 — Independent adversarial source audit and verdict
**Date:** 2026-11-18 UTC
**Final classification:** ECONOMIC **NO-GO**; SCIENTIFIC **INCONCLUSIVE**; RESEARCH DATA ACQUISITION **GO**.
**Never traded** — 0 orders, 0 purchases, 0 wallets, 0 signatures, no monetary outlay.

## Exact runs and integrity evidence
- Source receipt and schema probe: [GitHub Actions 44340933104](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44340933104), SUCCESS.
- Historical trade-print evaluation: [GitHub Actions 44341359083](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/44341359083), SUCCESS. Machine-readable results in `meme003-exploratory-results` workflow artifact. Logs include `REAL_REPLAY_RESULT=` receipts.
- `curve_paths.jsonl.gz` SHA-256: `6dfba77ddc3056d7f6d7e88fced4652b32108056ae0d1e0572ba0e4118ae5058`
- `launch_windows.jsonl.gz` SHA-256: `908ecaf196acad44e3df7e876da6eac0e9a1aa14e314a6b12c5e3b16ad08db74`
- Origin: [Tr4m0ryp/trenches-pumpfun-forward-2026-08](https://huggingface.co/datasets/Tr4m0ryp/trenches-pumpfun-forward-2026-08) — **PolyForm Noncommercial**; internal scientific investigation only. The two trade-level components cover May–Jun 2026, **not** the separate Aug 2026 observation cohort; they do not join with it.

## Reproduced numbers
| Metric | curve_paths | launch_windows | Total (events/objects only, not independent token-universe count) |
|---|---:|---:|---:|
| Mint-level objects | 1,361 | 999 | 2,360 |
| Raw chain events | 289,952 | 52,389 | 342,341 |
| Parsed eligible events | 287,819 | 52,225 | 340,044 |
| Excluded by local validator | 2,133 | 164 | 2,297 |
| Structural momentum-only signals | 13 | 23 | 36 |
| Wallet-filtered signals | **0** | **2** | **2** |
| Wallet signals with observable market-entry and market-exit price prints | **0** | **0** | **0** |

The two wallet-filtered signals: **1 ENTRY_UNOBSERVED** and **1 EXIT_UNOBSERVED**. We did not impute either a success or a failure.

Momentum-only: 4 print-only outcomes from 13 signals in the first dataset; 5 from 23 in the second. The remaining 27 are unobserved/censored or blocked by reserve threshold. This is an extreme selection problem: the tempting 4/4 positive prints in dataset 1 are **not** a 100% win rate; they exclude other non-executable/unknown outcomes.

Source/data statuses: 37 `error:RpcClientError` rows in curve_paths; 22 `error:RpcRateLimitError` and five `truncated` in launch_windows. The 'excluded events' count describes what the local parser rejected and should not be represented as all necessarily defective source rows. In-block ordering ambiguity remains for 1,857 and 891 same-slot/tx-index observations respectively where a unique sequence/ordinal is unavailable or uncertain.

## Scientific design barriers
1. The **original frozen strategy** requires >=$20,000 tradeable liquidity, >=$50 buyer amounts, >=$1,200 buy volume. This trade sample has SOL reserves and virtual curve ratios, **not** independent marketable USD liquidity; the audit uses exploratory **5 SOL real reserve / >=0.1 SOL per buyer / >=2 SOL buys**. **NOT the same frozen strategy**.
2. The age clock is the first retained event, not necessarily token creation. Data are retrospective and entry-delay measurements start at block time, **not live receipt time**.
3. We use ordered Solana prints and virtual reserve ratios. They are not executable quotes, cannot establish capacity, slippage, priority/MEV, failed orders, actual exit liquidity or realized P&L.
4. Intra-block sequence and multi-leg transactions need deterministic unique IDs. The MEME-DIAMANTE-002 input dedup by (mint, signature, side) can drop legitimate multiple fills. Also sorting by timestamp and signature lexicographic order can differ from chain execution order.
5. The source is curated/selected, not the whole launch universe. It lacks the independent 30-day held-out replay needed for scientific/economic GO. Absence of signals from this population **does not prove** no edge exists anywhere in memecoins.
6. Costs 1.7% per side + 2% modeled slippage are **stress assumptions**, not proven May–Jun 2026 historical fee schedules. The apparent print profits have no economic meaning.
7. **DIGUI-007 is not interchangeable**: it samples 2 GeckoTerminal new-pool pages every 2h, not the complete Pump.fun mint universe nor a sub-minute event/trade feed. It cannot validate the frozen second-wave strategy.

## Action
- **NO-GO** live trading, capital deployment, automated bots, copytrading or strategy marketing on these findings.
- Keep this PR **DRAFT, unmerged**, research-only. No schedule was activated for MEME-DIAMANTE-003.
- A new economic gate would require authorized complete and temporally indexed launched tokens, source receipts at detection, independent executable bids/asks/liquidity by venue, failed trades, actual historical fees and strict forward validation. If these data are unavailable at zero budget, **stop this hypothesis** rather than claim an edge from incomplete prints.
- Our original two-signal hypothesis has **0 independently liquidated economic outcomes**. This is a *decisive funding NO-GO* but scientifically **inconclusive**, not a universal theorem that all memecoin trading has no edge.

Scientific honesty is the deliverable: 0 proven profits.
