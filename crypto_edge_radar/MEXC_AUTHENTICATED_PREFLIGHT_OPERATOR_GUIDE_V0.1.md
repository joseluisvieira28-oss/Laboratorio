# MEXC Futures Authenticated Read-Only Preflight — Operator Guide V0.1

Date: 2026-09-21

## Scope

This package performs authenticated MEXC Futures account-state reads only. It is not an execution authority and contains no order, cancel, leverage-change, margin-change, transfer or withdrawal endpoint.

Canonical API base: `https://api.mexc.com`.

## Dedicated API key

Create a dedicated MEXC API key for this Crypto Lab integration.

Required safety constraints:

- KYC/account eligibility as required by MEXC Futures API.
- Withdrawals/asset-transfer permissions OFF.
- Use the minimum Futures permissions exposed by MEXC.
- Restrict the key to the operator PC public IP when MEXC IP whitelist is available.
- Never store the key or secret in GitHub, Google Drive, Render, chat, screenshots or documents.
- Do not reuse an API key from another bot or application.

Important permission nuance: MEXC documents the private GET endpoints for leverage state and position mode as requiring Trading permission. If a read-only key cannot read them, this preflight intentionally returns FAIL_CLOSED. Enabling a broader key permission does not make this software mutating: the client remains hard-allowlisted to GET-only endpoints. Any future order transport must live in a separate candidate-specific authority and code path.

## Local secret storage

From the `crypto_edge_radar\windows` directory:

```powershell
powershell -ExecutionPolicy Bypass -File .\Set_MEXC_Preflight_Secrets.ps1
```

The script prompts locally for API Key and API Secret as SecureString and stores DPAPI-encrypted blobs under:

`%LOCALAPPDATA%\CryptoEdgeRadar\secrets`

The encrypted files are tied to the current Windows user context. They are outside the repository.

## Run the preflight

```powershell
powershell -ExecutionPolicy Bypass -File .\Run_MEXC_Authenticated_Preflight.ps1
```

The runner asks locally for the expected MEXC Futures USDT equity shown in the app. This is used to prevent a valid API key for the wrong account from being accepted.

The runner prefers `dist\MEXCAuthenticatedPreflight.exe`; if absent, it uses local Python.

Output:

`mexc_authenticated_preflight_receipt.json`

The receipt contains no API key or secret.

## PASS requires

- MEXC server clock within the local clock budget.
- BTC_USDT Futures contract API-enabled and operational.
- Contract quantity/step/tick/minimum-notional metadata readable.
- Funding readable.
- Authenticated USDT equity and available balance readable.
- Authenticated equity matches the operator-entered expected balance within 0.01 USDT.
- No open Futures positions.
- No open BTC_USDT orders.
- Authenticated account fee tier/rates readable.
- BTC_USDT leverage state readable.
- Position mode readable.
- Risk limit readable.
- Existing frozen ETF-CME 0.1% validation allocation can satisfy the observed exchange minimum notional.

If the exchange minimum exceeds that frozen ETF-CME validation budget, the result is NO_TRADE / FAIL_CLOSED. Do not increase size merely to satisfy the venue minimum.

## Not performed

- no order;
- no test trade;
- no margin-mode mutation;
- no leverage mutation;
- no Auto Margin Add mutation;
- no transfer;
- no withdrawal;
- no Render secret;
- no main merge.

After PASS, a real order still requires a canonical eligible signal, healthy candidate source/runtime, and a separate frozen candidate-specific micro-live execution authority.
