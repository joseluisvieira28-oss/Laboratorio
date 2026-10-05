#!/usr/bin/env python3
from __future__ import annotations
import json
from datetime import datetime, timezone
from pathlib import Path

from radar.bnb_launchpool_watcher import BinanceOfficialLaunchpoolSource

OUT=Path("artifacts/bnb_launchpool/prospective_source_audit_v03")
CAUSAL_RUNTIME_COMMIT_UTC="2026-09-24T17:58:57Z"
CAUSAL_RUNTIME_BOUNDARY_MS=int(datetime.fromisoformat(CAUSAL_RUNTIME_COMMIT_UTC.replace("Z","+00:00")).timestamp()*1000)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    now_ms=int(datetime.now(timezone.utc).timestamp()*1000)
    src=BinanceOfficialLaunchpoolSource()
    probe=src.source_probe(now_ms=now_ms)
    events=src.discover_eligible(now_ms=now_ms)
    rows=[]
    for e in events:
        rows.append({
          "article_code":e.article_code,
          "title":e.title,
          "published_ms":e.published_ms,
          "published_utc":e.published_utc,
          "detail_sha256":e.detail_sha256,
          "post_forward_boundary":True,
          "post_causal_runtime_commit":e.published_ms>CAUSAL_RUNTIME_BOUNDARY_MS
        })
    post=[x for x in rows if x["post_causal_runtime_commit"]]
    report={
      "audit_id":"BNB-LAUNCHPOOL-DEMAND-001-PROSPECTIVE-SOURCE-AUDIT-V0.3",
      "checked_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
      "causal_runtime_commit_utc":CAUSAL_RUNTIME_COMMIT_UTC,
      "source_probe":probe,
      "eligible_post_forward_boundary_count":len(rows),
      "eligible_post_causal_runtime_count":len(post),
      "eligible_events":rows,
      "post_causal_runtime_events":post,
      "verdict":(
        "NO_NEW_ELIGIBLE_POST_CAUSAL_RUNTIME_EVENT__DIAMOND_TEST_STILL_WAITING"
        if not post else
        "ELIGIBLE_POST_CAUSAL_RUNTIME_EVENTS_FOUND__MISSED_OBSERVATION_AUDIT_REQUIRED"
      ),
      "authenticated_exchange_api_used":False,
      "account_reads":False,
      "orders_created":False,
      "wallet_used":False,
      "exchange_mutation_performed":False,
      "live_trading_authorized":False
    }
    (OUT/"BNB_LAUNCHPOOL_PROSPECTIVE_SOURCE_AUDIT_V03.json").write_text(json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")
    print(json.dumps({
      "verdict":report["verdict"],
      "source_status":probe.get("status"),
      "catalog_launchpool_candidates":probe.get("launchpool_candidates_on_current_page"),
      "eligible_post_forward_boundary_count":len(rows),
      "eligible_post_causal_runtime_count":len(post),
      "events":[{"published_utc":x["published_utc"],"title":x["title"]} for x in post]
    },indent=2))
if __name__=="__main__":main()
