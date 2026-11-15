"""Reconcile at most one expired V2 forward observation per requested day.

Runs ONLY after the daily frozen entry attempt; never reads future data.
No order/account access. Reads official Deribit delivery prices once at most.
Preserves UNSETTLED or failed responses rather than filling missing outcomes.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import zipfile
import audit_forward
import audit_settlement
import probe


def run(request, evidence, work):
    today=dt.date.fromisoformat(json.loads(Path(request).read_text())["date"])
    evidence=Path(evidence)
    work=Path(work)
    # Exactly one eligible expired entry per invocation; chronological by date.
    for dated in sorted(evidence.iterdir()):
        if not dated.is_dir():
            continue
        try:
            entry_day=dt.date.fromisoformat(dated.name)
        except ValueError:
            continue
        if entry_day>=today or entry_day+dt.timedelta(days=1)>today:
            continue
        archive=dated/"entry-session.zip"
        marker=dated/"entry-session-archive.json"
        if not archive.is_file() or not marker.is_file():
            continue
        # Already attempted this entry today. No duplicate GET; no retry.
        if (dated/("settlement-"+today.isoformat()+".zip")).exists():
            continue
        if any(p.name.startswith("settlement-audit-") and
               json.loads(p.read_text()).get("status")=="OFFICIAL_SETTLEMENT_INDEPENDENTLY_AUDITED_NOT_EDGE"
               for p in dated.glob("settlement-audit-*.json")):
            continue
        sha=json.loads(marker.read_text())["sha256"]
        result=audit_forward.audit_entry(archive,sha,entry_day.isoformat())
        if result["status"]!="FORWARD_DECISION_AUDITED_NOT_PROFIT":
            continue
        expiry=dt.datetime.fromisoformat(result["expiry"])
        if dt.datetime.now(dt.timezone.utc)<=expiry:
            continue
        # archive source entry receipt unchanged and bind its SHA256 to settlement.
        with zipfile.ZipFile(archive) as z:
            original=z.read("raw/receipt.json")
        work.mkdir(parents=True,exist_ok=False)
        source_entry=work/"entry-original.json"
        source_entry.write_bytes(original)
        raw=work/"settle-raw"
        # The collector performs one public delivery-price GET, no retries.
        probe.settlement(source_entry,raw,hashlib.sha256(original).hexdigest())
        target=dated/("settlement-"+today.isoformat()+".zip")
        with zipfile.ZipFile(target,"x",compression=zipfile.ZIP_DEFLATED) as z:
            for p in sorted(raw.glob("*")):
                if p.is_file():
                    z.write(p,"raw/"+p.name)
        settled_sha=hashlib.sha256(target.read_bytes()).hexdigest()
        report=audit_settlement.audit(archive,sha,target,settled_sha,entry_day.isoformat())
        # Record audit separately. Never overwrite a previous settlement attempt.
        with (dated/("settlement-audit-"+today.isoformat()+".json")).open("x") as stream:
            json.dump(dict(report,entry_date=entry_day.isoformat(),
                           attempted_date=today.isoformat()),stream,sort_keys=True,indent=2)
        with (dated/("settlement-archive-"+today.isoformat()+".json")).open("x") as stream:
            json.dump(dict(entry_archive_sha256=sha,settlement_archive_sha256=settled_sha,
                           entry_date=entry_day.isoformat(),attempted_date=today.isoformat(),
                           simulation=True),stream,sort_keys=True,indent=2)
        print(json.dumps(report,sort_keys=True))
        return report
    print("NO_ELIGIBLE_EXPIRED_ENTRY_TO_SETTLE")
    return {"status":"NO_ELIGIBLE_EXPIRED_ENTRY_TO_SETTLE"}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--request",required=True)
    p.add_argument("--evidence",required=True)
    p.add_argument("--work",required=True)
    a=p.parse_args()
    run(a.request,a.evidence,a.work)
