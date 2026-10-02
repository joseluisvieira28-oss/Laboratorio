# MEXC EVENT FUTURES LAB — V0.6.3 SELECTOR CORRECTION V0.6.3.1

Date: 2026-10-02

V0.6.3 source run returned BLOCKED because the generic horizon-selector search admitted multiple nested DOM nodes for the same visible label. This is a selector implementation failure, not a source failure.

V0.6.2.1 independently proved a unique Event Futures horizon group anchored by the unique visible 10m label, with sibling labels 30m, 1H and 1D. V0.6.3.1 changes only the selector implementation:

1. locate the unique visible leaf label 10m;
2. climb to the nearest ancestor containing exactly the Event Futures horizon set 10m / 30m / 1H / 1D and excluding chart-only labels 1m / 5m / 15m / 4H;
3. within that container, click the unique visible leaf for the requested horizon.

No payout outcomes, trading outcomes, thresholds, hypotheses or economic rules are changed. All non-GET requests remain blocked.
