# DEFI-LIQUIDATION-SHOCK-001 — KAMINO CHUNK #1 PHASE-B INPUT BINDING V0.1

Date: 2026-09-22  
Status: **FROZEN BEFORE TRANSACTION-BODY ACCESS**

Phase A classification: `KAMINO_CHUNK1_SIGNATURE_ENUMERATION_PASS`

Exact Phase A authority:
- workflow run: `35688650697`
- artifact ID: `10677641485`
- artifact name: `dls-kamino-chunk1-signature-enumeration-v01`
- artifact SHA256: `467583065780d9601fb837f67ae9110c9e09463f39bba50fa5c7630e76bf231a`
- exact `CHUNK1_SIGNATURES.csv` SHA256: `27f621aa318c138871a2951d94992acc0d5729b4d0657219ab21232325c5b73e`
- exact target signature count: `10560`
- Phase A pages: `11`
- Phase A terminal condition: `SHORT_PAGE_EXHAUSTED`

Phase B MUST download this exact artifact, verify the CSV hash and row count, and fail closed before RPC transaction access if either differs.

## Frozen transaction retrieval

- endpoint: `https://api.mainnet-beta.solana.com`
- method: `getTransaction`
- commitment: `finalized`
- encoding: `jsonParsed`
- max supported transaction version: `0`
- every one of the 10,560 frozen signatures must receive a non-null structurally valid transaction result;
- batching is a transport optimization only; batch size may be reduced automatically on transport/rate-limit errors without changing the signature corpus or decoder;
- each raw JSON-RPC response body must be retained in evidence;
- no signature substitution is permitted.

## Frozen verification per transaction

Required source consistency:
- returned slot equals Phase A slot;
- returned blockTime equals Phase A blockTime;
- successful/failed state agrees with Phase A `err` presence;
- all top-level and inner instructions are scanned.

Reference match requires:
- exact Kamino program ID `KLend2g3cP87fffoy8q1mQqGKjrxjC8boSyAYavgmjD`;
- base58-decoded data begins with exact `b1479abce2854a37`.

Realized liquidation reference requires additionally:
- `meta.err == null`.

Failed matching attempts are retained but are not realized events.

## Frozen adjudication

Only after all 10,560 transactions pass retrieval/source-consistency:
- sort matching successful references by `blockTime, slot, signature, instruction ordering`;
- the first row is the provisional Kamino first-success candidate for chunk #1;
- no later chunk is opened if a successful matching reference exists in chunk #1;
- exact earliest candidate must receive an independent RAW re-fetch verification before boundary acceptance.

If even one frozen transaction remains unavailable or structurally inconsistent, Phase B is source-blocked and no first-success boundary is accepted.

All economic/outcome firewalls remain closed.
