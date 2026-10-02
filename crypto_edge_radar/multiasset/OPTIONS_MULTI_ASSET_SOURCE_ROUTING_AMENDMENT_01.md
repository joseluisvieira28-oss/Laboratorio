# OPTIONS MULTI-ASSET — SOURCE ROUTING AMENDMENT 01

Date: 2026-10-02
Status: FROZEN BEFORE RERUN
Scope: technical source routing only; no outcome access; no scientific threshold change.

## Finding

The first source-gate run queried the Deribit historical currency route using the underlying asset symbol for all three hooks.

That is correct for ETH inverse options, but SOL and XRP options in the target historical period are linear USDC-settled instruments. Their canonical symbols use:

- SOL_USDC-DDMMMYY-STRIKE-SIDE
- XRP_USDC-DDMMMYY-STRIKE-SIDE

The historical currency-scoped trade route therefore needs the USDC settlement-currency stream for these linear products, followed by a strict target-instrument prefix filter.

## Frozen routing correction

ETH:
- request currency: ETH
- accepted instrument prefix: ETH-
- no ETH_USDC substitution in this source gate.

SOL:
- request currency: USDC
- accepted instrument prefix: SOL_USDC-

XRP:
- request currency: USDC
- accepted instrument prefix: XRP_USDC-

Rows from other USDC-settled underlyings are transport bycatch and MUST be counted as non-target rows, then excluded before any target-asset structural audit.

They MUST NOT count as parse failures.

## Scientific invariants unchanged

No skew.
No signal.
No forward return.
No PnL.
No price outcome source.
No 2025 rows.
No performance threshold.
No asset ranking.

This amendment repairs source addressability only. A zero-row result caused solely by querying the wrong settlement-currency namespace is not a scientific SOURCE_GATE_FAIL_DATA verdict.
