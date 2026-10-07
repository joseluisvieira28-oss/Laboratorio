# V14 Optimism Governance Lineage Audit — 2026-10-07

## Scope
Source-only governance-lineage work over the nine provisional Optimism V11 LT-decrease candidate transactions. This phase proves pre-effect governance lineage without opening borrower or economic outcomes.

## V14 authority
- Probe commit: `1f31e4ada9b0d055673b8be98099bd4da737773e`
- Workflow run: `37649228818`
- Workflow conclusion: **SUCCESS**
- Artifact ID: `11495287424`
- Artifact digest: `sha256:259dbff571fce1b872a455fde4a54714168d88da1fb6dcd7c37d2ebe367edc75`

## Result
- V11 provisional candidates: **9**
- Governance V3 candidates with unique `PayloadExecuted`: **8**
- Candidates with recovered pre-effect `PayloadQueued` linkage: **8 / 8**
- Queue-to-effect lag: approximately **86,404–86,412 seconds** per linked payload
- Payload action targets recovered: **8 / 8**
- Target bytecode at the queue block SHA256-hashed: **8 / 8**
- Exact parameter reproduction from pre-signal payload semantics: **PENDING**
- Fully source-gated independent shocks: **0**
- Economic outcomes opened: **0**

## V3 transaction → payload → target → governance cluster seed

| Effect transaction | Payload ID | Target | Proposal/report cluster |
|---|---:|---|---|
| `0x22c2eb7b02ae215657fdccfc442ff65b5972c1f84952c7bafd213354cedde8d56` | 12 | `0x2a1cb7834e36b318c5ad1939c45ce3e365b92a7d` | V3-19 — Optimism risk parameters |
| `0x32d60434b74e59c69ecf7a06d38b67527245aff9c2e5eef7e3bc5da3e30fbac9` | 28 | `0xd1f5433e094ca4c247a578c079b6602e0879df71` | V3-87 — multichain DAI |
| `0x367cce6e426cdc69a071afeff846189b69db43f101163fb2710399f51c40d3f4` | 7 | `0xcab466a6bed466316b20151c9526afc7654d00f2` | 409 — multichain native USDC |
| `0x50097b7a4ae1464f7c78b3be86da487b15a4aa8f9e7b95784844a4c279145b1d` | 3 | `0xf8bc2a699559c96d48cf1e6f70aa2e67508c2ae9` | 376 — multichain MAI deprecation |
| `0x6d6f4750a7109b7322de3782ffdd6f7e6a99a079242a7929481802f7094a026f` | 30 | `0x7b55bdbade8b990b1ca58d6b7b1f856e4d66a03f` | V3-100 — multichain LT/LTV reductions step 2 |
| `0x99af268f6b4145c78bc2239bb21e84e196638704ad9a3a15dd808742535bd485` | 33 | `0x5594521a5132faf674552cfc6387b75cf10f9924` | V3-114 — Optimism sUSD risk parameters |
| `0xa8ecf8b94a86aac1e68db482e01282cc4e66a051cc7c97d816ed293443db9538` | 24 | `0x11b8ceb0d53c3810959be617b5c22fa63e2181ac` | V3-71 — multichain stablecoin LT/LTV |
| `0xf646ec46e06384edbed76231bbb0fb92ea4d5de33f083079721684ca14047a50` | 50 | `0x0caac2579cb7fa10cc3bdcff88c0f32fe5e6152c` | V3-173 — multichain Chaos Labs LT/LTV alignment |

The cluster labels above are governance grouping seeds, not final independent-shock counts. The multichain reports show that V3-87, 409, 376, V3-100, V3-71, and V3-173 coordinate changes on multiple chains; matching chain effects from the same governance decision must therefore be collapsed before the sample-size verdict.

## Legacy candidate
The remaining Optimism V11 candidate is:
- effect transaction: `0x01580a23128ee97fdf9ddfc442ff65b5972c1f84952c7bafd213354cedde8d56`
- effect block: `102,694,765`
- eMode LT: `9750 → 9500`
- legacy executor observed: `0x7d9103572be58ffe99dc390e8246f02dcae6f611`
- event semantics: `ActionsSetExecuted(uint256,address,bytes[])`
- action-set ID: **18**

V14.1 attempted the legacy Governance V2 queue linkage at commit `0bbe149c50ef55a88a7c7609a4849ed38b68af00`, run `37649959172`. The run also contained a terminal print bug and did not recover a unique expected queue event with the initial range-search method. This is classified here as **OPERATIVELY_UNRESOLVED**, not as final `SOURCE_BLOCKED`; the historical action-set state remains a legitimate unresolved source path.

## Scientific classification
- `SOURCE_GATE_PENDING`
- `NOT_TESTED`
- no outcome data opened
- no promotion to edge
- no independent shock count frozen yet

Next legitimate work is exact pre-signal parameter reproduction, legacy V2 queue recovery, matching proposal clusters across other chains, and completion of Base / 2025 acquisition.
