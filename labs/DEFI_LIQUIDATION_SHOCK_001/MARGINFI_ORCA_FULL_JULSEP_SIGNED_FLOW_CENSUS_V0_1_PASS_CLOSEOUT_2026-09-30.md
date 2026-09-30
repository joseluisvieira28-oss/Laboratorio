# MARGINFI -> ORCA FULL JUL-SEP SIGNED-FLOW CENSUS V0.1 — PASS CLOSEOUT

Date: 2026-09-30
Branch: dls-marginfi-route-migration-v01

Canonical run:
36780139559

Canonical terminal artifact:
dls-marginfi-orca-julsep-signed-flow-source-v01
artifact ID 11127536853
digest sha256:4cbe2bad99237aee32d1e21c5055b17258897df6c312639678e68f15c4ae8dcb

Classification:
MARGINFI_ORCA_JULSEP_SIGNED_FLOW_SOURCE_PASS

Canonical Marginfi SOL population:
8,857

Full adjudication:
- merged adjudication count: 8,857
- missing identities: 0
- extra identities: 0
- duplicate identities: 0
- global errors: 0

Orca route coverage:
- Orca presence: 7,744
- not Orca route: 1,113
- source complete: 7,744 / 7,744 = 100%
- source evidence incomplete: 0
- direction proven: 7,717
- direction ambiguous: 27
- contradictions: 0
- exact route input amount proven: 7,717 / 7,717 = 100%

Monthly coverage:
July:
- population 865
- Orca presence 295
- direction proven 295

August:
- population 7,677
- Orca presence 7,155
- direction proven 7,128

September:
- population 315
- Orca presence 294
- direction proven 294

Decoded instruction counts:
- swap: 366
- swap_v2: 5,232
- two_hop_swap: 42
- two_hop_swap_v2: 2,108

Proven route semantic:
COLLATERAL_TO_LIABILITY_ORCA_PROVEN = 7,717

Structural conclusion:
The July-to-August route migration is confirmed at full-population scale.
Orca Whirlpools becomes the dominant post-liquidation external swap path for Marginfi SOL liquidations
in August and remains dominant in September.

This materially expands source-proven signed-flow coverage relative to the Jupiter-only route.

No market price, OHLC, return or PnL was used.

Consequence:
A separately frozen Orca market-impact family may proceed to its mandatory pre-outcome sample gate.

Firewall:
jul_sep_market_outcomes_opened=false
oct_dec_2024_opened=false
market_2025_opened=false
market_2026_opened=false
live_trading=false
orders=false
exchange_mutation=false
merge_main=false
post_decode_tuning=false
