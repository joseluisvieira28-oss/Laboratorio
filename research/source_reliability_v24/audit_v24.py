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
        self.accepted_seconds={k:[] for k in 'ABC'}
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
            if ok:
                self.good[k]+=1
                self.accepted_seconds[k].append(t)
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
        while self.nexttick<t and self.nexttick<=7200:
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
        if self.nexttick==t and self.nexttick<=7200:
            self.tick(t);self.nexttick+=1
    def finish(self):
        while self.nexttick<=7200:self.tick(self.nexttick);self.nexttick+=1


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


from collections import deque

class LiquidationStress:
    """Raw Bybit child events: independent source validation and incident sampling."""
    def __init__(self):
        self.unique=set()
        self.duplicates=0
        self.events=[]
        self.by_side={"Buy":deque(),"Sell":deque()}
        self.clusters=[]
        self.invalid=[]
        self.frames=0

    def feed(self,r):
        if r["venue"]!="bybit" or r["kind"]!="frame":
            return
        try:
            m=json.loads(r["raw"])
        except (ValueError,TypeError):
            return  # source-level parser handles malformed book/transport frames
        if m.get("topic")!="allLiquidation.BTCUSDT":
            return
        self.frames+=1
        t=r["elapsed"]
        try:
            chk(m.get("type")=="snapshot","LIQ_TYPE")
            ts=int(m["ts"])
            chk(r["utc_ms"]-1500<=ts<=r["utc_ms"]+250,"LIQ_PUBLISHER_CLOCK")
            children=m["data"]
            chk(isinstance(children,list),"LIQ_CHILDREN_NOT_LIST")
            for d in children:
                chk(isinstance(d,dict) and d.get("s")=="BTCUSDT","LIQ_SYMBOL")
                side=d.get("S")
                chk(side in ("Buy","Sell"),"LIQ_DIRECTION")
                t_event=int(d["T"])
                chk(r["utc_ms"]-1500<=t_event<=r["utc_ms"]+250,"LIQ_EVENT_CLOCK")
                size=val(d["v"]);price=val(d["p"])
                key=(t_event,"BTCUSDT",side,str(d["v"]),str(d["p"]))
                if key in self.unique:
                    self.duplicates+=1
                    continue
                self.unique.add(key)
                notional=size*price
                self.events.append((t,side,notional,t_event))
                rolling=self.by_side[side]
                while rolling and rolling[0][0]<t-10:
                    rolling.popleft()
                rolling.append((t,notional))
                strength=sum(v for _,v in rolling)
                # An explicit 60s separation suppresses overlapping clusters.
                if len(rolling)>=2 and strength>=Decimal("100000"):
                    if not self.clusters or t-self.clusters[-1]["center"]>=60:
                        self.clusters.append({"center":t,"side":side,
                            "children":len(rolling),"proxy_usdt":str(strength)})
        except (AuditFail,ValueError,TypeError,KeyError,IndexError) as exc:
            self.invalid.append({"receipt":r["seq"],"error":str(exc)})


def stress_brackets(parity,clusters):
    """Diagnostic only: future L1 anchor used RETROSPECTIVELY, never as trading input."""
    result=[]
    for c in clusters:
        counts=Counter()
        center=c["center"]
        for segment,book in parity.l50.items():
            anchors=parity.l1[segment]
            anchor_seq=[x[0] for x in anchors]
            for s,t,bid,ask in book:
                if abs(t-center)>10:continue
                counts["l50_book_frames"]+=1
                i=bisect_right(anchor_seq,s)
                if i==0 or i>=len(anchors):
                    counts["no_two_anchor_bracket"]+=1;continue
                left,right=anchors[i-1],anchors[i]
                if (left[2],left[3])!=(right[2],right[3]):
                    counts["moving_l1_unverifiable"]+=1;continue
                if abs(t-left[1])>.2 or abs(right[1]-t)>.2:
                    counts["time_not_within_200ms"]+=1;continue
                counts["stable_200ms"]+=1
                if (bid,ask)==(left[2],left[3]):
                    counts["stable_exact_match"]+=1
                else:
                    counts["stable_mismatch"]+=1
        result.append({**c,**dict(counts)})
    return result


def window_quality(good_seconds, minutes=120):
    """Fixed 600-second windows; exact one-second bins, no cherry-picked exclusions."""
    size=600; windows=[]
    for i in range(minutes//10):
        count=sum(1 for t in good_seconds if i*size<t<=(i+1)*size)
        windows.append({"window_utc_relative":i,"start_s":i*size,"end_s":(i+1)*size,
                        "joint_good":count,"fraction":count/size})
    return windows,[w["window_utc_relative"] for w in windows if w["joint_good"]<540]


def audit(path):
    root=Path(path)
    manifest=json.loads((root/"manifest.json").read_text())
    report=json.loads((root/"report.json").read_text())
    raw=root/"raw.jsonl.gz"
    chk(raw.exists(),"MISSING_ORIGINAL_RAW")
    artifact=root.parent/"research"
    protocol=artifact/"source_reliability_v24"/"PROTOCOL_FROZEN.md"
    collector=artifact/"source_reliability_v22"/"compare.py"
    chk(protocol.exists() and collector.exists(),"MISSING_CAPTURED_PROTOCOL_OR_SOURCE")
    chk(sha(protocol.read_bytes())==manifest["protocol_sha256"],"PROTOCOL_HASH_MISMATCH")
    chk(sha(collector.read_bytes())==manifest["source_sha256"],"CAPTURE_SOURCE_HASH_MISMATCH")
    chk(sha(raw.read_bytes())==manifest["gzip_sha256"],"GZIP_SHA_MISMATCH")

    replay=Independent();parity=Parity();liquidations=LiquidationStress()
    hasher=hashlib.sha256();row_count=0;connections=Counter();end_reason=None
    with gzip.open(raw,"rb") as stream:
        for line in stream:
            row_count+=1
            hasher.update(line)
            r=json.loads(line)
            chk(r["seq"]==row_count,"RAW_RECEIPT_GAP")
            replay.feed(r)
            parity.feed(r)
            liquidations.feed(r)
            if r["kind"]=="connect":
                connections[r["venue"]]+=1
            if r["venue"]=="system" and r["kind"]=="end":
                end_reason=r["raw"]
    replay.finish()
    chk(hasher.hexdigest()==manifest["raw_sha256"],"UNCOMPRESSED_RAW_HASH_MISMATCH")
    chk(row_count==manifest["rows"],"ORIGINAL_ROW_COUNT_MISMATCH")
    for name in "ABC":
        chk(replay.good[name]==report["comparison"][name]["good"],
            "ASOF_COVERAGE_MISMATCH_"+name+": "+str(replay.good[name])+" vs "+str(report["comparison"][name]["good"]))
    chk(replay.count["l50_delta"]==report["l50_delta_count"],"L50_DELTA_REPLAY_MISMATCH")
    chk(replay.count["l50_snapshot"]==report["l50_snapshot_count"],"L50_SNAPSHOT_REPLAY_MISMATCH")
    chk(replay.count["mexc_book"]==report["mexc_books"],"MEXC_REPLAY_MISMATCH")

    bracket=parity.measure()
    stable=bracket["stable_brackets"]
    match=bracket["price_parity_match"]
    frac=(match/stable) if stable else 0.
    windows,bad_windows=window_quality(replay.accepted_seconds["C"])
    stress=stress_brackets(parity,liquidations.clusters)
    full_capture=(float(report["elapsed_seconds"])>=7200 and end_reason=="WALL_LIMIT"
                  and manifest.get("end_reason")=="WALL_LIMIT"
                  and report.get("grid_seconds")==7200)
    quality=(full_capture and replay.good["C"]>=6840 and not bad_windows
             and not replay.invalid and not parity.errors
             and not liquidations.invalid
             and connections["bybit"] in (1,2) and connections["mexc"] in (1,2)
             and parity.gaps==0 and parity.sequence_reversals==0
             and parity.badbooks==0
             and stable>=50000 and frac>=.999)
    sufficient=len(liquidations.clusters)>=2
    if not full_capture:
        verdict="SOURCE_STRESS_BLOCKED_RESOURCE_CAP" if end_reason=="STORAGE_CAP" else "SOURCE_STRESS_NOT_MEASURED"
    elif not quality:
        verdict="SOURCE_STRESS_BLOCKED"
    elif not sufficient:
        verdict="SOURCE_QUALITY_PASS_BUT_STRESS_INSUFFICIENT"
    else:
        verdict="SOURCE_STRESS_PASS_LIMITED"
    return {
        "source_verdict":verdict,
        "quality_gate_pass":bool(quality),
        "stress_sample_gate_pass":bool(sufficient),
        "economic_verdict":"ECONOMIC_INSUFFICIENT",
        "live_verdict":"NO_LIVE_GO",
        "rows":row_count,
        "source_duration_seconds":report["elapsed_seconds"],
        "grid_seconds":7200,
        "end_reason":end_reason,
        "original_sha256":hasher.hexdigest(),
        "joint_good_seconds":{k:replay.good[k] for k in "ABC"},
        "l50_good_fraction":replay.good["C"]/7200,
        "ten_minute_windows":windows,
        "bad_ten_minute_windows":bad_windows,
        "stable_bracket_count":stable,
        "stable_match_count":match,
        "stable_mismatch_count":bracket["price_parity_mismatch"],
        "stable_price_parity_fraction":frac,
        "unverifiable_moving_l1_brackets":bracket["moving_l1_anchor"],
        "unverifiable_no_bracket":bracket["no_seq_bracket"],
        "unverifiable_outside_200ms":bracket["not_within_200ms"],
        "l50_snapshot_count":parity.snapshots,
        "l50_delta_count":parity.deltas,
        "l50_u_gaps":parity.gaps,
        "l50_seq_reversals":parity.sequence_reversals,
        "l50_crossed_books":parity.badbooks,
        "bybit_l1_frames":parity.l1_frames,
        "mexc_full_depth_frames":replay.count["mexc_book"],
        "liquidation_frames":liquidations.frames,
        "liquidation_children_distinct":len(liquidations.events),
        "liquidation_duplicate_children":liquidations.duplicates,
        "liquidation_clusters_distinct":len(liquidations.clusters),
        "stress_cluster_details":stress[:30],
        "liquidation_invalid":liquidations.invalid[:20],
        "independent_parser_invalid":replay.invalid[:20],
        "book_integrity_errors":parity.errors[:20],
        "connection_segments":dict(connections),
        "pnl":"NOT_COMPUTED_SOURCE_ONLY",
        "actual_order_or_account_access":False
    }


if __name__=="__main__":
    if len(sys.argv)!=2:
        raise SystemExit("usage: python audit_v24.py ORIGINAL_ARTIFACT/v24_evidence")
    try:
        result=audit(sys.argv[1])
        print(json.dumps(result,sort_keys=True,indent=2))
    except Exception as exc:
        print(json.dumps({"audit":"FAILED","error":str(exc)}))
        raise SystemExit(2)
