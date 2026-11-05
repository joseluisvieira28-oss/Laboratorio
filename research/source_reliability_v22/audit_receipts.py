"""Independent post-capture read-only auditor: NO import of compare.py.

Reconstructs raw source freshness/coverage using a separate implementation.
Only standard library. Does not alter live capture, source thresholds or PnL.
Usage: python audit_receipts.py ARTIFACT_ROOT
"""
from __future__ import annotations
import gzip,hashlib,json,sys
from collections import Counter
from decimal import Decimal,InvalidOperation
from pathlib import Path

class AuditFail(Exception):pass
def chk(t,msg):
    if not t:raise AuditFail(msg)
def sha(data):return hashlib.sha256(data).hexdigest()
def val(q,zero=False):
    try:p=Decimal(str(q))
    except (InvalidOperation,ValueError,TypeError):raise AuditFail("BAD_DECIMAL")
    chk(p.is_finite() and p>=0 and (p>0 or zero),"BAD_SIZE_OR_PRICE")
    return p

class Independent:
    def __init__(self):
        self.pong={"bybit":-1e12,"mexc":-1e12}
        self.ack={"bybit":False,"mexc":False}
        self.clock={"A":None,"B":None,"C":None,"mexc":None}
        self.q={"A":30,"B":30,"C":30}
        self.u1=None;self.sig1=None;self.um=None
        self.ub=None;self.seqb=None;self.bid={};self.ask={};self.ready=False
        self.good=Counter();self.stale=Counter();self.count=Counter()
        self.last=None;self.nexttick=1;self.samples=Counter();self.invalid=[]
    def reset(self,t,venue,why):
        self.count["reset:"+venue+":"+why]+=1
        self.pong[venue]=-1e12;self.ack[venue]=False
        if venue=="bybit":
            self.u1=None;self.sig1=None;self.ub=None;self.seqb=None
            self.ready=False;self.bid={};self.ask={}
            for k in "ABC":self.clock[k]=None;self.q[k]=max(self.q[k],t+30)
        else:
            self.um=None;self.clock["mexc"]=None
            for k in "ABC":self.q[k]=max(self.q[k],t+30)
    def tick(self,t):
        for k in "ABC":
            z=self.clock[k]
            if z is not None and t-z>1:
                self.stale[k]+=1
                self.q[k]=max(self.q[k],t+30)
                self.clock[k]=None
            ok=(t>=self.q[k] and self.ack["bybit"] and self.ack["mexc"]
                and 0<=t-self.pong["bybit"]<=35 and 0<=t-self.pong["mexc"]<=35
                and self.clock["mexc"] is not None
                and 0<=t-self.clock["mexc"]<=1
                and self.clock[k] is not None and 0<=t-self.clock[k]<=1
                and (k!="C" or self.ready))
            if ok:self.good[k]+=1
    def _stamp(self,m,r):
        x=int(m["ts"])
        chk(r["utc_ms"]-1500<=x<=r["utc_ms"]+250,"WRONG_SOURCE_TIMESTAMP")
    def _levels(self,rows,allowzero):
        chk(isinstance(rows,list),"MISSING_PRICE_LEVELS")
        ps=[]
        for pair in rows:
            chk(isinstance(pair,list) and len(pair)==2,"LEVEL_SHAPE")
            ps.append((val(pair[0]),val(pair[1],allowzero)))
        chk(len({x[0] for x in ps})==len(ps),"DUPLICATE_PRICE")
        return ps
    def _l1(self,msg,t):
        d=msg["data"]
        chk(msg["type"]=="snapshot" and d["s"]=="BTCUSDT","WRONG_L1")
        b=self._levels(d["b"],False);a=self._levels(d["a"],False)
        chk(b and a and b[0][0]<a[0][0],"BAD_L1_BBO")
        u=int(d["u"]);sig=(str(b[0][0]),str(a[0][0]),str(b[0][1]),str(a[0][1]))
        if u==self.u1:
            chk(sig==self.sig1,"L1_SAME_U_CHANGED")
            self.clock["B"]=t;self.count["l1_duplicate"]+=1
        else:
            chk(self.u1 is None or u>self.u1 or u==1,"L1_REGRESSION")
            self.u1=u;self.sig1=sig
            self.clock["A"]=t;self.clock["B"]=t
            self.count["l1_change"]+=1
    def _l50(self,msg,t):
        d=msg["data"];chk(d["s"]=="BTCUSDT","L50_SYMBOL")
        u,seq=int(d["u"]),int(d["seq"]);typ=msg["type"]
        if typ=="snapshot":
            b=self._levels(d["b"],True);a=self._levels(d["a"],True)
            chk(b and a,"EMPTY_SNAPSHOT")
            chk([x[0] for x in b]==sorted([x[0] for x in b],reverse=True),"BID_SORT")
            chk([x[0] for x in a]==sorted([x[0] for x in a]),"ASK_SORT")
            self.bid={p:q for p,q in b if q>0};self.ask={p:q for p,q in a if q>0}
            self.ready=True;self.count["l50_snapshot"]+=1
        elif typ=="delta" and u==1:
            self.ready=False;self.ub=None;self.seqb=None
            self.clock["C"]=None;self.q["C"]=t+30
            self.count["l50_u1"]+=1;return
        elif typ=="delta":
            if not self.ready:
                self.count["l50_wait"]+=1;return
            chk(u>self.ub and seq>self.seqb,"L50_REGRESSION")
            b=self._levels(d["b"],True);a=self._levels(d["a"],True)
            chk([x[0] for x in b]==sorted([x[0] for x in b],reverse=True),"DELTA_B_SORT")
            chk([x[0] for x in a]==sorted([x[0] for x in a]),"DELTA_A_SORT")
            newb=self.bid.copy();newa=self.ask.copy()
            for dest,rows in ((newb,b),(newa,a)):
                for p,q in rows:
                    if q==0:dest.pop(p,None)
                    else:dest[p]=q
            self.bid,self.ask=newb,newa
            self.count["l50_delta"]+=1
        else:raise AuditFail("L50_TYPE")
        chk(self.bid and self.ask and max(self.bid)<min(self.ask),"CROSSED_L50")
        self.ub=u;self.seqb=seq;self.clock["C"]=t
    def _mexc(self,msg,r,t):
        channel=msg.get("channel")
        if channel=="rs.sub.depth.full":
            chk(msg.get("data") in (0,"0","success"),"MEXC_SUB")
            self.ack["mexc"]=True
        elif channel=="pong":self.pong["mexc"]=t
        elif channel=="push.depth.full":
            chk(msg.get("symbol")=="BTC_USDT","MEXC_SYMBOL")
            self._stamp(msg,r)
            d=msg["data"];ver=int(d["version"])
            chk(self.um is None or ver>self.um,"MEXC_VERSION")
            b=self._levels(d["bids"],False);a=self._levels(d["asks"],False)
            chk(len(b)>=5 and len(a)>=5,"MEXC_SHORT")
            chk([x[0] for x in b]==sorted([x[0] for x in b],reverse=True),"MEXC_B_SORT")
            chk([x[0] for x in a]==sorted([x[0] for x in a]),"MEXC_A_SORT")
            chk(b[0][0]<a[0][0],"MEXC_CROSSED")
            self.um=ver;self.clock["mexc"]=t;self.count["mexc_book"]+=1
    def feed(self,r):
        t=r["elapsed"];v=r["venue"]
        while self.nexttick<t and self.nexttick<=600:
            self.tick(self.nexttick);self.nexttick+=1
        if self.last is not None:
            prev=self.last
            dt=r["utc_ms"]-prev["utc_ms"];dm=(r["mono_ns"]-prev["mono_ns"])/1e6
            chk(r["seq"]==prev["seq"]+1 and dm>=0 and dt>=-1
                and abs(dt-dm)<=250,"RECEIPT_CLOCK_OR_SEQUENCE")
        self.last=r;kind=r["kind"]
        if kind=="connect":self.reset(t,v,"CONNECT")
        if kind in ("disconnect","fault") and v in ("bybit","mexc"):
            self.reset(t,v,kind.upper())
        if kind=="frame":
            try:
                msg=json.loads(r["raw"])
                if v=="mexc":self._mexc(msg,r,t)
                elif v=="bybit":
                    if msg.get("op")=="subscribe":
                        chk(msg.get("success") is True,"BYBIT_SUB");self.ack["bybit"]=True
                    if msg.get("op")=="pong" or msg.get("ret_msg")=="pong":
                        self.pong["bybit"]=t
                    topic=msg.get("topic")
                    if topic=="orderbook.1.BTCUSDT":
                        self._stamp(msg,r);self._l1(msg,t)
                    elif topic=="orderbook.50.BTCUSDT":
                        self._stamp(msg,r);self._l50(msg,t)
            except Exception as exc:
                self.invalid.append((r["seq"],v,str(exc)))
                if v in ("bybit","mexc"):self.reset(t,v,"INVALID")
        if self.nexttick==t and self.nexttick<=600:
            self.tick(t);self.nexttick+=1
    def finish(self):
        while self.nexttick<=600:self.tick(self.nexttick);self.nexttick+=1

def audit(path):
    path=Path(path)
    raw=path/"raw.jsonl.gz";manifest=json.loads((path/"manifest.json").read_text())
    expected=json.loads((path/"report.json").read_text())
    chk(raw.exists(),"MISSING_RAW")
    chk(sha(raw.read_bytes())==manifest["gzip_sha256"],"GZIP_SHA256_MISMATCH")
    raw_h=hashlib.sha256();n=0;ind=Independent()
    with gzip.open(raw,"rb") as fh:
        for line in fh:
            n+=1;raw_h.update(line)
            r=json.loads(line)
            chk(r["seq"]==n,"SEQ_BAD")
            ind.feed(r)
    ind.finish()
    chk(raw_h.hexdigest()==manifest["raw_sha256"],"RAW_SHA256_MISMATCH")
    chk(n==manifest["rows"],"RAW_ROW_COUNT_MISMATCH")
    for k in "ABC":
        chk(ind.good[k]==expected["comparison"][k]["good"],
            "CAUSAL_GRID_MISMATCH_"+k+":"+str(ind.good[k])+" vs "+str(expected["comparison"][k]["good"]))
        chk(ind.stale[k]==expected["comparison"][k]["stale_resets"],
            "STALE_COUNT_MISMATCH_"+k)
    chk(ind.count["l50_snapshot"]==expected["l50_snapshot_count"],
        "L50_SNAPSHOT_COUNT_MISMATCH")
    chk(ind.count["l50_delta"]==expected["l50_delta_count"],
        "L50_DELTA_COUNT_MISMATCH")
    chk(ind.count["mexc_book"]==expected["mexc_books"],"MEXC_COUNT_MISMATCH")
    chk(ind.count["l1_duplicate"]==expected["l1_duplicate_no_refresh"],
        "L1_DUPLICATE_COUNT_MISMATCH")
    result={"audit":"INDEPENDENT_RECEIVE_ORDER_RECONSTRUCTION_PASS",
            "rows":n,"raw_sha256":raw_h.hexdigest(),
            "paired_good_seconds":{k:ind.good[k] for k in "ABC"},
            "l50_snapshots":ind.count["l50_snapshot"],
            "l50_deltas":ind.count["l50_delta"],
            "mexc_books":ind.count["mexc_book"],
            "l1_duplicate":ind.count["l1_duplicate"],
            "parser_invalid":len(ind.invalid),
            "source_verdict_original":expected["source_verdict"],
            "economic_verdict":"ECONOMIC_INSUFFICIENT","live_verdict":"NO_LIVE_GO"}
    return result

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: audit_receipts.py RAW_EVIDENCE_FOLDER")
    try:print(json.dumps(audit(sys.argv[1]),indent=2))
    except Exception as exc:
        print(json.dumps({"audit":"FAILED","reason":str(exc)}))
        raise SystemExit(2)
