#!/usr/bin/env python3
import json,pathlib,sys
p=pathlib.Path(__file__).with_name("ORPHAN_SUPERSESSION_RESOLVER_V0.4.json")
r=json.loads(p.read_text())
e=[]
ids={x["family"]:x for x in r["families"]}
if ids["ETH-STAKING-FLOW-001"]["state"].startswith("NO_EDGE"): e.append("ETH false no-edge")
if "SOURCE_ACCESS_BLOCKED" not in ids["UPBIT-KRW-LISTING-SHOCK-001"]["state"]: e.append("UPBIT")
if "DISCOVERY_PASS_VRP_EXISTS" not in ids["BTC-OPTIONS-VRP-001"]["state"]: e.append("VRP")
if ids["DLS-MARGINFI-ORCA-RELATIVE-INTENSITY-OOS-001"]["state"]!="TERMINAL_NO_EDGE": e.append("DLS OOS")
if "SURVIVES_OOS" not in ids["DEFI-LIQUIDATION-SHOCK-001"]["state"]: e.append("DLS parent")
if r["invariant"]["main_merge"] or r["invariant"]["protected_outcomes_opened_by_v04"]: e.append("firewall")
print(json.dumps({"status":"FAIL_CLOSED" if e else "PASS","errors":e,"families":len(r["families"]),"high_value_orphans":len(r["high_value_orphans"])},indent=2))
sys.exit(bool(e))
