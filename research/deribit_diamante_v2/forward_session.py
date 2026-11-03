"""One requested scheduled entry, no retries. Archive failures; never replace a day."""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import zipfile
import probe


def run(request, evidence_root, work_root):
    day=dt.date.fromisoformat(json.loads(Path(request).read_text())['date'])
    assert dt.date(2026,11,3)<=day<=dt.date(2027,11,2), 'OUTSIDE_365_DAY_STUDY'
    dated=Path(evidence_root)/day.isoformat()
    # Includes the immutable inherited entry-0809.zip and all failed entries.
    if dated.exists() and any(dated.glob('entry*')):
        print('SKIP_ALREADY_PRESERVED: '+day.isoformat())
        return
    now=dt.datetime.now(dt.timezone.utc)
    work=Path(work_root);work.mkdir(parents=True,exist_ok=False)
    if now.date()!=day or now.hour!=8 or not 5<=now.minute<10:
        result=dict(status='MISSED_SESSION',mode='entry',date=day.isoformat(),
                    observed=now.isoformat(),simulation=True,orders=0,private_requests=0,
                    reason='RUNNER_OUTSIDE_FROZEN_WINDOW',freeze=probe.FREEZE)
        probe.save(work/'receipt.json',result)
    else:
        try:
            probe.collect(work/'raw','entry')
        except Exception as exc:
            # Covers window rollover before collect() creates its source root.
            later=dt.datetime.now(dt.timezone.utc)
            missed=later.date()!=day or later.hour!=8 or not 5<=later.minute<10
            probe.save(work/'wrapper-error.json',dict(status='MISSED_SESSION' if missed else 'SOURCE_BLOCKED',
                       date=day.isoformat(),observed=later.isoformat(),simulation=True,
                       reason=type(exc).__name__+':'+str(exc),freeze=probe.FREEZE))
    dated.mkdir(parents=True,exist_ok=True)
    target=dated/'entry-session.zip'
    # Exclusive creation: no overwrite even if another caller won a race.
    with zipfile.ZipFile(target,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(work.rglob('*')):
            if path.is_file():archive.write(path,path.relative_to(work))
    checksum=hashlib.sha256(target.read_bytes()).hexdigest()
    probe.save(dated/'entry-session-archive.json',dict(archive=target.name,sha256=checksum,
                requested_date=day.isoformat(),simulation=True))
    print(json.dumps(dict(archive=str(target),sha256=checksum)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--request',required=True)
    p.add_argument('--evidence',required=True);p.add_argument('--work',required=True)
    a=p.parse_args();run(a.request,a.evidence,a.work)
