#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import crypto from "node:crypto";
import { x402Client, x402HTTPClient, wrapFetchWithPayment } from "@x402/fetch";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { registerExactSvmScheme } from "@x402/svm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import { createKeyPairSignerFromBytes } from "@solana/kit";
import { base58 } from "@scure/base";

const AUTH_PATH = "labs/BTC_OPTIONS_VRP_001/LAEVITAS_PAID_MICRO_PROBE_AUTHORITY_V0.1.json";
const CHALLENGE_PATH = "labs/BTC_OPTIONS_VRP_001/LAEVITAS_X402_CHALLENGE_FROZEN_V0.1.json";
const OUT = "artifacts/btc_options_vrp_laevitas_paid_micro_probe_v01";
fs.mkdirSync(OUT, { recursive: true });

const auth = JSON.parse(fs.readFileSync(AUTH_PATH, "utf8"));
const frozen = JSON.parse(fs.readFileSync(CHALLENGE_PATH, "utf8"));
const networkChoice = String(process.env.LAEVITAS_X402_NETWORK || "").toLowerCase();
const confirm = process.env.LAEVITAS_X402_CONFIRM || "";

function fail(msg, classification = "PAID_MICRO_PROBE_FAIL_CLOSED") {
  const result = {
    lab_id: auth.lab_id,
    source_mve_id: auth.source_mve_id,
    classification,
    error: msg,
    payment_authorized: true,
    payment_executed: false,
    wallet_signature_executed: false,
    outcomes_opened: false,
    strategy_pnl_opened: false,
    access_2025: false,
    access_2026: false,
  };
  const p = path.join(OUT, "paid_micro_probe_result.json");
  fs.writeFileSync(p, JSON.stringify(result, null, 2) + "\n");
  console.error(`${classification}: ${msg}`);
  process.exit(2);
}

if (confirm !== "PAY-EXACTLY-0.10-USDC-ONE-BUNDLE") fail("manual confirmation token missing or incorrect");
if (!["base", "solana"].includes(networkChoice)) fail("LAEVITAS_X402_NETWORK must be base or solana");
if (auth.provider_payment_cap_usdc !== 0.10 || auth.max_bundle_purchases !== 1) fail("authority cap mismatch");
for (const key of ["outcomes_authorized", "strategy_pnl_authorized", "access_2025_authorized", "access_2026_authorized", "live_trading_authorized", "exchange_mutation_authorized", "merge_to_main_authorized"]) {
  if (auth[key] !== false) fail(`firewall flag ${key} is not false`);
}

const expected = frozen.accepts[networkChoice];
if (!expected) fail("chosen network absent from frozen challenge");
if (expected.amount !== "100000") fail("frozen amount is not exactly 100000 atomic USDC", "PAYMENT_CAP_EXCEEDED");

function decodePaymentRequired(header) {
  if (!header) fail("PAYMENT-REQUIRED header missing from fresh challenge", "SOURCE_ACQUISITION_TECHNICAL_FAILURE");
  const padded = header + "=".repeat((4 - (header.length % 4)) % 4);
  try {
    return JSON.parse(Buffer.from(padded, "base64url").toString("utf8"));
  } catch (e) {
    fail(`cannot decode fresh PAYMENT-REQUIRED header: ${e.message}`, "SOURCE_ACQUISITION_TECHNICAL_FAILURE");
  }
}

function matchFrozen(req) {
  if (!req) return false;
  const sameAsset = networkChoice === "base"
    ? String(req.asset || "").toLowerCase() === String(expected.asset).toLowerCase()
    : String(req.asset || "") === String(expected.asset);
  return req.network === expected.network &&
    req.scheme === expected.scheme &&
    String(req.amount) === expected.amount &&
    sameAsset &&
    String(req.payTo) === expected.payTo &&
    Number(req.maxTimeoutSeconds) === Number(expected.maxTimeoutSeconds);
}

const url = frozen.resource_url;
if (!url.includes("date=2024-06-01T12%3A00%3A00Z")) fail("frozen resource URL no longer matches the authorized pre-2025 timestamp");

// Fresh pre-payment challenge. This request itself cannot spend funds.
const pre = await fetch(url, { method: "GET", headers: { "accept": "application/json", "user-agent": "SRC-Crypto-Lab-Laevitas-PaidMicro/0.1" } });
if (pre.status !== 402) fail(`expected HTTP 402 before payment, got ${pre.status}`, "SOURCE_ACQUISITION_TECHNICAL_FAILURE");
const paymentHeader = pre.headers.get("payment-required") || pre.headers.get("x-payment-required");
const paymentRequired = decodePaymentRequired(paymentHeader);
if (Number(paymentRequired.x402Version) !== 2) fail("fresh x402 version differs from frozen v2 challenge", "PAYMENT_CAP_EXCEEDED");
const candidates = Array.isArray(paymentRequired.accepts) ? paymentRequired.accepts.filter(matchFrozen) : [];
if (candidates.length !== 1) fail("fresh payment requirement does not exactly match the frozen authorized requirement", "PAYMENT_CAP_EXCEEDED");

// Create only the signer for the explicitly selected network. Never print the credential.
let signer;
if (networkChoice === "base") {
  let key = process.env.LAEVITAS_X402_EVM_PRIVATE_KEY || "";
  if (!key) fail("EVM signer secret not available", "SIGNER_NOT_AVAILABLE");
  if (!key.startsWith("0x")) key = `0x${key}`;
  signer = privateKeyToAccount(key);
} else {
  const key = process.env.LAEVITAS_X402_SOLANA_PRIVATE_KEY || "";
  if (!key) fail("Solana signer secret not available", "SIGNER_NOT_AVAILABLE");
  signer = await createKeyPairSignerFromBytes(base58.decode(key));
}

// Selector refuses every requirement except the single frozen 0.10-USDC choice.
const client = new x402Client((_version, accepts) => {
  const matches = accepts.filter(matchFrozen);
  if (matches.length !== 1) throw new Error("FAIL_CLOSED_PAYMENT_REQUIREMENT_MISMATCH");
  return matches[0];
});
if (networkChoice === "base") registerExactEvmScheme(client, { signer });
else registerExactSvmScheme(client, { signer });
const httpClient = new x402HTTPClient(client);
const paidFetch = wrapFetchWithPayment(fetch, httpClient);

// Exactly one payment-enabled application request. No loops, pagination, retries, or second endpoint.
let response;
try {
  response = await paidFetch(url, { method: "GET", headers: { "accept": "application/json", "user-agent": "SRC-Crypto-Lab-Laevitas-PaidMicro/0.1" } });
} catch (e) {
  fail(`payment/request failed: ${e?.message || String(e)}`, "PAYMENT_SETTLEMENT_FAILURE");
}

const text = await response.text();
if (text.length > 15_000_000) fail("paid payload exceeds 15 MB safety cap", "SOURCE_ACQUISITION_TECHNICAL_FAILURE");
const rawPath = path.join(OUT, "paid_response.json");
fs.writeFileSync(rawPath, text);

let payload;
try { payload = JSON.parse(text); }
catch (e) { fail(`paid response is not JSON: ${e.message}`, "SOURCE_DATA_INSUFFICIENT"); }

const required = auth.required_quote_fields;
function findRecord(obj) {
  if (Array.isArray(obj)) {
    for (const x of obj) { const r = findRecord(x); if (r) return r; }
    return null;
  }
  if (obj && typeof obj === "object") {
    if (required.every(k => Object.prototype.hasOwnProperty.call(obj, k))) return obj;
    for (const v of Object.values(obj)) { const r = findRecord(v); if (r) return r; }
  }
  return null;
}
const record = findRecord(payload);
const success = response.status === 200 && !!record;
const result = {
  lab_id: auth.lab_id,
  source_mve_id: auth.source_mve_id,
  classification: success ? "MICRO_PROBE_SOURCE_PASS" : "SOURCE_DATA_INSUFFICIENT",
  network: networkChoice,
  request_url: url,
  http_status: response.status,
  required_quote_fields_present_in_at_least_one_record: !!record,
  response_bytes: Buffer.byteLength(text),
  response_sha256: crypto.createHash("sha256").update(text).digest("hex"),
  frozen_payment_requirement: expected,
  payment_authorized: true,
  payment_executed: response.status !== 402,
  wallet_signature_executed: true,
  provider_payment_cap_usdc: auth.provider_payment_cap_usdc,
  outcomes_opened: false,
  strategy_pnl_opened: false,
  access_2025: false,
  access_2026: false,
  live_trading: false,
  exchange_mutation: false,
  merge_to_main: false,
  stop_rule_enforced: true
};
const resultPath = path.join(OUT, "paid_micro_probe_result.json");
fs.writeFileSync(resultPath, JSON.stringify(result, null, 2) + "\n");
const manifest = {
  authority_sha256: crypto.createHash("sha256").update(fs.readFileSync(AUTH_PATH)).digest("hex"),
  frozen_challenge_sha256: crypto.createHash("sha256").update(fs.readFileSync(CHALLENGE_PATH)).digest("hex"),
  result_sha256: crypto.createHash("sha256").update(fs.readFileSync(resultPath)).digest("hex"),
  paid_response_sha256: result.response_sha256
};
fs.writeFileSync(path.join(OUT, "manifest.json"), JSON.stringify(manifest, null, 2) + "\n");
console.log(JSON.stringify(result, null, 2));
if (!success) process.exit(3);
