#!/usr/bin/env python3
import csv, hashlib, json
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT=Path('.')
OUT=ROOT/'source_audit_output'; OUT.mkdir(exist_ok=True)
LEDGER=OUT/'CFTC_TFF_BTC_133741_SOURCE_LEDGER_V01.csv'
POLICY=ROOT/'PUBLICATION_TIMING_POLICY_V01.json'
CUTOFF=date(2024,12,31)
assert LEDGER.exists(), LEDGER
assert POLICY.exists(), POLICY
policy=json.loads(POLICY.read_text())
assert policy['frozen_before_outcomes'] is True
assert policy['holdout_2025_accessed'] is False

def d(s): return date.fromisoformat(s[:10])
def in_range(x,a,b): return d(a)<=x<=d(b)
def normal_release(report):
    # Monday report -> Friday +4d; Tuesday report -> Friday +3d. Other weekdays fail closed.
    if report.weekday()==0: return report+timedelta(days=4)
    if report.weekday()==1: return report+timedelta(days=3)
    raise ValueError(f'unsupported report weekday {report} {report.weekday()}')
def next_tuesday_after(release):
    delta=(1-release.weekday())%7
    if delta==0: delta=7
    return release+timedelta(days=delta)

overrides={d(x['report_date']):d(x['release_date']) for x in policy['release_date_overrides']}
ranges=[(d(x['report_date_start']),d(x['report_date_end']),x['reason']) for x in policy['fail_closed_exclusion_ranges']]
rows=list(csv.DictReader(LEDGER.open(encoding='utf-8')))
events=[]
for r in rows:
    report=d(r['report_date_as_yyyy_mm_dd'])
    excluded_reason=None
    for a,b,reason in ranges:
        if a<=report<=b:
            excluded_reason=reason; break
    release=None; entry=None; exitd=None
    if excluded_reason is None:
        release=overrides.get(report) or normal_release(report)
        entry=next_tuesday_after(release)
        exitd=entry+timedelta(days=7)
        if entry>CUTOFF or exitd>CUTOFF:
            excluded_reason='protected_period_firewall_entry_or_exit_after_2024-12-31'
    events.append({
      'report_date':str(report),'release_date':str(release) if release else None,
      'entry_date':str(entry) if entry else None,'exit_date':str(exitd) if exitd else None,
      'eligible_for_future_discovery':excluded_reason is None,'exclusion_reason':excluded_reason
    })

eligible=[x for x in events if x['eligible_for_future_discovery']]
excluded=[x for x in events if not x['eligible_for_future_discovery']]
report={
 'lab':'INSTITUTIONAL-FLOW-001','mode':'PUBLICATION_TIMING_AUDIT_ONLY',
 'policy_sha256':hashlib.sha256(POLICY.read_bytes()).hexdigest(),
 'source_ledger_sha256':hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
 'total_reports':len(events),'eligible_events_before_signal_delta':len(eligible),'excluded_events':len(excluded),
 'excluded_report_dates':[x['report_date'] for x in excluded],
 'excluded_by_reason':{},'entry_min':eligible[0]['entry_date'] if eligible else None,'exit_max':eligible[-1]['exit_date'] if eligible else None,
 'publication_timing_gate_pass':len(eligible)>=250,
 'btc_returns_computed':False,'pnl_computed':False,'holdout_2025_accessed':False,'year_2026_accessed':False
}
for x in excluded:
    k=x['exclusion_reason']; report['excluded_by_reason'][k]=report['excluded_by_reason'].get(k,0)+1
(OUT/'CFTC_PUBLICATION_EVENT_CALENDAR_V01.json').write_text(json.dumps(events,indent=2,sort_keys=True),encoding='utf-8')
(OUT/'CFTC_PUBLICATION_TIMING_AUDIT_V01.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
print('TIMING ONLY / NO BTC RETURNS / NO PNL / 2025 LOCKED / 2026 LOCKED')
raise SystemExit(0 if report['publication_timing_gate_pass'] else 2)
