#!/usr/bin/env python3
"""Strict one-writer/no-rescue ledger collision synthetic invariants."""
import copy, hashlib, json, tempfile
from pathlib import Path
from research.liquidation_cascade import licp001_forward_durable_ledger_v01 as ledger
def receipt(run,rows,offset):
 cfg=json.loads(ledger.CONFIG.read_text());h=ledger.sha256_bytes(ledger.CONFIG.read_bytes())
 return {"status":"FORWARD_OBSERVATION","live_trading":False,"config_version":cfg["version"],
    "config_sha256":h,"github_run_id":str(run),"github_run_attempt":"1",
    "started_wall_ms":ledger.FREEZE_CUTOFF_MS+offset,
    "ended_wall_ms":ledger.FREEZE_CUTOFF_MS+offset+500,
    "records":rows}
def row(family,eid,asset):
 return {"family":family,"episode_id":eid,"propagation_asset":asset,"pressure":"SELL",
         "event_local_ns":123456789000,"event_wall_ms":ledger.FREEZE_CUTOFF_MS+30,
         "meta":{"btc_episode":{"ignition":{"ignition_venue_ts":1800000001000}}}
              if family=="ALT_SECOND_WAVE" else {"ignition":{"ignition_venue_ts":1800000001000}},
         "targets":{"BTC_USDT":{"entry":{"bid":100,"ask":100.1},"outcomes":{}}}}
def test(rows_a,rows_b,expected,expected_keys):
 with tempfile.TemporaryDirectory() as d:
  p=Path(d)
  (p/"001.json").write_text(json.dumps(receipt(1,rows_a,1000)))
  (p/"002.json").write_text(json.dumps(receipt(2,rows_b,2500)))
  r=ledger.build(p,p/"ledger")
  assert r["status"]==expected,(r["status"],expected,r["conflicts"])
  assert r["unique_episode_ids"]==expected_keys,(r["unique_episode_ids"],expected_keys)
  return r
def main():
 eid="e101";primary=row("BTC_CONFIRMED",eid,"BTCUSDT")
 eth=row("ALT_SECOND_WAVE",eid,"ETHUSDT")
 sol=row("ALT_SECOND_WAVE",eid,"SOLUSDT")
 # Both ALT siblings sharing original BTC episode are DISTINCT and allowed.
 # Same primary across overlapping saved receipts is idempotent.
 r=test([primary,eth,sol],[copy.deepcopy(primary),copy.deepcopy(eth),copy.deepcopy(sol)],"LEDGER_OK",3)
 assert not r["conflicts"]
 # If a repeated ALT event has the SAME asset but diverges in any actual field,
 # ledger must refuse it, without picking the most profitable one.
 modified=copy.deepcopy(eth);modified["event_wall_ms"]+=333
 r=test([eth],[modified],"BLOCKED_INTEGRITY_CONFLICT",1)
 assert len(r["conflicts"])==1 and r["conflicts"][0]["family"]=="ALT_SECOND_WAVE"
 # BTC primary remains strict; no simplification of its identity.
 changed_primary=copy.deepcopy(primary);changed_primary["pressure"]="BUY"
 r=test([primary],[changed_primary],"BLOCKED_INTEGRITY_CONFLICT",1)
 assert len(r["conflicts"])==1 and r["conflicts"][0]["family"]=="BTC_CONFIRMED"
 # Cannot infer missing ALT asset; reject rather than count.
 missing=copy.deepcopy(eth);del missing["propagation_asset"]
 r=test([missing],[],"BLOCKED_INTEGRITY_CONFLICT",0)
 assert any(x.get("error")=="ALT_PROPAGATION_ASSET_MISSING_OR_INVALID" for x in r["conflicts"])
 print("LICP_ALT_SIBLING_LEDGER_FOUR_SYNTHETIC_INVARIANTS_PASS")
if __name__=="__main__":main()
