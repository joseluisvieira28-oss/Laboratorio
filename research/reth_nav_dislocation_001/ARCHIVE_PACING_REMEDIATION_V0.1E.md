# RETH-NAV-DISLOCATION-001 — ARCHIVE PACING REMEDIATION V0.1E

Frozen: 2026-09-26
Scope: transport pacing only.

Evidence:
- direct-call census V0.1 lost 105/556 points;
- low-concurrency V0.1A still failed with a deterministic 7-point cadence;
- V0.1C reduces archive state traffic to one Multicall3 eth_call per scientific point.

Final pacing rule:
- minimum 1.5 seconds between consecutive scientific points that hit the archive RPC;
- retry backoff = 2 seconds * attempt number;
- maximum attempts per point remains 10;
- header calls remain on PublicNode and do not consume the archive quota.

UNCHANGED:
- all block numbers;
- all source addresses;
- EIP-1898 blockHash pinning;
- q05/q95;
- Discovery/OOS/holdout partitions;
- sample gates;
- mechanism horizons;
- all outcome firewalls.

No scientific or promotion credit is attached to pacing.
