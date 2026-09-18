#!/usr/bin/env python3
"""DEFI-LIQUIDATION-SHOCK-001 protocol-history collector V0.2.

Append-only successor to V0.1. The acquisition mechanics are intentionally
unchanged; the only scientific routing change is that future execution loads
protocol_registry_v0_2.json, which contains the corrected Kamino discriminator
and excludes Drift spot-with-swap classes from the frozen 2021-2024 window.

READ-ONLY / SOURCE-ONLY / OUTCOME-BLIND.
"""
from __future__ import annotations
import json,os,pathlib,sys,time
import collect_protocol_history_v0_1 as base

COLLECTOR_VERSION="DLS_PROTOCOL_HISTORY_SOURCE_V02"

# Re-export shared helpers so future verifier versions can import this module.
LAB_ID=base.LAB_ID
Rpc=base.Rpc
extract_protocol_instructions=base.extract_protocol_instructions
redact_rpc_url=base.redact_rpc_url
rpc_url=base.rpc_url
sha256_bytes=base.sha256_bytes
write_json=base.write_json
b58decode=base.b58decode
load_registry=base.load_registry
select_protocols=base.select_protocols
collect_protocol=base.collect_protocol

def main()->int:
    # Rpc methods in the retained V0.1 implementation read this module-global
    # value from the base module. Set it explicitly before any request.
    base.COLLECTOR_VERSION=COLLECTOR_VERSION
    here=pathlib.Path(__file__).resolve().parent
    registry_path=here/"protocol_registry_v0_2.json"
    registry=base.load_registry(registry_path)
    if registry.get("registry_version")!="V0.2":
        raise RuntimeError("REGISTRY_VERSION_NOT_V0_2")
    protocols=base.select_protocols(registry)

    # Fail closed if the retired Kamino nibble-pair reappears anywhere in the
    # active reference encodings.
    active_prefixes=[
        str(spec.get("prefix_hex","")).lower()
        for p in protocols
        for spec in (p.get("reference_liquidation_encodings") or [])
    ]
    if "b1479acce2854a37" in active_prefixes:
        raise RuntimeError("RETIRED_KAMINO_PREFIX_ACTIVE")
    if "b1479abce2854a37" not in active_prefixes:
        raise RuntimeError("CORRECT_KAMINO_PREFIX_MISSING")

    out_dir=pathlib.Path(
        os.environ.get("DLS_OUT_DIR","data/defi_liquidation_shock_001/source_v02")
    ).resolve()
    if (out_dir/"RUN_MANIFEST.json").exists():
        raise RuntimeError(f"RUN_MANIFEST_ALREADY_EXISTS {out_dir}; use a new DLS_OUT_DIR")
    raw_dir=out_dir/"raw_rpc";raw_dir.mkdir(parents=True,exist_ok=True)

    delay=float(os.environ.get("DLS_RPS_DELAY","0.12"))
    max_pages=int(os.environ.get("DLS_MAX_PAGES_PER_PROTOCOL","0"))
    fetch_failed=os.environ.get("DLS_FETCH_FAILED","1").strip() not in {"0","false","False"}
    max_tx_version=int(os.environ.get("DLS_MAX_SUPPORTED_TX_VERSION","0"))
    if delay<0 or max_pages<0 or max_tx_version!=0:
        raise RuntimeError("INVALID_OR_UNFROZEN_CONFIGURATION")

    url=base.rpc_url();rpc=base.Rpc(url,raw_dir,delay)
    started=int(time.time());protocol_results=[];run_status="SOURCE_ACQUISITION_COMPLETE"
    try:
        for cfg in protocols:
            result=base.collect_protocol(
                rpc,cfg,out_dir,max_pages=max_pages,
                fetch_failed=fetch_failed,max_tx_version=max_tx_version,
            )
            protocol_results.append(result)
            if result["partial_due_to_safety_cap"]:
                run_status="SOURCE_ACQUISITION_PARTIAL"
    except Exception as exc:
        run_status="SOURCE_ACQUISITION_FAILED"
        base.write_json(out_dir/"RUN_ERROR.json",{
            "lab_id":base.LAB_ID,"collector_version":COLLECTOR_VERSION,
            "registry_version":"V0.2","error_type":type(exc).__name__,"error":str(exc),
            "prices_queried":False,"returns_computed":False,"pnl_computed":False,
        })
        raise
    finally:
        receipts_path=out_dir/"RPC_RECEIPTS.json"
        base.write_json(receipts_path,rpc.receipts)
        base.write_json(out_dir/"RUN_MANIFEST.json",{
            "lab_id":base.LAB_ID,"collector_version":COLLECTOR_VERSION,
            "registry_version":"V0.2","registry_sha256":base.sha256_bytes(registry_path.read_bytes()),
            "run_status":run_status,"started_unix":started,"finished_unix":int(time.time()),
            "rpc_url":base.redact_rpc_url(url),
            "source_window_utc":{"start":base.SOURCE_START_ISO,"end":base.SOURCE_END_ISO},
            "selected_protocols":[p["protocol"] for p in protocols],
            "configuration":{"rps_delay":delay,"max_pages_per_protocol":max_pages,
              "fetch_failed_transactions":fetch_failed,"max_supported_transaction_version":max_tx_version},
            "protocol_results":protocol_results,"rpc_request_count":rpc.request_id,
            "rpc_receipts_sha256":base.sha256_bytes(receipts_path.read_bytes()) if receipts_path.exists() else None,
            "governance":{"read_only":True,"source_only":True,"prices_queried":False,
              "returns_computed":False,"pnl_computed":False,"direction_tested":False,
              "live_trading":False,"exchange_mutation":False,"wallets":False,
              "source_data_pass_implied":False,"merge_main":False},
        })
    print(json.dumps({"status":run_status,"collector_version":COLLECTOR_VERSION,
                      "registry_version":"V0.2","out_dir":str(out_dir)},sort_keys=True))
    return 0

if __name__=="__main__":
    try:raise SystemExit(main())
    except KeyboardInterrupt:
        print("INTERRUPTED: source acquisition incomplete; no SOURCE_DATA_PASS",file=sys.stderr)
        raise SystemExit(130)
