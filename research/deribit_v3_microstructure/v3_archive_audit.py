"""Independently audit the restored V3 quote archive before/after each cloud session.

Offline only; no Deribit, trading, order/fill or economic assumptions.
"""
import argparse
import datetime as dt
import hashlib
import json
from pathlib import Path
import v3_forward_audit as independent

def demand(condition,reason):
    if not condition: raise ValueError(reason)

def audit_archive(root, source_dir=None):
    root=Path(root)
    source_dir=Path(source_dir) if source_dir else Path(__file__).resolve().parent
    prospective=root/'prospective'
    if not prospective.is_dir():
        return dict(status='ARCHIVE_AUDIT_PASS', independent_valid=0, invalid_attempts=0,
                    claimed_days=0, missed_windows=0, live_go=False, net_pnl=None)
    claim_files=list(prospective.glob('*.claim'))
    claims={}
    for f in claim_files:
        day=f.stem
        demand(day not in claims and dt.date.fromisoformat(day).isoformat()==day,'DUPLICATE_CLAIM')
        demand(json.loads(f.read_bytes())=={'day':day},'CLAIM_CONTENT')
        claims[day]=f
    days=set()
    valid=0
    invalid=0
    for folder in sorted(p for p in prospective.iterdir() if p.is_dir()):
        receipt_file=folder/'receipt.json'
        manifest_file=folder/'manifest.json'
        demand(receipt_file.is_file() and manifest_file.is_file(),
               'INCOMPLETE_ATTEMPT_REQUIRES_RECONCILIATION')
        receipt=json.loads(receipt_file.read_bytes())
        day=receipt.get('session_utc')
        demand(isinstance(day,str) and day in claims and folder.name.startswith(day+'-'),'UNCLAIMED_ATTEMPT')
        demand(day not in days,'DUPLICATE_DAY_ATTEMPT')
        days.add(day)
        manifest_bytes=manifest_file.read_bytes()
        demand(hashlib.sha256(manifest_bytes).hexdigest()==receipt.get('manifest_sha256'),
               'MANIFEST_HASH')
        manifest=json.loads(manifest_bytes)
        demand(isinstance(manifest,list) and len(manifest)<=4,'MANIFEST_SHAPE')
        names=set()
        for item in manifest:
            name=item.get('name')
            demand(name in ('call','put','index','instruments') and name not in names,
                   'MANIFEST_SOURCE')
            names.add(name)
            raw=folder/(name+'.json')
            if 'sha256' in item:
                demand(raw.is_file() and len(raw.read_bytes())==item.get('bytes') and
                       hashlib.sha256(raw.read_bytes()).hexdigest()==item['sha256'],
                       'RAW_HASH')
            else:
                demand(not raw.exists(),'UNHASHED_SOURCE')
        demand(receipt.get('net_pnl') is None and receipt.get('live_go') is False and
               receipt.get('orders')==0 and receipt.get('delivery_fee_status')=='UNVERIFIED',
               'ECONOMICS_CONTAMINATION')
        if receipt.get('prospective_v3') is True:
            independent.audit(folder,source_dir=source_dir)
            valid+=1
        else:
            demand(receipt.get('valid_technical') is False and
                   receipt.get('status')=='INVALID_ATTEMPT',
                   'INVALID_ATTEMPT_MISCLASSIFIED')
            invalid+=1
    demand(set(claims)==days,'ORPHAN_CLAIM')
    demand(valid<=20,'COHORT_LIMIT')
    missed=list((root/'missed_windows').glob('*.json')) if (root/'missed_windows').exists() else []
    for file in missed:
        m=json.loads(file.read_bytes())
        demand(m.get('status')=='MISSED_WINDOW' and m.get('prospective_v3') is False and
               m.get('orders')==0 and m.get('net_pnl') is None,'MISSED_WINDOW_DATA')
    return dict(status='ARCHIVE_AUDIT_PASS',independent_valid=valid,
                invalid_attempts=invalid,claimed_days=len(claims),
                missed_windows=len(missed),live_go=False,net_pnl=None)

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    a=p.parse_args()
    print(json.dumps(audit_archive(a.root),indent=2))
