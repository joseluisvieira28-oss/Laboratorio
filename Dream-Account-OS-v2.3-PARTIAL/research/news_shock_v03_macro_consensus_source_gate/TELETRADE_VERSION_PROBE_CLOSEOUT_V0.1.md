# News Shock Lab V0.3 — TeleTrade Version Probe Closeout V0.1

Date: 2026-10-07  
Branch: `news-shock-v03-public-source-recovery-v0.1`

## Verdict

**VERSION_AUDIT_BLOCKED — NO SOURCE-GATE UPGRADE**

The exact historical TeleTrade article ID `3655582` was fetched directly from three locale routes. All three currently preserve the visible article timestamp `08.01.2021, 07:33` and the Credit Agricole/eFXdata text containing payroll consensus 68k, unemployment 6.8%, AHE 0.2% MoM and **4.5% YoY**.

However, the source still does not satisfy the frozen immutable-version requirement.

## Canonical probe

- workflow run: `37658646825`
- job: `112920183330`
- artifact: `11498943043`
- artifact ZIP SHA-256: `c1788f024c80a7bd34affaa9bd3af2b9fda98ff5d5577837c4ccdc411099ba49`

Current HTML hashes were frozen independently for Vietnamese, Ukrainian and Serbian locale pages.

## Version evidence result

The HTTP/HTML probe found:

- no `Last-Modified` header;
- no `ETag`;
- no structured `datePublished`;
- no structured `dateModified`;
- current response `Date` and `Expires` are retrieval-time 2026 values;
- the historical article ID and visible timestamp are stable across the tested locale routes.

Locale mirrors are not independent historical publishers and do not constitute an immutable revision history. Their agreement proves current article identity/content consistency, not that the current bytes are identical to the bytes served before the NFP release.

## Scientific consequence

The TeleTrade/Credit Agricole item remains a strong contemporaneous **witness** for NFP AHE YoY = 4.5%, but it cannot yet promote that field to the static/version-audited acceptance standard.

The exact whole-gate state therefore remains:

- CPI frozen event: static institutional **4/4**
- NFP frozen event: static institutional **3/4**
- NFP AHE YoY: contemporaneous witness exists, **version audit blocked**
- two-event reopening gate: **PARTIAL_SOURCE**
- V0.3 hypothesis: **UNTESTED**
- new census/outcome access: **NOT AUTHORIZED**

Next source work must target an independent static pre-T0 document or an auditable archived/original version for the NFP AHE YoY field. Acceptance thresholds remain unchanged.
