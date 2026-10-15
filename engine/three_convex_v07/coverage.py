"""Observation coverage receipts; no historical signal replay or trading decisions."""
from engine.three_convex_v05.signals import MS5, aggregate_complete, Halt

class Coverage:
    def __init__(self,db):
        self.db=db
        db.execute('CREATE TABLE IF NOT EXISTS observer_coverage(lane TEXT,close_ms INTEGER,state TEXT,evaluated_ms INTEGER,signal_id TEXT,PRIMARY KEY(lane,close_ms))')
        db.execute('CREATE TABLE IF NOT EXISTS observer_gaps(lane TEXT,first_close_ms INTEGER,last_close_ms INTEGER,step_ms INTEGER,PRIMARY KEY(lane,first_close_ms,last_close_ms))')
        db.execute('CREATE TABLE IF NOT EXISTS observer_lane_health(lane TEXT PRIMARY KEY,checked_ms INTEGER,state TEXT,error_type TEXT)')
        db.commit()

    def record(self,lane,n,bars,now,activation,signals,*,error=None):
        step=n*MS5;close=now//step*step
        first=((activation+step-1)//step)*step
        if first>close:return
        previous=self.db.execute('SELECT max(close_ms) FROM observer_coverage WHERE lane=?',(lane,)).fetchone()[0]
        gap_start=first if previous is None else previous+step
        if error:
            state='SOURCE_FAILED'
        else:
            try:
                tf=aggregate_complete(bars,n)
                if len(tf)<250:state='WARMUP_INSUFFICIENT'
                elif now-close>180000:state='EXPIRED_CLOSE'
                elif not bars or bars[-1].t+MS5!=close:state='NOT_AT_TF_BOUNDARY'
                else:state='SIGNAL_QUEUED' if any(s['lane']==lane for s in signals) else 'NO_SIGNAL'
            except (Halt,TypeError,AttributeError):state='UNVERIFIED_HISTORY'
        identity=next((s['signal_id'] for s in signals if s['lane']==lane),None)
        with self.db:
            if gap_start<close:
                self.db.execute('INSERT OR IGNORE INTO observer_gaps VALUES(?,?,?,?)',(lane,gap_start,close-step,step))
            # Preserve a proved decision on the same close; failures later in the
            # timeframe cannot erase an earlier eligible decision/queued alert.
            self.db.execute('INSERT INTO observer_coverage VALUES(?,?,?,?,?) ON CONFLICT(lane,close_ms) DO UPDATE SET state=excluded.state,evaluated_ms=excluded.evaluated_ms,signal_id=excluded.signal_id WHERE observer_coverage.state NOT IN (\'SIGNAL_QUEUED\',\'NO_SIGNAL\')',(lane,close,state,now,identity))
            self.db.execute('INSERT INTO observer_lane_health VALUES(?,?,?,?) ON CONFLICT(lane) DO UPDATE SET checked_ms=excluded.checked_ms,state=excluded.state,error_type=excluded.error_type',(lane,now,state,type(error).__name__ if error else None))

    def summary(self):
        rows=self.db.execute('SELECT lane,checked_ms,state,error_type FROM observer_lane_health ORDER BY lane').fetchall()
        gaps=self.db.execute('SELECT coalesce(sum((last_close_ms-first_close_ms)/step_ms+1),0) FROM observer_gaps').fetchone()[0]
        unresolved=self.db.execute("SELECT count(*) FROM observer_coverage WHERE state NOT IN ('SIGNAL_QUEUED','NO_SIGNAL')").fetchone()[0]
        lanes={}
        for lane,checked,state,error in rows:
            latest=self.db.execute('SELECT close_ms,state FROM observer_coverage WHERE lane=? ORDER BY close_ms DESC LIMIT 1',(lane,)).fetchone()
            lanes[lane]={'checked_ms':checked,'state':state,'error_type':error,
                         'latest_close_ms':latest[0] if latest else None,
                         'latest_close_state':latest[1] if latest else None}
        return {'lanes':lanes,'unvisited_closes':int(gaps),'unresolved_observed_closes':unresolved,'complete_coverage_proven':False}
