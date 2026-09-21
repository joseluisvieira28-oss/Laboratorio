# STETH-REDEMPTION-BASIS-002 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-21  
Status: **FORMALLY CLOSED — DISCOVERY_INSUFFICIENT_SAMPLE**  
Branch: `steth-redemption-basis-002-discovery-closeout-v0.1`

## 1. Canonical authority

This closeout binds only the already-authorized V0.1 execution and does not alter any scientific rule.

Source Gate:
- run: `35386033845`
- source head: `dbc396c8d161bfd2ed097449d184d9fd0c69987b`
- artifact: `10563803871`
- digest: `sha256:d1c371d5dda3718bb044f9a6b2cd628d8c35cd55af8ba85040375ee903110f53`
- classification: `SOURCE_DATA_PASS`

Frozen protocol:
- `research/steth_redemption_basis_002/STETH_REDEMPTION_BASIS_002_FINAL_PRE_DISCOVERY_PROTOCOL_V0_1.md`
- protocol commit: `80c9a30d4abcedbc86a951228fb0105c1cd094e9`

Canonical Discovery execution:
- run: `35398364376`
- head: `6acb229448c61922ca2c2016feb9866ae27c18d9`
- artifact: `10571306603`
- artifact digest: `sha256:bfd278261fe006df29b65dd64fe62b956449d9d9b25eba1de9c4f357eba775b1`
- technical workflow conclusion: `success`
- scientific classification: `DISCOVERY_INSUFFICIENT_SAMPLE`

The prior run `35387691310` was a technical/provenance failure caused by RPC transport limits and produced no valid scientific classification. The canonical run above used the frozen transport-only remediation and completed successfully.

## 2. Frozen hypothesis

The V0.1 hypothesis tested whether a sufficiently large executable secondary-market stETH discount could support a positive ETH-denominated convergence payoff through:

`buy stETH with ETH -> request Lido withdrawal -> claim ETH`

after the prospectively frozen Curve haircut, queue opportunity cost, gas, protocol-risk reserve, queue mechanics and protocol-exact claim reconstruction.

No ETH directional prediction, leverage, alternate venue, alternate LST, threshold sweep or period rescue was authorized.

## 3. Frozen sample gate

The protocol required at least:

**30 completed non-overlapping hypothetical redemptions**

before promotion gates could be meaningfully adjudicated.

The canonical run produced:

- frozen daily snapshots: `596`
- signals: `2`
- completed redemptions: `2`
- operational wait failures: `0`
- right-censored positions: `0`

Therefore the sample gate failed mechanically:

`2 < 30`

and the correct frozen classification is:

**DISCOVERY_INSUFFICIENT_SAMPLE**

## 4. Diagnostics observed

The canonical receipt reported:

- mean base net ETH: `0.000173072406161847`
- median base net ETH: `0.000173072406161847`
- positive rate: `0.5`
- bootstrap 95% lower statistic reported by runner: `0.00017307240616184702`
- stress mean net ETH: `-0.02709919710712846`

These values are preserved as diagnostics only.

Because the completed sample is only 2, they MUST NOT be used to claim edge, rescue the experiment, tune thresholds, alter the clock, alter costs, expand the period, change venue, change notional or justify promotion.

## 5. Scientific decision

V0.1 is closed as:

**DISCOVERY_INSUFFICIENT_SAMPLE**

This is NOT:
- `NO_EDGE`;
- proof that the economic mechanism is false;
- `SOURCE_BLOCKED`;
- a technical failure;
- a promotion;
- evidence sufficient for a replication stage.

The experiment did not generate the prospectively required number of qualifying opportunities inside the frozen 2023-05-16 through 2024-12-31 window.

## 6. Anti-rescue boundary

Under `STETH-REDEMPTION-BASIS-002 / V0.1`, do NOT:

- lower the 30-trade sample gate;
- lower or alter the signal threshold;
- change 12:00 UTC snapshot timing;
- add intraday observations;
- change 10 ETH notional;
- change Curve venue;
- add another LST;
- relax the 14-day queue horizon;
- change base/stress cost assumptions;
- extend into 2025 or 2026;
- optimize on the two observed trades;
- reinterpret the two diagnostics as evidence of edge;
- rerun the same V0.1 in search of a different scientific answer.

A future investigation requires a separately authorized successor with a new LAB_ID and a prospectively frozen, economically defensible design. It may not be a post-outcome parameter rescue of V0.1.

## 7. Safety / governance

Canonical run evidence confirms:
- no 2025/2026 access;
- no live trading;
- no wallet access;
- no orders;
- no exchange mutation;
- no leverage deployment;
- no main merge;
- no market-direction return test.

Google Drive was not required for this closeout.

## 8. Final state

`STETH-REDEMPTION-BASIS-002 / V0.1 = FORMALLY CLOSED — DISCOVERY_INSUFFICIENT_SAMPLE`

No promotion.  
No rescue.  
No claim of edge.  
No claim of NO_EDGE.
