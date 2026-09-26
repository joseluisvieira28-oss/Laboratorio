# RETH-NAV-DISLOCATION-001 — FINAL CONTINUATION TRIGGER V0.1E

Triggered: 2026-09-26

Execute the exact pre-frozen continuation chain using:
- ubuntu-22.04;
- Python 3.12;
- Node 24;
- split PublicNode header / BlockMachine archive transport;
- Multicall3;
- EIP-1898 exact blockHash + requireCanonical;
- archive pacing >=1.5 seconds between scientific points;
- 2-second * attempt retry backoff.

No scientific gate changes.

Sequence:
1. split-transport/blockHash equivalence;
2. exact 556/556 predictor census;
3. q05/q95 calibration;
4. 139-point Discovery predictor sample gate;
5. mechanism Discovery only if sample PASS.

OOS, protected holdout, market-return PnL and live trading remain CLOSED.
