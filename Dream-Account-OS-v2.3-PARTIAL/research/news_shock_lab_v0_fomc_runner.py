from __future__ import annotations
import csv, hashlib, json, math, zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from io import TextIOWrapper
from pathlib import Path
from statistics import mean, median
from zoneinfo import ZoneInfo

FREEZE_PATH = Path(__file__).with_name("NEWS_SHOCK_LAB_V0_FOMC_EVENT_STUDY_FREEZE.json")
EXPECTED_FREEZE_FINGERPRINT = "ca2c9dae37a6e7ca53211388c19e2762a9e9a1640655af74c9560071b9234c78"
NY = ZoneInfo("America/New_York")
ONE_MIN_MS = 60_000
SYMBOLS = ("BTCUSDT","ETHUSDT")
POST_WINDOWS = (5,15,30,60,120,240)
PRE_WINDOWS = (5,15,60)
CONTROL_LAGS = (7,14,21,28)

@dataclass(frozen=True)
class Bar:
    open_time:int
    open:float
    high:float
    low:float
    close:float
    volume:float
    trades:int
    taker_buy_base:float

def canonical_hash(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(",",":"), ensure_ascii=False).encode()).hexdigest()

def load_freeze():
    raw=json.loads(FREEZE_PATH.read_text())
    supplied=raw.get("fingerprint")
    unsigned=dict(raw); unsigned.pop("fingerprint",None)
    if supplied!=EXPECTED_FREEZE_FINGERPRINT or canonical_hash(unsigned)!=supplied:
        raise PermissionError("freeze fingerprint mismatch")
    if raw["governance"]["no_2026"] is not True:
        raise PermissionError("2026 guard drift")
    return raw

def event_dt(day:str)->datetime:
    d=date.fromisoformat(day)
    return datetime(d.year,d.month,d.day,14,0,tzinfo=NY).astimezone(timezone.utc)

def norm_ts(v:int)->int:
    return v//1000 if abs(v)>=100_000_000_000_000 else v

def parse_checksum(text:str, filename:str)->str:
    parts=text.strip().split()
    if len(parts)<2:
        raise ValueError("invalid checksum")
    digest=parts[0].lower(); fname=parts[-1].lstrip("*")
    if fname!=filename or len(digest)!=64:
        raise ValueError("checksum filename/format mismatch")
    return digest

def parse_day(root:Path,symbol:str,day:str)->dict[int,Bar]:
    fn=f"{symbol}-1m-{day}.zip"
    zp=root/symbol/fn; cp=root/symbol/(fn+".CHECKSUM")
    raw=zp.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=parse_checksum(cp.read_text(),fn):
        raise ValueError(f"checksum mismatch {symbol} {day}")
    member=fn[:-4]+".csv"; out={}
    with zipfile.ZipFile(zp) as zf:
        if zf.namelist()!=[member]:
            raise ValueError(f"zip member mismatch {symbol} {day}")
        with zf.open(member) as bio:
            rd=csv.reader(TextIOWrapper(bio,encoding="utf-8-sig",newline=""))
            for row in rd:
                if not row or not row[0].strip().lstrip("-").isdigit():
                    continue
                if len(row)!=12: raise ValueError("field count")
                ot=norm_ts(int(row[0])); op,hi,lo,cl,vol=map(float,row[1:6]); trades=int(row[8]); tb=float(row[9])
                if ot%ONE_MIN_MS!=0 or not all(math.isfinite(x) for x in (op,hi,lo,cl,vol,tb)):
                    raise ValueError("invalid row")
                if min(op,hi,lo,cl)<=0 or vol<0 or trades<0 or tb<0 or tb>vol+max(1e-12,abs(vol)*1e-10):
                    raise ValueError("invalid values")
                out[ot]=Bar(ot,op,hi,lo,cl,vol,trades,tb)
    return out

def sign(x:float,eps:float=1e-15)->int:
    return 1 if x>eps else (-1 if x<-eps else 0)

def ret(op0:float, op1:float)->float:
    return op1/op0-1.0

def agg_flow(bars:list[Bar])->float|None:
    v=sum(b.volume for b in bars)
    if v<=0:return None
    return (2*sum(b.taker_buy_base for b in bars)-v)/v

def event_metrics(series:dict[int,Bar], ts:int):
    if ts not in series: raise ValueError("event minute missing")
    base=series[ts].open; out={}
    for h in POST_WINDOWS:
        end=ts+h*ONE_MIN_MS
        if end not in series: raise ValueError(f"post endpoint missing {h}")
        window=[series[ts+i*ONE_MIN_MS] for i in range(h)]
        if len(window)!=h: raise ValueError("post window gap")
        out[f"ret_{h}m"]=ret(base,series[end].open)
        out[f"abs_ret_{h}m"]=abs(out[f"ret_{h}m"])
        out[f"volume_{h}m"]=sum(b.volume for b in window)
        out[f"trades_{h}m"]=sum(b.trades for b in window)
        out[f"flow_{h}m"]=agg_flow(window)
    for h in PRE_WINDOWS:
        start=ts-h*ONE_MIN_MS
        if start not in series: raise ValueError(f"pre endpoint missing {h}")
        out[f"pre_ret_{h}m"]=ret(series[start].open,base)
    out["reversal_5_60"]=sign(out["ret_5m"])*sign(out["ret_60m"])==-1
    out["reversal_15_120"]=sign(out["ret_15m"])*sign(out["ret_120m"])==-1
    out["flow_persist_5_15"]=(sign(out["flow_5m"] or 0)!=0 and sign(out["flow_5m"] or 0)==sign(out["flow_15m"] or 0))
    return out

def required_days(freeze):
    events=set(freeze["event_contract"]["events"]); days=set(events)
    for e in events:
        d=date.fromisoformat(e)
        for lag in CONTROL_LAGS:
            c=(d-timedelta(days=lag)).isoformat()
            if c not in events: days.add(c)
    return tuple(sorted(days))

def summarize(rows):
    summary={}
    for symbol in SYMBOLS:
        s=[r for r in rows if r["symbol"]==symbol]; one={"events":len(s)}
        for h in POST_WINDOWS:
            vals=[r[f"ret_{h}m"] for r in s]
            one[f"{h}m"]={
                "mean_return":mean(vals),"median_return":median(vals),
                "mean_abs_return":mean(abs(x) for x in vals),
                "up_rate":sum(x>0 for x in vals)/len(vals),
                "down_rate":sum(x<0 for x in vals)/len(vals),
                "median_volume_ratio_vs_controls":median(r[f"volume_ratio_{h}m"] for r in s),
                "median_trade_count_ratio_vs_controls":median(r[f"trade_ratio_{h}m"] for r in s),
                "mean_flow_imbalance":mean(r[f"flow_{h}m"] for r in s if r[f"flow_{h}m"] is not None)
            }
        one["prepositioning"]={f"mean_pre_return_{h}m":mean(r[f"pre_ret_{h}m"] for r in s) for h in PRE_WINDOWS}
        one["reversal_5m_vs_60m_rate"]=sum(r["reversal_5_60"] for r in s)/len(s)
        one["reversal_15m_vs_120m_rate"]=sum(r["reversal_15_120"] for r in s)/len(s)
        one["flow_persistence_5m_to_15m_rate"]=sum(r["flow_persist_5_15"] for r in s)/len(s)
        summary[symbol]=one
    return summary

def run(root:Path,out_path:Path):
    freeze=load_freeze(); events=tuple(freeze["event_contract"]["events"]); event_set=set(events)
    cache={s:{} for s in SYMBOLS}; days=required_days(freeze)
    for s in SYMBOLS:
        for d in days: cache[s][d]=parse_day(root,s,d)
    rows=[]
    for s in SYMBOLS:
        for e in events:
            ts=int(event_dt(e).timestamp()*1000); em=event_metrics(cache[s][e],ts); controls=[]; ed=date.fromisoformat(e)
            for lag in CONTROL_LAGS:
                cd=(ed-timedelta(days=lag)).isoformat()
                if cd in event_set: continue
                d=date.fromisoformat(cd); cdt=datetime(d.year,d.month,d.day,14,0,tzinfo=NY).astimezone(timezone.utc); cts=int(cdt.timestamp()*1000)
                controls.append(event_metrics(cache[s][cd],cts))
            if len(controls)<3: raise ValueError("insufficient matched controls")
            row={"symbol":s,"event_date":e,"release_utc":event_dt(e).isoformat()}; row.update(em)
            for h in POST_WINDOWS:
                cv=mean(c[f"volume_{h}m"] for c in controls); ct=mean(c[f"trades_{h}m"] for c in controls)
                row[f"volume_ratio_{h}m"]=em[f"volume_{h}m"]/cv if cv>0 else None
                row[f"trade_ratio_{h}m"]=em[f"trades_{h}m"]/ct if ct>0 else None
            rows.append(row)
    top60=sorted(rows,key=lambda r:abs(r["ret_60m"]),reverse=True)[:12]
    body={
        "document_type":"NEWS_SHOCK_LAB_V0_FOMC_EVENT_STUDY_RECEIPT","version":"0.1","status":"DIAGNOSTIC_COMPLETE",
        "authority":"HISTORICAL_EVENT_STUDY_ONLY_NO_TRADING_AUTHORITY","freeze_fingerprint":EXPECTED_FREEZE_FINGERPRINT,
        "events_per_symbol":len(events),"symbols":list(SYMBOLS),"timeframe":"1m","summary":summarize(rows),
        "largest_abs_60m_moves":[{"symbol":r["symbol"],"event_date":r["event_date"],"ret_5m":r["ret_5m"],"ret_15m":r["ret_15m"],"ret_60m":r["ret_60m"],"ret_240m":r["ret_240m"],"flow_15m":r["flow_15m"],"volume_ratio_15m":r["volume_ratio_15m"]} for r in top60],
        "all_event_rows":rows,
        "guards":{"live_trading":False,"exchange_mutation":False,"holdout_2026_accessed":False,"directional_rule_defined":False}
    }
    body["fingerprint"]=canonical_hash(body); out_path.parent.mkdir(parents=True,exist_ok=True); out_path.write_text(json.dumps(body,indent=2,sort_keys=True)+"\n"); return body

if __name__=="__main__":
    import sys
    if len(sys.argv)!=3: raise SystemExit("usage: runner <raw_root> <out_receipt>")
    receipt=run(Path(sys.argv[1]),Path(sys.argv[2]))
    print(json.dumps({"status":receipt["status"],"fingerprint":receipt["fingerprint"],"summary":receipt["summary"],"largest_abs_60m_moves":receipt["largest_abs_60m_moves"]},indent=2,sort_keys=True))
