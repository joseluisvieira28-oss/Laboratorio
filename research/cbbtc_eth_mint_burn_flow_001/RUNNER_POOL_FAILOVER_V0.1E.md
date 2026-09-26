# CBBTC-ETH-MINT-BURN-FLOW-001 — RUNNER POOL FAILOVER V0.1E

Frozen: 2026-09-27
Scope: GitHub-hosted runner pool only.

Observed:
- single-run V0.1D is queued on ubuntu-22.04;
- multiple Laboratorio Ubuntu jobs are simultaneously queued;
- no scientific step of the cbBTC lab has executed in that queued run.

Permitted remediation:
- change only the GitHub-hosted runner image from ubuntu-22.04 to macos-15;
- retain Node 24 and Python 3.12;
- retain exact source/census/calibration/sample/Discovery scripts;
- retain exact source authorities, periods, q10/q90, event counts, 24h primary horizon, bootstrap and 2026 firewall.

The workflow keeps the same concurrency group with cancel-in-progress=true, so the new runner-pool attempt supersedes the obsolete queued Ubuntu attempt.

Runner selection earns zero promotion/scientific credit.
