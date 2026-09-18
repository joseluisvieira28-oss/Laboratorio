#!/usr/bin/env python3
import argparse,hashlib,json
from pathlib import Path

EXPECTED_RUNNER_SHA256="df625d0d4a05c55ba34ca51514d31fd61636ff0a823567585c2d02afa0877958"
EXPECTED_ID="CED1D-0031"

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda:f.read(1<<20),b""): h.update(b)
    return h.hexdigest()

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--promotion",required=True)
    ap.add_argument("--shadow",required=True)
    ap.add_argument("--runner-zip",required=True)
    ap.add_argument("--output",required=True)
    a=ap.parse_args()

    promotion=json.load(open(a.promotion))
    shadow=json.load(open(a.shadow))
    checks={}

    checks["promotion_tier2"]=promotion["v3_adjudication"]=="TIER_2_PROMOTED_CANDIDATE_QUASE_DIAMANTE"
    checks["promotion_candidate"]=promotion["candidate"]["combination_id"]==EXPECTED_ID
    checks["promotion_live_false"]=promotion["live_authorized"] is False
    checks["promotion_orders_false"]=promotion["orders_authorized"] is False
    checks["promotion_2026_false"]=promotion["access_2026_plus"] is False
    checks["shadow_status_frozen"]=shadow["status"]=="FROZEN_PRE_ACTIVATION_2026_ACCESS_NOT_AUTHORIZED"
    checks["shadow_candidate"]=shadow["candidate"]["combination_id"]==EXPECTED_ID
    checks["shadow_parameters_exact"]=(shadow["candidate"]["symbol"]=="AVAXUSDT" and shadow["candidate"]["lookback_days"]==20 and shadow["candidate"]["direction"]=="CONTINUATION" and shadow["candidate"]["horizon_days"]==1)
    checks["shadow_100usdt"]=shadow["shadow_mode"]["research_notional_usdt"]==100
    checks["shadow_read_only"]=shadow["shadow_mode"]["read_only"] is True
    checks["shadow_no_orders"]=shadow["shadow_mode"]["real_orders"] is False and shadow["shadow_mode"]["exchange_mutation"] is False
    checks["shadow_no_wallets"]=shadow["shadow_mode"]["wallets"] is False
    checks["shadow_no_keys"]=shadow["shadow_mode"]["account_api_keys"] is False
    checks["shadow_no_webhooks"]=shadow["shadow_mode"]["alerts_webhooks"] is False
    checks["shadow_activation_false"]=shadow["governance"]["activation_authorized"] is False
    checks["shadow_2026_false"]=shadow["governance"]["access_2026_plus"] is False
    checks["fees_frozen"]=(shadow["execution_model"]["base_taker_fee_bps_per_fill"]==4 and shadow["execution_model"]["stress_taker_fee_bps_per_fill"]==5)
    checks["sample_frozen"]=(shadow["operational_shadow_sample"]["min_resolved_shadow_events"]==10 and shadow["operational_shadow_sample"]["min_calendar_days"]==14)
    checks["runner_sha256"]=sha256_file(a.runner_zip)==EXPECTED_RUNNER_SHA256

    status="SHADOW_STATIC_PREFLIGHT_PASS" if all(checks.values()) else "SHADOW_STATIC_PREFLIGHT_FAIL"
    receipt={
      "document_id":"CED1D_0031_TIER2_SHADOW_STATIC_PREFLIGHT_RECEIPT_V0.1",
      "status":status,
      "candidate":EXPECTED_ID,
      "checks":checks,
      "market_data_accessed":False,
      "year_2026_accessed":False,
      "live_trading":False,
      "orders":False,
      "exchange_mutation":False,
      "wallets":False,
      "alerts_webhooks":False,
      "activation_authorized":False,
      "note":"Static readiness only. No prospective shadow outcome has been collected."
    }
    raw=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
    receipt["fingerprint"]=hashlib.sha256(raw).hexdigest()
    out=Path(a.output); out.mkdir(parents=True,exist_ok=False)
    (out/"CED1D_0031_TIER2_SHADOW_STATIC_PREFLIGHT_RECEIPT_V0.1.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
    print(json.dumps(receipt,indent=2,sort_keys=True))
    if status!="SHADOW_STATIC_PREFLIGHT_PASS": raise SystemExit(2)

if __name__=="__main__": main()
