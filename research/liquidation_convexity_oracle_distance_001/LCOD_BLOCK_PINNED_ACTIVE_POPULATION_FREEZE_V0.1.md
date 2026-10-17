# LCOD BLOCK-PINNED ACTIVE-DEBT POPULATION FREEZE V0.1

Frozen: 2026-09-25
Lab: LIQUIDATION-CONVEXITY-ORACLE-DISTANCE-001
Stage: SOURCE / POPULATION
Market and liquidation outcomes: CLOSED

Execution prerequisite:
A Borrow-event universe source receipt must classify PASS with 100% current-MCP
coverage and complete contiguous Ethereum block coverage.

## Scientific population boundary

Choose one Ethereum finalized block N at population-run start.

Candidate universe:
all distinct (official lending Spoke, indexed Borrow user) pairs observed in
canonical Aave V4 Borrow history through block N.

The current Aave MCP borrow-holder list is NOT the scientific population. It is
only an independent contradiction/source-coverage check.

For every candidate pair:
call official Spoke.getUserAccountData(user) with block_identifier=N.

ACTIVE_DEBT_N iff:
totalDebtValueRay > 0 at N.

INACTIVE_AT_N iff:
totalDebtValueRay == 0 at N.

A borrower may be active on more than one Spoke. Scientific identity remains
(spoke,user), because Aave V4 debt/account data is Spoke-scoped.

## Required evidence

Durable receipt retains:
- block N and block hash;
- Borrow-event universe pair count through N;
- active pair count;
- inactive pair count;
- zero/raw call error count;
- SHA256 of sorted active pair hashes;
- per-Spoke active counts;
- source-universe receipt SHA/commit reference.

Raw wallet addresses are not persisted.

## PASS

BLOCK_PINNED_ACTIVE_POPULATION_PASS only if:
- source-universe prerequisite PASS;
- every candidate pair receives a successful getUserAccountData read at the
  exact same block N;
- active + inactive = candidate universe;
- zero current/latest fallback;
- active pair count > 0.

No HF threshold or collateral/debt magnitude participates in population
selection beyond totalDebtValueRay > 0.

## Next gate

Only a passing active population may be partitioned deterministically for
block-N component reconstruction.

The frozen HF reconciliation tolerance remains <=5e-5.
The canonical stress curve cannot be computed unless component reconstruction
covers >=90% of this exact active pair population with explicit exclusion/debt
share reporting.

No market return, liquidation outcome, PnL, order, transaction or live trading
is authorized by this freeze.
