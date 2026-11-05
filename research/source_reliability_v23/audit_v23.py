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
    def _levels(self,rows,allowzero,allowthird=False):
        chk(isinstance(rows,list),"MISSING_PRICE_LEVELS")
        ps=[]
        for pair in rows:
            chk(isinstance(pair,list) and (len(pair)==2 or (allowthird and len(pair)==3)),"LEVEL_SHAPE")
            ps.append((val(pair[0]),val(pair[1],allowzero)))
        chk(len({x[0] for x in ps})==len(ps),"DUPLICATE_PRICE")
        return ps
    def _l1(self,msg,t):
        d=msg["data"]
        chk(msg["type"]=="snapshot" and d["s"]=="BTCUSDT","WRONG_L1")
        b=self._levels(d["b"],False);a=self._levels(d["a"],False)
        chk(b and a and b[0][0]<a[0][0],"BAD_L1_BBO")
        u=int(d["u"]);sig=(str(b[0][0]),str(a[0][0]),str(d["b"][0][1]),str(d["a"][0][1]))
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
            b=self._levels(d["bids"],False,True);a=self._levels(d["asks"],False,True)
            chk(len(b)>=5 and len(a)>=5,"MEXC_SHORT")
            chk([x[0] for x in b]==sorted([x[0] for x in b],reverse=True),"MEXC_B_SORT")
            chk([x[0] for x in a]==sorted([x[0] for x in a]),"MEXC_A_SORT")
            chk(b[0][0]<a[0][0],"MEXC_CROSSED")
            self.um=ver;self.clock["mexc"]=t;self.count["mexc_book"]+=1
    def feed(self,r):
        t=r["elapsed"];v=r["venue"]
        while self.nexttick<t and self.nexttick<=900:
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
        if self.nexttick==t and self.nexttick<=900:
            self.tick(t);self.nexttick+=1
    def finish(self):
        while self.nexttick<=900:self.tick(self.nexttick);self.nexttick+=1


# V2.3 extends the prior independent raw replayer, not the capture collector.
from bisect import bisect_right
from collections import defaultdict

class Parity:
    def __init__(self):
        self.segment=0;self.epoch=0
        self.bid={};self.ask={};self.u=None;self.seq=None;self.ready=False
        self.l1=defaultdict(list);self.l50=defaultdict(list)
        self.gaps=0;self.sequence_reversals=0;self.badbooks=0;self.u1_resets=0
        self.after_gap_without_snapshot=0;self.snapshots=0;self.deltas=0
        self.l1_frames=0;self.errors=[]
    def _reject(self,code,receipt):
        self.errors.append({"receipt_seq":receipt["seq"],"reason":code})
    def _levels(self,rows,side,allow_zero):
        if not isinstance(rows,list):raise AuditFail("LEVEL_ARRAY_MISSING")
        prices=[];out=[]
        for row in rows:
            if not isinstance(row,list) or len(row)!=2:raise AuditFail("LEVEL_SHAPE")
            price=val(row[0]);size=val(row[1],zero=allow_zero)
            prices.append(price);out.append((price,size))
        if len(prices)!=len(set(prices)):raise AuditFail("DUPLICATE_LEVELS")
        if prices!=sorted(prices,reverse=(side=="bids")):
            raise AuditFail("UNSORTED_LEVELS")
        return out
    def _frame(self,r):
        m=json.loads(r["raw"]);topic=m.get("topic")
        if topic not in ("orderbook.1.BTCUSDT","orderbook.50.BTCUSDT"):return
        d=m["data"];chk(d.get("s")=="BTCUSDT","SYMBOL")
        ts=int(m["ts"])
        chk(r["utc_ms"]-1500<=ts<=r["utc_ms"]+250,"SOURCE_TIMESTAMP")
        seq=int(d["seq"]);u=int(d["u"])
        if topic.startswith("orderbook.1."):
            chk(m.get("type")=="snapshot","L1_NOT_SNAPSHOT")
            b=self._levels(d["b"],"bids",False)
            a=self._levels(d["a"],"asks",False)
            chk(b and a and b[0][0]<a[0][0],"L1_CROSSED")
            previous=self.l1[self.segment]
            if previous and seq<previous[-1][0]:
                self.sequence_reversals+=1
                raise AuditFail("L1_SEQ_REVERSED")
            previous.append((seq,r["elapsed"],b[0][0],a[0][0]))
            self.l1_frames+=1
            return
        typ=m.get("type")
        if typ=="snapshot":
            bids=self._levels(d["b"],"bids",False)
            asks=self._levels(d["a"],"asks",False)
            chk(bids and asks and bids[0][0]<asks[0][0],"L50_SNAPSHOT_CROSSED")
            self.bid=dict(bids);self.ask=dict(asks)
            self.u=u;self.seq=seq;self.ready=True;self.snapshots+=1
        elif typ=="delta":
            if u==1:
                self.ready=False;self.bid={};self.ask={};self.u=None;self.seq=None
                self.u1_resets+=1
                return
            if not self.ready:
                self.after_gap_without_snapshot+=1
                return
            if seq<=self.seq:
                self.sequence_reversals+=1;self.ready=False
                raise AuditFail("L50_SEQ_REVERSED")
            if u!=self.u+1:
                self.gaps+=1;self.ready=False
                raise AuditFail("L50_U_NOT_CONSECUTIVE")
            bids=self._levels(d["b"],"bids",True)
            asks=self._levels(d["a"],"asks",True)
            outb=self.bid.copy();outa=self.ask.copy()
            for dest,entries in ((outb,bids),(outa,asks)):
                for price,size in entries:
                    if size==0:dest.pop(price,None)
                    else:dest[price]=size
            if not outb or not outa or max(outb)>=min(outa):
                self.badbooks+=1;self.ready=False
                raise AuditFail("L50_CROSSED_OR_EMPTY")
            self.bid=outb;self.ask=outa;self.u=u;self.seq=seq;self.deltas+=1
        else:raise AuditFail("L50_TYPE")
        self.l50[self.segment].append((seq,r["elapsed"],max(self.bid),min(self.ask)))
    def feed(self,r):
        if r["venue"]!="bybit":return
        kind=r["kind"]
        if kind=="connect":
            self.segment+=1
            self.ready=False;self.u=None;self.seq=None;self.bid={};self.ask={}
        elif kind in ("disconnect","fault"):
            self.ready=False;self.u=None;self.seq=None;self.bid={};self.ask={}
        elif kind=="frame":
            try:self._frame(r)
            except (AuditFail,ValueError,TypeError,KeyError,IndexError) as e:
                self._reject(str(e),r)
                self.ready=False
    def measure(self):
        counts=Counter()
        for seg,book in self.l50.items():
            anchors=self.l1[seg]
            seqs=[a[0] for a in anchors]
            for s,t,bid,ask in book:
                i=bisect_right(seqs,s)
                if i==0 or i>=len(anchors):
                    counts["no_seq_bracket"]+=1;continue
                left,right=anchors[i-1],anchors[i]
                if (left[2],left[3])!=(right[2],right[3]):
                    counts["moving_l1_anchor"]+=1;continue
                if abs(t-left[1])>.2 or abs(right[1]-t)>.2:
                    counts["not_within_200ms"]+=1;continue
                counts["stable_brackets"]+=1
                if (bid,ask)==(left[2],left[3]):
                    counts["price_parity_match"]+=1
                else:
                    counts["price_parity_mismatch"]+=1
                    if counts["price_parity_mismatch"]<=5:
                        counts["mismatch_sample_"+str(counts["price_parity_mismatch"])]={
                            "l50_seq":s,"l50_bbo":[str(bid),str(ask)],
                            "l1_bbo":[str(left[2]),str(left[3])],
                            "l50_receipt":t}
        return counts

def audit(path):
    root=Path(path);raw=root/"raw.jsonl.gz"
    chk(raw.is_file(),"MISSING_ORIGINAL_RAW")
    manifest=json.loads((root/"manifest.json").read_text())
    report=json.loads((root/"report.json").read_text())
    checked=root.parent/"research"
    frozen=checked/"source_reliability_v23"/"PROTOCOL_FROZEN.md"
    capture_source=checked/"source_reliability_v22"/"compare.py"
    chk(frozen.is_file() and capture_source.is_file(),"MISSING_ORIGINAL_CAPTURE_CODE")
    chk(sha(frozen.read_bytes())==manifest["protocol_sha256"],"FROZEN_PROTOCOL_HASH_MISMATCH")
    chk(sha(capture_source.read_bytes())==manifest["source_sha256"],"ORIGINAL_SOURCE_HASH_MISMATCH")
    chk(sha(raw.read_bytes())==manifest["gzip_sha256"],"ORIGINAL_GZIP_HASH_MISMATCH")
    ledger=Independent();parity=Parity()
    h=hashlib.sha256();rows=0;segments=Counter();end_reason=None
    with gzip.open(raw,"rb") as fh:
        for line in fh:
            rows+=1;h.update(line)
            r=json.loads(line)
            chk(r["seq"]==rows,"RECEIPT_ID_GAP")
            ledger.feed(r);parity.feed(r)
            if r["kind"]=="connect":
                segments[r["venue"]]+=1
            if r["venue"]=="system" and r["kind"]=="end":end_reason=r["raw"]
    ledger.finish()
    chk(h.hexdigest()==manifest["raw_sha256"],"ORIGINAL_UNCOMPRESSED_SHA_MISMATCH")
    chk(rows==manifest["rows"],"RECEIPT_COUNT_MISMATCH")
    for k in "ABC":
        chk(ledger.good[k]==report["comparison"][k]["good"],
           "CAUSAL_GRID_"+k+"_MISMATCH:"+str(ledger.good[k])+" vs "+
           str(report["comparison"][k]["good"])+
           " invalid="+repr(ledger.invalid[:3]))
    chk(ledger.count["l50_delta"]==report["l50_delta_count"],
        "DELTA_COUNT_MISMATCH")
    chk(ledger.count["l50_snapshot"]==report["l50_snapshot_count"],
        "SNAPSHOT_COUNT_MISMATCH")
    chk(ledger.count["mexc_book"]==report["mexc_books"],"MEXC_BOOK_MISMATCH")
    q=parity.measure()
    stable=q["stable_brackets"];match=q["price_parity_match"]
    pct=(match/stable) if stable else 0.0
    elapsed=float(report["elapsed_seconds"])
    source_ok=(elapsed>=900 and end_reason=="WALL_LIMIT"
              and ledger.good["C"]>=855 and not ledger.invalid and
              segments["bybit"]<=2 and segments["mexc"]<=2
              and parity.gaps==0 and parity.sequence_reversals==0
              and parity.badbooks==0 and not parity.errors
              and stable>=15000 and pct>=0.999)
    return {
        "source_verdict":"SOURCE_PARITY_PASS_LIMITED" if source_ok else "SOURCE_PARITY_BLOCKED",
        "relative_gain":"RELATIVE_GAIN_REPRODUCED" if ledger.good["C"]-ledger.good["A"]>=45
                         else "RELATIVE_GAIN_NOT_REPRODUCED",
        "economic_verdict":"ECONOMIC_INSUFFICIENT","live_verdict":"NO_LIVE_GO",
        "rows":rows,"original_raw_sha256":h.hexdigest(),
        "capture_wall_seconds":elapsed,"end_reason":end_reason,
        "joint_good_seconds":{k:ledger.good[k] for k in "ABC"},
        "l50_snapshots":parity.snapshots,"l50_deltas":parity.deltas,
        "l50_u_gaps":parity.gaps,"seq_reversals":parity.sequence_reversals,
        "crossed_books":parity.badbooks,"l50_service_u1":parity.u1_resets,
        "discarded_without_snapshot":parity.after_gap_without_snapshot,
        "l1_frames":parity.l1_frames,
        "stable_200ms_cross_seq_brackets":stable,
        "stable_price_parity_matches":match,
        "stable_price_parity_mismatches":q["price_parity_mismatch"],
        "stable_price_parity_fraction":pct,
        "uncomparable":{k:v for k,v in q.items() if k not in (
           "stable_brackets","price_parity_match","price_parity_mismatch")},
        "original_parser_invalid":len(ledger.invalid),
        "strict_parity_errors":parity.errors[:10],
        "connection_segments":dict(segments),
        "pnl":"NOT_COMPUTED_SOURCE_ONLY",
        "online_quote_or_trade_authority":False
    }

if __name__=="__main__":
    if len(sys.argv)!=2:raise SystemExit("usage: audit_v23.py ARTIFACT_ROOT/v23_evidence")
    try:print(json.dumps(audit(sys.argv[1]),indent=2,sort_keys=True))
    except Exception as e:
        print(json.dumps({"audit":"FAILED","reason":str(e)}))
        raise SystemExit(2)
