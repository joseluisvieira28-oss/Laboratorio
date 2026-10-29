# Oct 1/2 NVIDIA 10m Replay V0.1a — canonical source gate closeout BEFORE opening directional outcomes

Original source-only #40930443134 PASS. Initial frozen replay #40930889735 failed closed after 7/7 synthetic guards and BEFORE any win/loss calculations because the full Yahoo JSON body SHA256 differed; this is not economic rejection. V0.1a source-only #40931140788 then made two independent fetches of exactly those three public URLs, **no signal or outcome calculation**. Required price/time series had stable canonical hashes despite raw Yahoo metadata drift (raw response drift Yahoo only). Canonical hashes, pinned before any win/loss, are:
- Yahoo NVDA stock 2026-10-01: `723d89e7e3512438f55bc168dba6fd39bc3adf1d83870cbf4e7b77ce952a2b18`.
- Yahoo NVDA stock 2026-10-02: `2a075f970b68d657193aa15a2864cbf2ea9581fe2ba5a990fef8c6ee843521cc`.
- MEXC NVIDIA_USDT standard index 2026-10-01: `062323b62013951e465967d4fc8e2147a5e8509231d1a56892a143e7098e3b91`.
- MEXC NVIDIA_USDT standard index 2026-10-02: `d411b7fa75025b1c9488cf0ba87e79301bc80295d5ead4e00b6b7123e11a9203`.

Historical replay now checks exactly these required-bar canonical hashes **before** evaluating a direction or outcome. Raw bytes hashes still preserved and reported, never falsely equated with canonical price hash. This source-integrity correction is separate from economic science. Signal thresholds 10bps cash/5bps gap, Oct1/2, 12 fixed slots/day, proxy 10-minute INDEX_OPEN(t+10)-INDEX_OPEN(t), q80, baselines, session and scientific limitations are unchanged. MEXC actual Event Futures payout and server open/expiry parity remain unproved. Sept protected and Oct5–30 NVIDIA old forward remain sealed.
