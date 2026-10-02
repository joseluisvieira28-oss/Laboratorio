# MEXC EVENT FUTURES LAB — V0.6.3.2 SELECTOR HARDENING

Date: 2026-10-02
Status: SOURCE-ONLY / TECHNICAL

V0.6.3.1 still failed to identify the Event Futures horizon group reliably in the automated collector. This is a DOM-selector implementation failure only.

Independent V0.6.2.1 census established a simpler invariant for the current public page:
- the unique visible leaf "10m" belongs to the Event Futures horizon selector;
- its parent text is "10m";
- its grandparent text is exactly the four-label group "10m / 30m / 1H / 1D".

V0.6.3.2 therefore anchors the group directly at the unique 10m leaf's grandparent and validates that the grandparent contains exactly those four short time labels before any click.

No scientific hypothesis, payout rule, strategy threshold, or trading action is changed.
All non-GET requests remain blocked.
