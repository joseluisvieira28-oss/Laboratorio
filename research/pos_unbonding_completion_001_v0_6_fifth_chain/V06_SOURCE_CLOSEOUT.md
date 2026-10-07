# POS-UNBONDING-COMPLETION-SUPPLY-RELEASE-001 — V0.6 SOURCE CLOSEOUT

Date: 2026-10-07
Branch: pos-unbonding-completion-001-v0.6-fifth-chain-expansion-2026-10-07
Freeze: e8a3e4b4eb07142d40abc781230235f7ea9d3c53
Market outcomes opened: NO
Main changed: NO

## Verdict

**SOURCE_HISTORICAL_COVERAGE_BLOCKED**

Not NO_EDGE. Economic hypothesis remains untested.

## V0.6 result

Prospectively frozen candidates CRO -> EVMOS -> JUNO were tested only for historical source capability before any candidate completion-event census.

- CRO: official RPC proved historical raw blocks including H=10,000,000 (2023-02-17) and H=15,000,000 (2023-12-13), but tested independent public RPCs did not reproduce those historical heights.
- EVMOS: no two-source historical fixed-height pair established.
- JUNO: no two-source historical fixed-height pair established.

A separate public historical-explorer lead was tested:
- archive-explorer.cudos.org publicly lists Crypto.org Chain and Evmos in its frontend.
- its public GraphQL endpoint is live and exposes block/unbonding schema.
- the tested GraphQL backend did not contain CRO H=15,000,000 and therefore was not promoted as CRO Source B.
- no unbonding event counts were queried from that GraphQL source.

## Cumulative source-remediation finding

Across V0.3-V0.6:
- known-height raw block and block_results reconstruction is proven;
- ATOM and DYDX have dual independent historical block-index evidence in V0.4;
- OSMO and TIA have strong historical raw sources but no matching second completion index in the tested route;
- multiple additional chains expose one historical archive, but the required second independently operated public/free historical path could not be reproduced for a fifth comparable chain;
- historical queue-subspace iteration was explicitly invalidated after returning present/future queue contents at old response heights.

The >=5-chain two-source gate therefore remains unsatisfied.

## Gates

G1 >=5 comparable chains: source-qualified set insufficient.
G2 two independent historical paths per selected chain: FAIL for a five-chain set.
G3 complete five-chain census: NOT AUTHORIZED / NOT RUN.
G4 full census-scale lifecycle reconciliation: NOT RUN.
G5 >=40 material chain-days TOTAL across >=5 chains: UNKNOWN.
G6 market-source capability: no outcome values opened.
Scientific firewall: PASS.

Materiality remains 10 bps and sample bar remains >=40 TOTAL across >=5 chains.

## Reopening rule

Reopen only on genuinely new pre-outcome capability, for example:
- a second independently operated archive for one of the near-pass chains;
- a public/free historical bulk export with independently verifiable canonical hashes;
- a multi-chain historical index whose chain-specific backend can be mapped and reproduced;
- restoration of an independent archive provider covering the frozen interval.

Do not reopen by adding chains indefinitely after source results, reducing the five-chain requirement, accepting same-operator endpoints as independent, or opening prices first.

No PRE-OUTCOME analysis is authorized.
