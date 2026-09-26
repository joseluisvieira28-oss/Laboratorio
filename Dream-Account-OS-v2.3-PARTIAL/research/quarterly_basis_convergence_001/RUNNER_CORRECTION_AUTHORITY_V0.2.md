# QUARTERLY-BASIS-CONVERGENCE-001 — RUNNER CORRECTION AUTHORITY V0.2

Date: 2026-09-26  
Parent MVE: `QBC-BINANCE-USDM-7D-001`  
Parent protocol: `FROZEN_PROTOCOL_V01.json`  
Parent scientific state: V0.1 Discovery returned DATA_FAILURE before complete adjudication.

## PURPOSE

This additive authority corrects an implementation-order defect in `discovery_runner_v01.py`. It does not alter the frozen hypothesis, source, universe, signal, threshold, execution rules, costs, discovery gates, validation gates, or protected-period boundaries.

## DEFECT

V0.1 required a completely contiguous spot and futures 1-minute path from snapshot through forced exit **before** evaluating whether the frozen 0.7% signal threshold selected a trade.

That requirement is stricter than the frozen protocol. A contract with `signal_basis < 0.007` creates no position and therefore has no execution path whose intermediate bars need adjudication.

V0.1 stopped at a missing Binance Spot interval on 2023-03-24 during the BTCUSDT_230331 route before recording whether that contract was selected.

## V0.2 CORRECTION

For each frozen route, in this order:

1. Require the frozen 07:59 UTC snapshot bar on exact Binance Spot and exact dated future.
2. Compute the already-frozen signal basis.
3. If `signal_basis < 0.007`, classify that route NO_TRADE and do not inspect later execution-path continuity.
4. If selected, require the frozen 08:00 UTC entry open.
5. Walk the realized execution path minute-by-minute.
6. Any missing required bar **before the actual exit** is `DATA_FAILURE`.
7. Once target, stop, or forced exit is completed, later bars are irrelevant and are not required.

This is an implementation correction only. It cannot improve or worsen a trade by changing any economic rule.

## FROZEN ITEMS UNCHANGED

- assets: BTC, ETH
- venue: Binance Spot + Binance USD-M quarterly delivery futures
- discovery years: 2021-2023
- 2024 validation: locked until Discovery survives
- 2025/2026: locked
- signal time: T-7d 07:59 UTC close
- entry: T-7d 08:00 UTC open
- minimum entry basis: 0.007
- target basis: 0.001
- additive basis stop: 0.015
- forced exit: expiry 07:45 UTC open
- base pair cost: 0.003
- stress pair cost: 0.005
- all sample, breadth, bootstrap, PF, concentration and leave-one-out gates
- no parameter rescue / no post-outcome tuning / no asset rescue / no horizon rescue

## EXTERNAL INCIDENT CONTEXT

Binance publicly documented a Spot trading halt on 2023-03-24 beginning at 11:27 UTC and resumption at 14:00 UTC after a matching-engine trailing-stop issue. This context explains the V0.1 missing spot bars but does not authorize synthetic fill or alternate execution.

If an actually selected trade requires any missing bar during its realized path, V0.2 must remain DATA_FAILURE.

## AUTHORIZED OUTPUT

Only an additive `QBC_DISCOVERY_RESULT_V02.json` may be created. V0.1 evidence must remain preserved unchanged.
