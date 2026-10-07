# News Shock Lab V0.3 — NFP Surprise Discovery Closeout V0.1

Date: 2026-10-07

## Final verdict

**NO_EDGE_STOP_UNDER_2021_NFP_SIGN_VOTE_DEFINITION**

The data problem was solved first: the 2021 NFP consensus source census passed **12/12**. Only after the signal, window, assets, costs and statistical gates were frozen were market outcomes opened.

The primary NFP signal was an equal sign vote across four release surprises:

- payrolls: sign(actual − consensus)
- unemployment: sign(consensus − actual)
- average hourly earnings MoM: sign(actual − consensus)
- average hourly earnings YoY: sign(actual − consensus)

Positive score = HOTTER / hypothesized crypto-down. Negative score = COOLER / hypothesized crypto-up. Zero = neutral.

The frozen market test used official Binance Spot 1-minute archives, BTCUSDT and ETHUSDT, entry at the 08:31 ET open and exit at the 08:45 ET open, with a fixed 10 bps round-trip cost proxy. Ten events were directional (8 HOTTER, 2 COOLER); two were neutral. The exact fixed-count permutation universe contained 45 assignments.

## Results

| Metric | BTCUSDT | ETHUSDT |
|---|---:|---:|
| Mean aligned gross | **-26.48 bps** | **-21.81 bps** |
| Mean aligned net after 10 bps | **-36.48 bps** | **-31.81 bps** |
| Median aligned gross | **-9.68 bps** | **-4.73 bps** |
| Exact one-sided p | **0.4889** | **0.4222** |
| Hit rate aligned gross > 0 | **30%** | **50%** |
| Minimum leave-one-out mean net | **-46.13 bps** | **-41.20 bps** |
| Frozen criteria passed | **0/4** | **0/4** |

Both pre-specified assets fail every primary criterion.

This is not a near miss. The observed direction is adverse on average before costs, remains adverse after costs, has negative medians, weak permutation evidence, and fails every leave-one-out robustness requirement.

## Governance consequence

No OOS extension is authorized by this result. No alternate window, delayed entry, subset, magnitude threshold, field weighting, revision-based rescue, asset selection or cost change may be tested as a rescue of this lab.

The correct scientific decision is:

**STOP — NO EDGE UNDER THIS PRE-SPECIFIED NFP SURPRISE DEFINITION.**

No live trading, exchange mutation or main merge is authorized.

Canonical workflow run: `37683873867`  
Artifact: `11510598139`  
Artifact ZIP SHA256: `5ea4680645819644752597f94010e5241f3b35836ea5d48643ac45ba9f112b9a`
