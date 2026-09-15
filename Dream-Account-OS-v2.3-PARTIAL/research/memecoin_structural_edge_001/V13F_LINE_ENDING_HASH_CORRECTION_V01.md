# MSEL-001 — V13F Line-Ending Hash Correction V0.1

Status: TECHNICAL CORRECTION / PRE-V14 / RESEARCH-ONLY
Date: 2026-09-15

## Trigger

`bind_pilot25_v14_inputs_v13f.py` failed closed on the frozen V12A Markdown authority with:

- expected canonical GitHub/LF SHA-256: `e8d319c6b5f89d99ac9265a9e4ec23b7cf5f87160dd27fdee4abce6d8e112aa7`
- Windows working-tree byte SHA-256: `8b7331757bbaeb030c33d6d0d8bbcaf9edeab744f820a493dc7828dda26ab887`

The content is unchanged. The mismatch is exactly explained by Git checkout newline normalization: the repository blob uses LF while the Windows working tree materializes the Markdown file with CRLF. Re-encoding the same text with CRLF produces the observed local byte hash.

## Correction

V13F must verify the V12A Markdown authority using a canonical text hash:

1. read the UTF-8 text with universal newline normalization;
2. encode the normalized text with LF line endings;
3. compare that canonical byte sequence to the original frozen SHA-256 `e8d319c6b5f89d99ac9265a9e4ec23b7cf5f87160dd27fdee4abce6d8e112aa7`.

The binder may also record the raw local working-tree byte SHA-256 for auditability, but that platform-specific hash is not the scientific authority.

## Scientific impact

None.

This correction does not change:
- V12A content or economics;
- cohort, V11 features, risk order or 5/13/5 slices;
- entry size or formula;
- future windows;
- SELL-only evidence;
- catastrophe/winner thresholds;
- Pump/PumpSwap schemas;
- any future transaction bytes;
- any return, label, statistic or verdict.

No future raw transaction is decoded by this correction. V14 remains blocked until the corrected binder passes.
