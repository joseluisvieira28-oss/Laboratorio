"""Sanitized SQLite audit. Read-only connection + consistent read transaction.

Never selects message text, kv secrets, credentials or chat identifiers.
Run twice around actual closes to distinguish historical counters from growth.
"""
import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def inspect(path):
    db=sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True,timeout=5)
    try:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        result={'checked_utc':datetime.now(timezone.utc).isoformat(),'read_only':True}
        if 'observer_gaps' in tables:
            result['gaps']=[dict(zip(('lane','first_close_ms','last_close_ms','step_ms','count'),r)) for r in db.execute('SELECT lane,first_close_ms,last_close_ms,step_ms,(last_close_ms-first_close_ms)/step_ms+1 FROM observer_gaps ORDER BY lane,first_close_ms')]
        if 'observer_coverage' in tables:
            result['coverage_by_lane_state']=[dict(zip(('lane','state','count','first_close_ms','last_close_ms'),r)) for r in db.execute('SELECT lane,state,count(*),min(close_ms),max(close_ms) FROM observer_coverage GROUP BY lane,state ORDER BY lane,state')]
            result['unresolved']=[dict(zip(('lane','close_ms','state','evaluated_ms'),r)) for r in db.execute("SELECT lane,close_ms,state,evaluated_ms FROM observer_coverage WHERE state NOT IN ('NO_SIGNAL','SIGNAL_QUEUED') ORDER BY close_ms,lane")]
        for table,sent in (('outbox','sent_at_ms'),('notices','sent_ms')):
            if table not in tables:continue
            columns={r[1] for r in db.execute(f'PRAGMA table_info({table})')}
            live=' AND expired_ms IS NULL' if 'expired_ms' in columns else ''
            result[table]={'pending':db.execute(f'SELECT count(*) FROM {table} WHERE {sent} IS NULL'+live).fetchone()[0],
                           'sent':db.execute(f'SELECT count(*) FROM {table} WHERE {sent} IS NOT NULL').fetchone()[0]}
            if 'telegram_message_id' in columns:
                result[table]['ack_receipts']=[dict(zip(('signal_id','sent_ms','telegram_message_id'),r)) for r in db.execute(f"SELECT id,{sent},telegram_message_id FROM {table} WHERE telegram_message_id IS NOT NULL AND id LIKE '%CONVEX_%' ORDER BY {sent} DESC LIMIT 20")]
        db.rollback()
        return result
    finally:db.close()


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('database',type=Path)
    args=p.parse_args()
    try:print(json.dumps(inspect(args.database),indent=2,sort_keys=True))
    except (sqlite3.Error,OSError):
        print(json.dumps({'status':'LEDGER_READ_BLOCKED','read_only':True}));raise SystemExit(2)
