# VELOCITY FILLER SOURCE V0.2 — STRICT SCHEMA REMEDIATION PRE-SOURCE FREEZE

2026-10-31. New independent read-only source experiment, frozen BEFORE V0.2 market/API receipts. Original V0.1 source failure remains immutable: [CI #41227701534](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41227701534), SOURCE_BLOCKED_FAIL_CLOSED, STATS_MARKETS_SCHEMA_BAD.

An independently executed OFFLINE forensic based only on archived V0.1 raw payload (not new prices), [CI #41227815313](https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/41227815313), confirmed response raw hash 05c501e4894232f464154246af91964ed5a3e2cb75a1c1cfc286cac89967c1f1 and actual public GET /stats/markets wrapper keys ["success","markets"]; markets is an array of length 10 with observed fields including symbol, marketIndex, status and quoteVolume. V0.1 erroneously expected a top-level array or .data array. This is ONE structural parser fix before V0.2 sources. It does not change any trading rule, payout economics, symbol selection, timestamp, market, limit, eligibility, fee calculation, threshold or cause result-based tuning.

Frozen V0.2 collection and economic gate are otherwise BYTE-FOR-BYTE inherited from V0.1 PRE-SOURCE FREEZE:
- Exactly four public GET calls in order: /stats/markets, /market/SOL-PERP/trades?limit=100, /market/BTC-PERP/trades?limit=100, /market/ETH-PERP/trades?limit=100; 12s timeout, 2MB cap, no retry/substitution/pagination.
- Accept stats as original valid top-level list, .data list, OR previously observed official .markets list with .success=true. If .markets array missing, blocked.
- Trade feeds accepted only as a top-level list or documented .data array, each reward value nonnegative integer micro quote unit, all fields identity checked. If trade endpoint returns an undocumented structure or missing fillerReward stop SOURCE_BLOCKED, not "zero rewards."
- Historic explicit positive rewards in 7-day window, transaction identities, hard follow-up HURDLE: >=10 positive records, >=3 distinct txSig, and >=10 quote USD sum across frozen 100 most recent records per fixed market. Passing threshold still NOT a net edge; all real-user queue/race/cost/receipt/legal eligibility gates remain.
- No real orders, exchange mutation, account/wallet login, Solana private endpoints, capital, trading, Telegram, schedules, main merge, protected holds or NVIDIA overlap.
- This is FINAL parser-remediation market source run for Velocity family. If still fails, archive as SOURCE_BLOCKED and stop, no source replacement or fourth attempt; if passes but economic hurdle fails, STOP this family as too small under preselected micro-operator requirements.

Do NOT interpret any historical fillerReward as a payment earned by user or guaranteed profit. Official API field documented: https://docs.velocity.exchange/developers/data-api/glossary .
