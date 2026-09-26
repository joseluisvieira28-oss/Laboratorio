#!/usr/bin/env python3
"""Mechanical LICP-001 trigger-config freezer.

This script MUST NOT inspect any price outcome. It maps predeclared feature
quantiles from an outcome-blind calibration receipt into the trigger config.
"""
import argparse,json
from pathlib import Path

def extract(receipt):
    if receipt.get("decision")!="CALIBRATION_SAMPLE":
        raise ValueError("CALIBRATION_NOT_SUFFICIENT")
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
    if any(float(v)<=0 for v in vals.values() if v is not None):
        raise ValueError("NONPOSITIVE_CALIBRATION_THRESHOLD")
    return {k:float(v) for k,v in vals.items()}

def freeze(config,receipt,receipt_ref):
    vals=extract(receipt)
    if config.get("status")=="FROZEN":
        raise ValueError("CONFIG_ALREADY_FROZEN")
    config["status"]="FROZEN"
    config["source_calibration_receipt"]=receipt_ref
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
