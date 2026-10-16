#!/usr/bin/env python3
"""Mechanical LICP-001 trigger-config freezer.

This script MUST NOT inspect any price outcome. It maps predeclared feature
quantiles from an outcome-blind calibration receipt into the trigger config.

V0.2 hardening: a short bounded CALIBRATION_SAMPLE is not enough. The receipt
must also prove the minimum forward-calibration evidence frozen in
LICP_001_FORWARD_CALIBRATION_FREEZE_V0_1.md.
"""
import argparse,json
from pathlib import Path

MIN_SPAN_DAYS=7.0
MIN_BYBIT_EVENTS=250
MIN_BYBIT_BTC_EVENTS=50
MIN_UPTIME_PCT=95.0

def validate_eligibility(receipt):
    if receipt.get("decision")!="CALIBRATION_SAMPLE":
        raise ValueError("CALIBRATION_NOT_SUFFICIENT")
    e=receipt.get("eligibility")
    if not isinstance(e,dict):
        raise ValueError("CALIBRATION_ELIGIBILITY_NOT_PROVEN")

    checks={
      "span_days": float(e.get("span_days",0)) >= MIN_SPAN_DAYS,
      "bybit_events": int(e.get("bybit_events",0)) >= MIN_BYBIT_EVENTS,
      "bybit_btc_events": int(e.get("bybit_btc_events",0)) >= MIN_BYBIT_BTC_EVENTS,
      "uptime_pct": float(e.get("uptime_pct",0)) >= MIN_UPTIME_PCT,
      "clock_regressions": int(e.get("clock_regressions",-1)) == 0,
      "raw_event_log_sha256": isinstance(e.get("raw_event_log_sha256"),str)
          and len(e.get("raw_event_log_sha256"))==64,
    }
    failed=[k for k,v in checks.items() if not v]
    if failed:
        raise ValueError("CALIBRATION_ELIGIBILITY_FAIL:"+",".join(failed))
    return True

def extract(receipt):
    validate_eligibility(receipt)
    b=receipt["bursts"]
    vals={
      "btc_notional":b["bybit"]["BTCUSDT"]["bursts"]["5000"]["notional"].get("p95"),
      "btc_concentration":b["bybit"]["BTCUSDT"]["bursts"]["5000"]["side_concentration"].get("p75"),
      "binance_btc_notional":b["binance"]["BTCUSDT"]["bursts"]["5000"]["notional"].get("p75"),
      "eth_notional":b["bybit"]["ETHUSDT"]["bursts"]["5000"]["notional"].get("p95"),
      "sol_notional":b["bybit"]["SOLUSDT"]["bursts"]["5000"]["notional"].get("p95"),
    }
    if any(v is None for v in vals.values()):
        raise ValueError("REQUIRED_CALIBRATION_QUANTILE_MISSING")
    if any(float(v)<=0 for v in vals.values()):
        raise ValueError("NONPOSITIVE_CALIBRATION_THRESHOLD")
    return {k:float(v) for k,v in vals.items()}

def freeze(config,receipt,receipt_ref):
    vals=extract(receipt)
    if config.get("status")=="FROZEN":
        raise ValueError("CONFIG_ALREADY_FROZEN")
    config["status"]="FROZEN"
    config["source_calibration_receipt"]=receipt_ref
    config["calibration_eligibility"]=receipt["eligibility"]
    config["btc_ignition"]["notional_threshold"]=vals["btc_notional"]
    config["btc_ignition"]["side_concentration_threshold"]=vals["btc_concentration"]
    config["binance_confirmation"]["notional_threshold"]=vals["binance_btc_notional"]
    config["alt_propagation"]["notional_thresholds"]["ETHUSDT"]=vals["eth_notional"]
    config["alt_propagation"]["notional_thresholds"]["SOLUSDT"]=vals["sol_notional"]
    config["oi_confirmation"]["enabled"]=False
    return config

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--receipt",required=True)
    ap.add_argument("--config",default="research/liquidation_cascade/LICP_001_TRIGGER_CONFIG_V0_1.json")
    ap.add_argument("--output")
    a=ap.parse_args()
    rp=Path(a.receipt);cp=Path(a.config)
    receipt=json.loads(rp.read_text())
    config=json.loads(cp.read_text())
    frozen=freeze(config,receipt,str(rp))
    out=Path(a.output) if a.output else cp
    out.write_text(json.dumps(frozen,indent=2,sort_keys=True)+"\n")
    print(json.dumps(frozen,indent=2,sort_keys=True))

if __name__=="__main__":main()
