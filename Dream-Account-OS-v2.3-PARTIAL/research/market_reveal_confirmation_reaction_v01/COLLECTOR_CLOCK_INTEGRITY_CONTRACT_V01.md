# MRCR V0.1 — Collector Clock Integrity Contract
Status: PRE-TARGET / INFRASTRUCTURE ONLY
Date: 2026-09-25

## Purpose

Future MRCR availability checks depend on collector-arrival timestamps. A wall
clock can be corrected by the operating system while a monotonic clock should
only advance. Therefore prospective capture must preserve both clocks.

## Defined diagnostics

For consecutive samples:

- wall_delta_ns = current wall time - previous wall time
- monotonic_delta_ns = current monotonic time - previous monotonic time
- residual_ns = wall_delta_ns - monotonic_delta_ns
- wall_reversed = wall_delta_ns < 0
- monotonic_reversed = monotonic_delta_ns < 0

The tooling also reports min/max/max-absolute residual across a sample sequence.

## Boundary

No tolerance or acceptance threshold is authorized here.

This contract does not decide whether a particular residual is acceptable for a
future scientific protocol. Any such threshold, if required, must be frozen
under explicit H02 design/freeze authority before target observation.

A monotonic-clock reversal is treated as an infrastructure impossibility/error
and fails closed.

Final rule:

**MEASURE CLOCK BEHAVIOR NOW; DO NOT TUNE A SCIENTIFIC CLOCK TOLERANCE FROM TARGET DATA.**
