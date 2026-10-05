#!/usr/bin/env python3
import csv,json,statistics,time,urllib.parse,urllib.request
from datetime import datetime,timezone,timedelta
from pathlib import Path

EVENTS=[
("WIF","2024-03-05T10:01:00Z","https://www.binance.com/en/support/announcement/detail/90ad67fe5be7483ea058191bfde677e4"),
("AXL","2024-03-01T07:18:00Z","https://www.binance.com/en/support/announcement/detail/2eb66d061d214c31a096cff35ede9360"),
("TAO","2024-04-11T06:43:00Z","https://www.binance.com/en/support/announcement/detail/dd856efc9c1a4a209eb48992e190e4d6"),
("NEIRO","2024-09-16T05:45:00Z","https://www.binance.com/en-AE/support/announcement/detail/4336ae4908154736acff8302509f7a05"),
("TURBO","2024-09-16T05:45:00Z","https://www.binance.com/en-AE/support/announcement/detail/4336ae4908154736acff8302509f7a05"),
("1MBABYDOGE","2024-09-16T05:45:00Z","https://www.binance.com/en-AE/support/announcement/detail/4336ae4908154736acff8302509f7a05"),
("COW","2024-11-06T05:10:00Z","https://www.binance.com/en/support/announcement/detail/2faa229be2ba4b758bbeb1859f63ba36"),
("CETUS","2024-11-06T05:10:00Z","https://www.binance.com/en/support/announcement/detail/2faa229be2ba4b758bbeb1859f63ba36"),
("ACT","2024-11-11T05:39:00Z","https://www.binance.com/en/support/announcement/detail/d16d96c136154680a6373225d592bca1"),
("PNUT","2024-11-11T05:39:00Z","https://www.binance.com/en/support/announcement/detail/d16d96c136154680a6373225d592bca1"),
("ACX","2024-12-06T08:34:00Z","https://www.binance.com/en/support/announcement/detail/b8b988973b88493192f2e43ba26da331"),
("ORCA","2024-12-06T08:34:00Z","https://www.binance.com/en/support/announcement/detail/b8b988973b88493192f2e43ba26da331"),
("VELODROME","2024-12-13T08:07:00Z","https://www.binance.com/en/support/announcement/detail/4f8e9e0b5dd54e9095b7d718f289d9d4"),
]
ALIASES={"1MBABYDOGE":["BABYDOGE","1MBABYDOGE"],"VELODROME":["VELODROME"],"NEIRO":["NEIROETH","NEIRO"]}

def get(url):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabResearch/1.0"})
    with urllib.request.urlopen(req,timeout=25) as r: return json.load(r)

def bybit(sym,start,end):
    u="https://api.bybit.com/v5/market/kline?"+urllib.parse.urlencode({"category":"spot","symbol":sym+"USDT","interval":"1","start":start,"end":end,"limit":1000})
    j=get(u)
    if j.get("retCode")!=0:return []
    out=[]
    for x in j.get("result",{}).get("list",[]): out.append((int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])))
    return sorted(out)

def okx(sym,start,end):
    u="https://www.okx.com/api/v5/market/history-candles?"+urllib.parse.urlencode({"instId":sym+"-USDT","bar":"1m","after":end+1,"before":start-1,"limit":300})
    j=get(u); out=[]
    for x in j.get("data",[]): out.append((int(x[0]),float(x[1]),float(x[2]),float(x[3]),float(x[4]),float(x[5])))
    return sorted(out)

def gate(sym,start,end):
    fr=start//1000; to=end//1000
    u="https://api.gateio.ws/api/v4/spot/candlesticks?"+urllib.parse.urlencode({"currency_pair":sym+"_USDT","interval":"1m","from":fr,"to":to})
    j=get(u);out=[]
    if isinstance(j,dict):return []
    for x in j:
        # gate: timestamp, quote_volume, close, high, low, open, base_volume...
        out.append((int(x[0])*1000,float(x[5]),float(x[3]),float(x[4]),float(x[2]),float(x[6]) if len(x)>6 else float(x[1])))
    return sorted(out)

def gate_bulk(sym,t0):
    # Official Gate bulk public trade archive; reconstruct 1m OHLCV locally.
    import csv as _csv, gzip as _gzip, io as _io
    dt=datetime.fromtimestamp(t0/1000,timezone.utc)
    ym=dt.strftime("%Y%m")
    url=f"https://download.gatedata.org/spot/deals/{ym}/{sym}_USDT-{ym}.csv.gz"
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 CryptoLabResearch/1.0"})
    try:
      with urllib.request.urlopen(req,timeout=45) as r: raw=_gzip.decompress(r.read()).decode("utf-8",errors="replace")
    except Exception: return []
    mins={}
    for row in _csv.reader(_io.StringIO(raw)):
      try:
        ts=int(float(row[0])*1000); price=float(row[2]); amt=float(row[3])
      except Exception: continue
      if not (t0-25*3600_000 <= ts <= t0+65*60_000): continue
      m=(ts//60000)*60000
      if m not in mins: mins[m]=[m,price,price,price,price,0.0]
      b=mins[m]; b[2]=max(b[2],price); b[3]=min(b[3],price); b[4]=price; b[5]+=amt
    return [tuple(mins[k]) for k in sorted(mins)]

def fetch_venue(ticker,t0):
    aliases=ALIASES.get(ticker,[ticker])
    # Technical remediation V0.1.1: API candle caps require chunked windows.
    # Science is unchanged: fetch a 60m witness around T-24h, a T-23h..T-1h
    # baseline in <=1000m chunks, and the event window separately.
    windows=[
      (t0-25*3600_000,t0-24*3600_000+10*60_000),
      (t0-23*3600_000,t0-19*3600_000),
      (t0-19*3600_000,t0-15*3600_000),
      (t0-15*3600_000,t0-11*3600_000),
      (t0-11*3600_000,t0-7*3600_000),
      (t0-7*3600_000,t0-3*3600_000),
      (t0-3*3600_000,t0-3600_000),
      (t0-10*60_000,t0+65*60_000),
    ]
    for venue,fn in [("BYBIT",bybit),("OKX",okx),("GATE",gate)]:
      for a in aliases:
        try:
          merged={}
          for ws,we in windows:
            for b in fn(a,ws,we): merged[b[0]]=b
            time.sleep(.10)
          bars=sorted(merged.values())
          if bars:
            pre=[b for b in bars if b[0] < (t0//60000)*60000]
            old=[b for b in bars if b[0] <= t0-24*3600_000+10*60_000]
            if pre and old:return venue,a,bars
        except Exception as e:
          print(f'DIAG {ticker} {venue} {a}: {type(e).__name__}: {e}')
        time.sleep(.15)
    # Frozen venue hierarchy ends at Gate. This is a source-only fallback
    # for the SAME Gate venue using Gate's official bulk historical archive.
    for a in aliases:
      bars=gate_bulk(a,t0)
      if bars:
        minute=(t0//60000)*60000
        pre=[b for b in bars if b[0] < minute]
        old=[b for b in bars if b[0] <= t0-24*3600_000+10*60_000]
        if pre and old:return "GATE_BULK",a,bars
    return None,None,[]

def analyze(ticker,ts,url):
    dt=datetime.fromisoformat(ts.replace("Z","+00:00")); t0=int(dt.timestamp()*1000); minute=(t0//60000)*60000
    venue,alias,bars=fetch_venue(ticker,t0)
    if not bars:return {"ticker":ticker,"t0":ts,"status":"NO_VALID_PRET0_VENUE","source":url}
    d={b[0]:b for b in bars}; pre=[b for b in bars if b[0] < minute]
    p0=pre[-1][4]
    def close_after(n):
      targets=[b for b in bars if minute <= b[0] <= minute+n*60000]
      return targets[-1][4] if targets else None
    row={"ticker":ticker,"t0":ts,"status":"VALID","venue":venue,"venue_symbol":alias+"USDT","p0":p0,"source":url}
    for n in [1,5,15,60]:
      c=close_after(n)
      row[f"r{n}"]=((c/p0)-1) if c else None
      win=[b for b in bars if minute<=b[0]<=minute+n*60000]
      row[f"mfe{n}"]=max((b[2]/p0-1 for b in win),default=None)
      row[f"mae{n}"]=min((b[3]/p0-1 for b in win),default=None)
    first5=[b for b in bars if minute<=b[0]<minute+5*60000]
    v5=sum(b[5] for b in first5)
    hist=[b for b in bars if t0-24*3600_000<=b[0]<t0-3600_000]
    chunks=[]
    for i in range(0,len(hist)-4,5): chunks.append(sum(x[5] for x in hist[i:i+5]))
    row["volume_shock_5m"]=v5/statistics.median(chunks) if chunks and statistics.median(chunks)>0 else None
    return row

rows=[analyze(*e) for e in EVENTS]
valid=[r for r in rows if r["status"]=="VALID" and r.get("r15") is not None]
def med(k): return statistics.median([r[k] for r in valid if r.get(k) is not None]) if valid else None
n=len(valid); hit=sum(r["r15"]>0 for r in valid)/n if n else 0
loo_ok=n>1 and all(statistics.median([x["r15"] for j,x in enumerate(valid) if j!=i])>0 for i in range(n))
pos=[max(0,r["r15"]) for r in valid]; concentration=(max(pos)/sum(pos)) if sum(pos)>0 else 1
survive=n>=12 and med("r15")>.0075 and hit>=.65 and med("r5")>.005 and med("volume_shock_5m")>=2 and loo_ok and concentration<=.35
verdict="SURVIVES_DISCOVERY" if survive else ("SOURCE_BLOCKED" if n<12 else "NO_EDGE_DISCOVERY")
out=Path("research/binance_listing_information_cascade/results");out.mkdir(parents=True,exist_ok=True)
fields=sorted(set().union(*(r.keys() for r in rows)))
with open(out/"v01_events.csv","w",newline="") as f:
 w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
summary={"verdict":verdict,"n_valid":n,"median_r5":med("r5"),"median_r15":med("r15"),"hit_rate_r15":hit,"median_volume_shock_5m":med("volume_shock_5m"),"loo_positive":loo_ok,"positive_concentration":concentration}
(out/"v01_summary.json").write_text(json.dumps(summary,indent=2))
md="# BINANCE LISTING INFORMATION CASCADE V0.1 — RESULT\n\n"+json.dumps(summary,indent=2)+"\n\nFrozen gate: V01_PRE_OUTCOME_FREEZE_2026-10-05.md\n"
(out/"V01_RESULT.md").write_text(md)
print(json.dumps(summary,indent=2))
