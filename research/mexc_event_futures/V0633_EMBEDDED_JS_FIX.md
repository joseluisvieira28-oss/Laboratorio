# MEXC EVENT FUTURES LAB — V0.6.3.3 EMBEDDED-JS FIX

Date: 2026-10-02

V0.6.3.2 failed before source collection because Python interpreted the embedded JavaScript regex newline escape, producing invalid JavaScript for Playwright Page.evaluate.

V0.6.3.3 changes only string escaping so the browser receives a valid `/\\n+/` regex.

No source mapping, payout semantics, strategy, threshold, trading behavior, or account interaction is changed.
All non-GET requests remain blocked.
