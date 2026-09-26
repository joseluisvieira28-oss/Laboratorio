# CBBTC-ETH-MINT-BURN-FLOW-001 — ADAPTIVE ETH_GETLOGS TRANSPORT REMEDIATION V0.1C

Frozen: 2026-09-27
Parent: SOURCE_GATE_FREEZE_V0.1

Scope: transport/pagination only.

Ethereum JSON-RPC does not standardize a maximum eth_getLogs range and public RPC providers may enforce block-span, result-count, or timeout ceilings.

The frozen source gate already explicitly permits reducing eth_getLogs block spans and deterministic retries/backoff.

## Remediation

Preserve the original logical requested interval exactly.

For each logical 20,000-block segment:
1. attempt the exact segment with the frozen address/topics;
2. retry transient failures;
3. if still rejected and span > 1 block, split the interval exactly at midpoint;
4. recursively query left and right halves;
5. concatenate all returned logs;
6. preserve exact block/log provenance;
7. do not skip any block.

A single-block interval that still fails after retries is a hard source error.

## Unchanged

- contract;
- two fixed source windows;
- Transfer topic;
- zero-address mint/burn topics;
- block boundaries;
- decode rules;
- duplicate gate;
- SOURCE_PASS criteria;
- outcome closure.

This remediation changes no scientific sample and earns zero promotion credit.
