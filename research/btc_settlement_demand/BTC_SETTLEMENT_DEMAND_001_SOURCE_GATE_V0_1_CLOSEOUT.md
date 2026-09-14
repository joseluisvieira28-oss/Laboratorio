# BTC-SETTLEMENT-DEMAND-001 — SOURCE GATE V0.1 CLOSEOUT

Classification: PROVENANCE_FAILURE / PROTECTED_PERIOD_BOUNDARY_BREACH

Run: 34864107073
GitHub artifact: 10355653056
Artifact ZIP SHA256: 227875f32915a41d23f31beb88350f77235c08ebd35c37659634fae4bfb8a2df
Drive evidence ZIP: 1J7SrLYVnomh6bbf-kaf5K3K1UyhO2PX9
Drive V0.1 authority: 1NQGome0r0gRpwjG3iPGlyqh_ltfx_74I

The V0.1 authority froze start=2017-01-01 and timespan=2922days. That duration terminates on 2025-01-01, not 2024-12-31. The official Blockchain.com n-transactions response therefore contained a protected-period source observation at 2025-01-01T00:00:00Z. The fail-closed runner detected the first protected timestamp and terminated immediately with access_2025=true.

This is an administrative/source-boundary error, not an economic outcome. No BTC market-price value, forward return, PnL, signal series or performance statistic was computed. Nevertheless 2025 cannot be described as fully unopened for this V0.1 run because one non-price on-chain source observation was returned. The breach is explicitly preserved.

V0.1 is CLOSED as PROVENANCE_FAILURE. It may not be silently edited or reclassified. A corrected source boundary requires a new source-gate ID and new prospective authority. Mathematical correction: 2921days from 2017-01-01 terminates exactly on 2024-12-31.
