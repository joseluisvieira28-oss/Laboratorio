# V11 Optimism source audit — 2026-10-07

SOURCE-ONLY; V01/V02 and prior receipts preserved. Hypothesis NOT_TESTED; SOURCE_GATE_PENDING; Development 0; economic outcomes 0; 2026 closed.

Run: https://github.com/joseluisvieira28-oss/Laboratorio/actions/runs/37595077922
Head: 5474f9c286f5e38a92c036ca890f9970460b310e
Artifact ID: 11473472395; aave-gov-lt-optimism-v11
GitHub artifact digest: sha256:344786a2c64aa38d918995c5f1057e71279c2ba9f86deadd4de36c0e4ab7b7bf
RECEIPT.json SHA256: 045dc8d9ffedb056f72f625159c084b6e282b522be3d29427c4bfd62279510d5
checkpoint.json SHA256: cb65b0a493125e82922ee7da250620b6e8ef1d9ff9a39e500698899647a8011c
requests.jsonl SHA256: 5b1cee4e99779b1f35b96745e70b52fb445d2a49177e3cda61e062e16e5e1db3

## Acquisition audit
Public RPC https://mainnet.optimism.io; configurator 0x8145edddf43f50276641b55bd3ad95944510021e.
Continuous range 0–130045411; terminal timestamp 1735689599 (2024-12-31 23:59:59 UTC).
8433 accepted intervals; zero interval gaps.
10393 requests: 8463 HTTP 200, 1930 HTTP 413. Rejected ranges were bisected; 413 responses are not accepted absence.
10392 unique raw response bodies present; zero decompressed SHA256 mismatches.
64 configurator events: 45 collateral configuration, 6 eMode configuration, 10 EModeAssetCategoryChanged, 3 upgrades.
Topic 0x5bb69795b6a2ea222d73a5f8939c23471a1f85a99c7ca43c207f1b71f10c6264 is EModeAssetCategoryChanged, as specified by the acquisition code. The V10 audit's BorrowableInIsolationChanged label for this topic is a documentation error; its raw data/counts are preserved and this clarification does not alter results.

## Sequential reconstruction
15 base-LT decreases across 8 effect transactions.
2 eMode-LT decreases: category 1 9750→9500 at block 102694765 (tx 0x01580a23128ee97fdf9ddfc442ff65b5972c1f84952c7bafd213354cedde8d56), then 9500→9300 at block 121043649 (tx 0x99af268f6b4145c78bc2239bb21e84e196638704ad9a3a15dd808742535bd485).
The second eMode tx overlaps a base-LT decrease tx.
Union: 9 provisional candidate effect transactions, NOT 10 and NOT independent defensible shocks.
Governance advance anchors, definitive parameter reproduction, eMode exposure mapping and cross-chain/proposal clustering remain pending. Coverage of 2025 and Base also remains incomplete. No complete-universe sample verdict is implied.
