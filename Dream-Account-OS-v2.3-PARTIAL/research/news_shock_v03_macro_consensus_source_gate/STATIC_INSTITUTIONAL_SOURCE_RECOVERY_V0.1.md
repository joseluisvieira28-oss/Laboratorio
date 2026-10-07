# News Shock Lab V0.3 — Static Institutional Source Recovery V0.1

Date: 2026-10-07  
Branch: `news-shock-v03-public-source-recovery-v0.1`

## Verdict

**PARTIAL_SOURCE — CPI STATIC 4/4; NFP STATIC 3/4; ONE FIELD REMAINS**

The public-source recovery materially advanced beyond the first web-page probe. A GitHub Actions evidence job downloaded the publisher-hosted PDFs directly, hashed the exact bytes, extracted PDF metadata and text, and uploaded an immutable workflow artifact.

Canonical evidence run: `37657905625`  
Artifact: `11499386948`  
Artifact ZIP SHA-256: `65432f012307e029cd2f3cd6751976b87ddb2141d05525d70a714901be7ace3a`

No market outcomes were opened.

## CPI frozen event — static 4/4 recovered

Frozen event: `US_CPI_2021-01-13`, T0 `2021-01-13T13:30:00Z`.

Danske Bank Research, *Weekly Focus*, 8 January 2021:

- PDF SHA-256: `a6515f7d42778c3eedb263f201a001f9dc2ad45eca63fb491ab2fb9edf739c79`
- PDF CreationDate: `2021-01-08T11:58:59Z`
- PDF ModDate: `2021-01-08T12:10:08Z`
- headline CPI MoM consensus: **0.4%**
- headline CPI YoY consensus: **1.3%**
- core CPI MoM consensus: **0.1%**
- core CPI YoY consensus: **1.6%**

The embedded creation/modification timestamps predate frozen CPI T0 by roughly five days. The current publisher-hosted bytes are now pinned by hash and by the Actions artifact.

**Static field coverage: 4/4.**

## NFP frozen event — static 3/4 recovered

Frozen event: `US_NFP_2021-01-08`, T0 `2021-01-08T13:30:00Z`.

Scotiabank Global FX Strategy, *Daily FX Update*, Friday 8 January 2021:

- PDF SHA-256: `b13d54258779d0ce20d421ca246d7e2b4b2ef9b1a7aca3b24667071a86972864`
- PDF CreationDate: `2021-01-08T12:08:19Z`
- PDF ModDate: `2021-01-08T13:22:58Z`
- last embedded modification precedes NFP T0 by **422 seconds (7m02s)**
- payroll consensus: **50k**
- unemployment consensus: **6.8%**
- AHE MoM consensus: **0.2%**
- AHE YoY: **not present in this document**

The document identifies its calendar source as Scotiabank & Bloomberg. Its embedded ModDate is inside the final eight minutes before T0, making it a strong point-in-time witness for the three displayed fields.

**Static field coverage: 3/4.**

## Important conflict preserved

A separate pre-release Credit Agricole/TeleTrade item reported payroll consensus as 68k, while the Scotiabank/Bloomberg calendar reports 50k. This is not averaged or reconciled after the fact. It demonstrates why source vendor and snapshot time must be carried explicitly.

## Exact remaining blocker

Only one required field still lacks a source meeting the same static/auditable standard:

`US_NFP_2021-01-08 -> Average Hourly Earnings YoY consensus`

Multiple public contemporaneous pages report **4.5% YoY**, including the Yahoo Finance Morning Brief before the 08:30 ET release, but current mutable web pages are not promoted to frozen source PASS without an immutable snapshot/version chain.

## Consequence

The whole two-event reopening gate remains **PARTIAL_SOURCE**. Do not start a new census, calculate macro surprises, open market outcomes, or change the terminal V0.3 scientific status yet.

The next attack is narrowly defined: recover a static or version-auditable pre-T0 witness for the NFP AHE YoY field, ideally tied to the same Bloomberg-consensus snapshot family as the Scotiabank document.
