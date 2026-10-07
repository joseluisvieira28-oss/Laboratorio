# TMFCB V0.4 source remediation freeze

Date: 2026-10-07. Parent: 6ab03d3d486ed332eee72272fffe2197eec01c8e.
Branch: token-migration-forced-conversion-basis-001-v0.4-source-remediation-2026-10-07.

V0.1–V0.3 remain byte-for-byte authoritative. A-F, >=12 independent programmes, exclusions, economic hypothesis, and 2022–2025 scope are unchanged. No outcomes are authorized, including after a source PASS in this phase. A separate pre-outcome freeze would be required.

Source-only implementation fixes: factory log discovery does not require historical state/code availability. Query PairCreated directly, with bounded history and complete pagination. Do not interpret empty/error/null interchangeably. Pool creation alone proves creation, not executable liquidity, continuous tradability, or historical price archive coverage. No automatic FULLY_CLOSED promotion.

Investigate public RPC historical headers/receipts and creation logs; SQD archive/Portal with field projection and factory/topic allowlists; first-party deployment manifests; metadata-only Uniswap subgraphs; anonymous public archive object filenames and listing/delisting metadata. No OHLC/trade files may be downloaded. No swaps, reserves, amounts, TVL, sqrtPrice/tick, balances/accounts/wallets, private/authenticated data endpoints or money. Repository authentication is solely for authorized source code/document commits.

Factory discovery order: Uniswap V2 then V3; quote order inherited WETH, USDC, USDT, DAI. Preserve all eligible creation records, sorted by block/log index; do not choose a venue by performance. Discovery starts at factory deployment (V2 10000835; V3 12369621), ends no later than the last block before 2026, resolved by historical header timestamps. First request may use block 24000000 as a conservative 2025 upper bound, then verify its timestamp; records at/after 1767225600 are never admitted. Historical pre-2022 pool creation metadata may identify already existing venues; study events remain 2022–2025.

Any source failures describe the tested endpoint/environment/request, not universal provider incapability. Partial scans are incomplete, never NOT_FOUND. Do not run old probes: receipt responses can contain unrelated logs and old probes use latest/2026 search bounds. V0.4 retains only required metadata and does not inspect receipt logs.
