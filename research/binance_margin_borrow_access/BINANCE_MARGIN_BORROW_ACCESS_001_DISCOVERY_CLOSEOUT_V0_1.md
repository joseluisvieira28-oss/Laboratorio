# BINANCE-MARGIN-BORROW-ACCESS-001 — DISCOVERY CLOSEOUT V0.1

Date: 2026-09-17
Status: **DISCOVERY_NO_SIGNAL / CLOSED FOR THIS FROZEN HYPOTHESIS**
Branch: `binance-margin-borrow-access-v0.1`
Canonical Discovery run: `35270625130`
Canonical Discovery artifact: `BINANCE_MARGIN_BORROW_ACCESS_001_DISCOVERY_V0_1`
Artifact ID: `10519357487`
Artifact ZIP digest: `sha256:be277b86ca164a3a0b2d622b107e3436d71d1c4cc88b25fd3b8c78dffc985c4f`

## Frozen hypothesis tested

Whether relaxation of short-sale / hedging constraints when an already Binance-Spot-traded asset becomes newly borrowable on Binance Cross Margin creates a reliably negative market-adjusted price effect after the information timestamp.

The Discovery protocol was frozen before outcome access. Primary outcome: article-clustered market-adjusted 24h return versus BTCUSDT. Secondary horizons: 1h and 4h only. No post-outcome tuning, rescue, pair substitution, event redefinition or protected-period access was permitted.

## Source gates

- Source census: PASS.
- Event parser/adjudication: PASS.
- Prior-Spot gate: `PRIOR_SPOT_PRIMARY_PASS`.
- Prior-Spot counts: 96 archive passes, 4 access confounds, 0 unresolved.
- Historical margin cost/borrow provenance: `CREDENTIAL_BOUND`; therefore Discovery is non-executable research only and no after-cost/live claim is authorized.
- Discovery source manifest: PASS.
- Upstream clean asset-events: 96.
- Analyzable USDT-only asset-events: 94.
- No-USDT-source exclusions: 2.
- Analyzable independent article observations: 49.
- Protected 2025/2026 firewall remained intact.

## Canonical Discovery result

Classification: `DISCOVERY_NO_SIGNAL`

Primary 24h article-level market-adjusted return:

- mean: `-0.002835880961176958` (~ -0.284%)
- median: `-0.015780987989204954` (~ -1.578%)
- t-statistic: `-0.21293965390653652`
- one-sided p-value: `0.4161379153607906`
- bootstrap 95% CI for mean: `[-0.026643233219679485, 0.024645733976477412]`
- negative article count: `30 / 49`
- negative article fraction: `0.6122448979591837`
- one-sided sign-test p-value: `0.07620388598073902`

Secondary frozen diagnostics:

- mean article MAR 4h: `0.0002878570761984466`
- mean article MAR 1h: `0.0037066571381503747`
- mean pre-event 24h MAR: `0.04652145806905686`
- pretrend t-statistic: `1.5010231789184034`
- pretrend one-sided p-value: `0.930050227539315`

## Scientific adjudication

The direction of the 24h point estimate is negative, but the primary test fails by a wide margin and the bootstrap interval spans economically meaningful positive and negative values. The sign test is also above the frozen rejection threshold. Secondary horizons do not rescue the hypothesis and are not promotable as alternate primary horizons after outcome access.

Therefore:

- no Validation/OOS is authorized for this frozen hypothesis;
- no after-cost claim is authorized;
- no promotion to watchlist/candidate/quase-diamante is authorized;
- no tuning or subset rescue is authorized;
- 2025/2026 remain unopened for this lab;
- the branch remains a reproducible research receipt and may be archived/superseded, but not rewritten as a success.

Terminal state: **DISCOVERY_NO_SIGNAL**.
