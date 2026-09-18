#!/usr/bin/env python3
import hashlib, json, sys
from pathlib import Path

OUT=Path("artifacts/eth_staking_flow_archive_probe_v03a_aggregate"); OUT.mkdir(parents=True,exist_ok=True)
PROVIDERS=[
  "https://lodestar-mainnet.chainsafe.io",
  "http://testing.mainnet.beacon-api.nimbus.team",
  "https://ethereum-beacon-api.publicnode.com",
  "https://rpc.ankr.com/eth_beacon",
  "https://eth-mainnetbeacon.g.alchemy.com/v2/docs-demo",
]

def sha(b): return hashlib.sha256(b).hexdigest()

def main():
    files=sorted(Path("downloaded_provider_receipts").rglob("provider_*.json"))
    receipt={
      "family_id":"ETH-STAKING-FLOW-001",
      "parent_mve":"ESF-NETQUEUE-7D-001",
      "probe_id":"ESF-ARCHIVE-TRANSPORT-PROBE-003A",
      "classification":None,
      "providers":[],
      "selected_provider":None,
      "source_run_semantics":"parallel provider acquisition; canonical selection preserves original frozen provider order",
      "firewall":{"access_2025":False,"access_2026":False,"price_values_opened":False,
        "signal_series_computed":False,"discovery_event_count_computed":False,
        "returns_computed":False,"pnl_computed":False,"performance_statistics_computed":False,
        "live_trading":False,"exchange_mutation":False,"wallet_access":False,"merge_to_main":False}
    }
    try:
        if len(files)!=5:
            raise RuntimeError(f"expected 5 provider receipts, found {len(files)}")
        by_idx={}
        for p in files:
            obj=json.loads(p.read_text(encoding="utf-8"))
            idx=int(obj.get("provider_index"))
            if idx in by_idx:
                raise RuntimeError(f"duplicate provider index {idx}")
            if idx<0 or idx>=5:
                raise RuntimeError(f"invalid provider index {idx}")
            if obj.get("base")!=PROVIDERS[idx]:
                raise RuntimeError(f"provider identity mismatch at {idx}")
            fw=obj.get("firewall") or {}
            if any(bool(fw.get(k)) for k in ("access_2025","access_2026","price_values_opened","signal_series_computed",
                                             "discovery_event_count_computed","returns_computed","pnl_computed",
                                             "performance_statistics_computed","live_trading","exchange_mutation",
                                             "wallet_access","merge_to_main")):
                raise RuntimeError(f"firewall violation at provider {idx}")
            by_idx[idx]=obj
        receipt["providers"]=[by_idx[i] for i in range(5)]
        selected=None
        for i in range(5):
            if by_idx[i].get("pass") is True:
                selected=PROVIDERS[i]
                break
        if selected is not None:
            receipt["classification"]="ARCHIVE_TRANSPORT_PROBE_PASS"
            receipt["selected_provider"]=selected
        else:
            any_auth=any(bool(by_idx[i].get("auth_blocked")) for i in range(5))
            receipt["classification"]="ARCHIVE_TRANSPORT_PROBE_BLOCKED" if any_auth else "ARCHIVE_TRANSPORT_PROBE_TECHNICAL_FAILURE"
    except Exception as exc:
        receipt["classification"]="PROVENANCE_FAILURE"
        receipt["failure"]=f"{type(exc).__name__}: {str(exc)[:1200]}"

    p=OUT/"probe_receipt.json"
    p.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (OUT/"manifest.json").write_text(json.dumps({"result_sha256":sha(p.read_bytes())},indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"classification":receipt["classification"],"selected_provider":receipt["selected_provider"],
                      "provider_summary":[{"index":x.get("provider_index"),"base":x.get("base"),"pass":x.get("pass"),
                                           "auth_blocked":x.get("auth_blocked"),
                                           "boundary_successes":sum(1 for b in (x.get("boundary_results") or []) if b.get("chosen") is not None)}
                                          for x in receipt["providers"]],
                      "firewall":receipt["firewall"]},indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    sys.exit(main())
