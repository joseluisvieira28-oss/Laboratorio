#!/usr/bin/env python3
import csv, hashlib, io, json, math, os, random, statistics, time, zipfile
from collections import defaultdict, Counter
from datetime import datetime, timezone
from urllib.request import Request, urlopen

OUTDIR=os.path.join(os.path.dirname(__file__),"receipts")
os.makedirs(OUTDIR,exist_ok=True)

COMET="0xc3d688B66703497DAA19211EEdff47f25384cdc3"
B0=16_308_190
B1=21_525_890
ABSORB_TOPIC="0x9850ab1af75177e4a9201c65a2cf7976d5d28e40ef63494b44366f86b2f9412e"
BUY_TOPIC="0xf891b2a411b0e66a5f0a6ff1368670fefa287a13f541eb633a386a1a9cc7046b"
BLOCKSCOUT_RPC="https://eth.blockscout.com/api/eth-rpc"
BINANCE="https://data.binance.vision/data/spot/monthly/klines"

ASSET_MAP={
 "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2":"ETHUSDT",
 "0x514910771af9ca656af840dff83e8264ecf986ca":"LINKUSDT",
 "0x1f9840a85d5af5bf1d1762f925bdaddc4201f984":"UNIUSDT",
 "0xc00e94cb662c3520282e6f5717214004a7f26888":"COMPUSDT",
}
BENCH="BTCUSDT"
CUTOFF_MS=int(datetime(2025,1,1,tzinfo=timezone.utc).timestamp()*1000)

def sha256(b): return hashlib.sha256(b).hexdigest()

def fetch(url, method="GET", data=None, timeout=120):
    body=None if data is None else json.dumps(data).encode()
    h={"User-Agent":"CryptoLab-CompoundPersistence-Discovery-V0.1"}
    if body is not None: h["Content-Type"]="application/json"
    req=Request(url,data=body,headers=h,method=method)
    with urlopen(req,timeout=timeout) as r:
        b=r.read()
        return b,r.status,dict(r.headers)

def fetch_json(url, method="GET", data=None, timeout=120):
    b,s,h=fetch(url,method,data,timeout)
    return json.loads(b.decode()),sha256(b),s

def rpc(method,params):
    obj,_,_=fetch_json(BLOCKSCOUT_RPC,"POST",{"jsonrpc":"2.0","id":1,"method":method,"params":params})
    if "error" in obj: raise RuntimeError(f"{method}: {obj['error']}")
    return obj["result"]

def iv(v):
    if isinstance(v,int): return v
    s=str(v); return int(s,16) if s.startswith("0x") else int(s)

def words(data):
    s=str(data or "")
    if s.startswith("0x"): s=s[2:]
    if len(s)%64: raise RuntimeError("malformed event data")
    return [int(s[i:i+64],16) for i in range(0,len(s),64)]

def get_logs(topic0):
    out=[]; seen=set(); pages=[]; cur=B0; chunk=2_000_000
    while cur<=B1:
        stop=min(B1,cur+chunk-1)
        url=("https://eth.blockscout.com/api/?module=logs&action=getLogs"
             f"&fromBlock={cur}&toBlock={stop}&address={COMET}&topic0={topic0}")
        time.sleep(1.1)
        obj,h,_=fetch_json(url)
        rows=obj.get("result") if isinstance(obj,dict) else None
        if not isinstance(rows,list): raise RuntimeError(f"invalid Blockscout response {cur}-{stop}")
        if len(rows)>=1000: raise RuntimeError(f"possible Blockscout truncation {cur}-{stop}: {len(rows)}")
        pages.append({"from":cur,"to":stop,"count":len(rows),"sha256":h})
        for x in rows:
            k=(str(x.get("blockNumber","")).lower(),str(x.get("transactionHash","")).lower(),str(x.get("logIndex","")).lower())
            if k not in seen: seen.add(k); out.append(x)
        cur=stop+1
    return out,pages

def pos(x): return (iv(x.get("blockNumber",0)),iv(x.get("transactionIndex",0)),iv(x.get("logIndex",0)))

def asset_absorb(x):
    t=x.get("topics") or []
    return ("0x"+str(t[3])[-40:]).lower() if len(t)>3 else None

def asset_buy(x):
    t=x.get("topics") or []
    return ("0x"+str(t[2])[-40:]).lower() if len(t)>2 else None

def block_ts(block):
    obj=rpc("eth_getBlockByNumber",[hex(block),False])
    if not isinstance(obj,dict) or "timestamp" not in obj: raise RuntimeError(f"missing block {block}")
    return int(obj["timestamp"],16)

def month_key(ms):
    d=datetime.fromtimestamp(ms/1000,tz=timezone.utc)
    return f"{d.year}-{d.month:02d}"

cache={}
archive_receipts=[]

def load_month(symbol,ym):
    key=(symbol,ym)
    if key in cache: return cache[key]
    url=f"{BINANCE}/{symbol}/1m/{symbol}-1m-{ym}.zip"
    csum_url=url+".CHECKSUM"
    zb,_,_=fetch(url,timeout=180)
    cb,_,_=fetch(csum_url,timeout=60)
    expected=cb.decode().strip().split()[0].lower()
    actual=sha256(zb)
    if expected!=actual: raise RuntimeError(f"checksum mismatch {symbol} {ym}")
    z=zipfile.ZipFile(io.BytesIO(zb))
    names=z.namelist()
    if len(names)!=1: raise RuntimeError(f"unexpected zip members {symbol} {ym}: {names}")
    bars={}
    with z.open(names[0]) as raw:
        txt=io.TextIOWrapper(raw,encoding="utf-8")
        for row in csv.reader(txt):
            if len(row)<2: continue
            try:
                t=int(row[0]); o=float(row[1])
            except Exception:
                continue
            # 2023-2024 Binance Data Vision uses milliseconds.
            if t>10_000_000_000_000: t//=1000
            bars[t]=o
    archive_receipts.append({"symbol":symbol,"month":ym,"sha256":actual,"rows":len(bars)})
    cache[key]=bars
    return bars

def get_open(symbol,ms):
    return load_month(symbol,month_key(ms)).get(ms)

# Reconstruct exact lower-bound episodes from source events.
absorbs,absorb_pages=get_logs(ABSORB_TOPIC)
buys,buy_pages=get_logs(BUY_TOPIC)
events=[]
for x in absorbs:
    a=asset_absorb(x)
    if a not in ASSET_MAP: continue
    w=words(x.get("data"))
    events.append({"kind":"ABSORB","asset":a,"block":pos(x)[0],"txi":pos(x)[1],"logi":pos(x)[2],"amount":w[0]})
for x in buys:
    a=asset_buy(x)
    if a not in ASSET_MAP: continue
    w=words(x.get("data"))
    events.append({"kind":"BUY","asset":a,"block":pos(x)[0],"txi":pos(x)[1],"logi":pos(x)[2],"amount":w[1]})
events.sort(key=lambda e:(e["block"],e["txi"],e["logi"]))

by_asset=defaultdict(list)
for e in events: by_asset[e["asset"]].append(e)

episodes=[]
for asset,rows in sorted(by_asset.items()):
    inv=0; active=None; i=0
    while i<len(rows):
        block=rows[i]["block"]
        j=i
        block_rows=[]
        while j<len(rows) and rows[j]["block"]==block:
            block_rows.append(rows[j]); j+=1
        started_this_block=False
        start_amount=0
        for e in block_rows:
            if e["kind"]=="ABSORB":
                if inv==0:
                    active={"asset":asset,"symbol":ASSET_MAP[asset],"start_block":block,"start_amount_raw":0}
                    started_this_block=True
                inv+=e["amount"]
                if active is not None: active["start_amount_raw"]+=e["amount"]
            else:
                inv=max(0,inv-e["amount"])
                if inv==0 and active is not None:
                    active["clear_block"]=block
                    active["duration_blocks"]=block-active["start_block"]
                    if active["duration_blocks"]>0:
                        episodes.append(active)
                    active=None
        # If a new episode survived its start block, it remains active and is a valid future signal.
        i=j
    if active is not None:
        active["clear_block"]=None
        active["duration_blocks"]=None
        episodes.append(active)

# Deduplicate start block/asset defensively.
tmp={}
for e in episodes: tmp[(e["asset"],e["start_block"])]=e
episodes=sorted(tmp.values(),key=lambda e:(e["start_block"],e["asset"]))

rows=[]; excluded=[]; block_time_cache={}
for ep in episodes:
    b=ep["start_block"]
    if b not in block_time_cache: block_time_cache[b]=block_ts(b)
    ts=block_time_cache[b]
    entry_ms=((ts//60)+1)*60*1000
    exit_ms=entry_ms+24*60*60*1000
    if exit_ms>=CUTOFF_MS:
        excluded.append({"asset":ep["asset"],"start_block":b,"reason":"24H_WINDOW_CROSSES_2025"})
        continue
    sym=ep["symbol"]
    ae=get_open(sym,entry_ms); ax=get_open(sym,exit_ms)
    be=get_open(BENCH,entry_ms); bx=get_open(BENCH,exit_ms)
    if None in (ae,ax,be,bx) or min(ae,ax,be,bx)<=0:
        excluded.append({"asset":ep["asset"],"start_block":b,"symbol":sym,"reason":"MISSING_EXACT_BAR"})
        continue
    rel=(math.log(ax/ae)-math.log(bx/be))*10000.0
    dt=datetime.fromtimestamp(entry_ms/1000,tz=timezone.utc)
    iso=dt.isocalendar()
    rows.append({
      "asset_address":ep["asset"],"symbol":sym,"start_block":b,
      "block_timestamp_utc":datetime.fromtimestamp(ts,tz=timezone.utc).isoformat(),
      "entry_ms":entry_ms,"exit_ms":exit_ms,
      "entry_utc":dt.isoformat(),
      "year":dt.year,"month":f"{dt.year}-{dt.month:02d}",
      "iso_week":f"{iso.year}-W{iso.week:02d}",
      "duration_blocks":ep["duration_blocks"],
      "start_amount_raw":ep["start_amount_raw"],
      "rel_24h_bps":rel,
    })

N=len(rows)
assets=sorted({r["symbol"] for r in rows})
weeks=sorted({r["iso_week"] for r in rows})
years=sorted({r["year"] for r in rows})
sample_pass=N>=12 and len(assets)>=3 and len(weeks)>=8 and years==[2023,2024]

vals=[r["rel_24h_bps"] for r in rows]
mean=sum(vals)/N if N else None
median=statistics.median(vals) if vals else None
negative_fraction=(sum(v<0 for v in vals)/N) if N else None

asset_stats={}
for a in assets:
    x=[r["rel_24h_bps"] for r in rows if r["symbol"]==a]
    asset_stats[a]={"n":len(x),"mean_bps":sum(x)/len(x),"median_bps":statistics.median(x),"negative_fraction":sum(v<0 for v in x)/len(x)}
year_stats={}
for y in years:
    x=[r["rel_24h_bps"] for r in rows if r["year"]==y]
    year_stats[str(y)]={"n":len(x),"mean_bps":sum(x)/len(x)}

ci=[None,None]
boot=[]
if sample_pass:
    clusters={w:[r["rel_24h_bps"] for r in rows if r["iso_week"]==w] for w in weeks}
    rnd=random.Random(20260927)
    for _ in range(10000):
        drawn=[rnd.choice(weeks) for __ in weeks]
        x=[]
        for w in drawn: x.extend(clusters[w])
        boot.append(sum(x)/len(x))
    boot.sort()
    ci=[boot[int(0.025*(len(boot)-1))],boot[int(0.975*(len(boot)-1))]]

loo=[]
if N>1:
    total=sum(vals)
    loo=[(total-v)/(N-1) for v in vals]
loo_all_negative=bool(loo) and max(loo)<0
asset_negative_fraction=(sum(v["mean_bps"]<0 for v in asset_stats.values())/len(asset_stats)) if asset_stats else None
years_all_negative=(set(year_stats)=={"2023","2024"} and all(v["mean_bps"]<0 for v in year_stats.values()))

gates={
 "sample_pass":sample_pass,
 "mean_negative":mean is not None and mean<0,
 "bootstrap_upper_negative":ci[1] is not None and ci[1]<0,
 "asset_mean_negative_fraction_ge_75pct":asset_negative_fraction is not None and asset_negative_fraction>=0.75,
 "both_years_negative":years_all_negative,
 "leave_one_episode_out_all_negative":loo_all_negative,
}
if not sample_pass:
    verdict="DISCOVERY_INSUFFICIENT_SAMPLE"
elif all(gates.values()):
    verdict="DISCOVERY_MECHANISM_SUPPORTED"
else:
    verdict="DISCOVERY_FAIL_NO_SUPPORT"

receipt={
 "lab_id":"COMPOUND-INVENTORY-PERSISTENCE-001",
 "protocol":"COMPOUND_INVENTORY_PERSISTENCE_001_DISCOVERY_FREEZE_V0.1",
 "generated_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),
 "verdict":verdict,
 "population":{"source_episodes":len(episodes),"eligible":N,"excluded":excluded},
 "sample":{"n":N,"assets":assets,"asset_count":len(assets),"iso_week_count":len(weeks),"years":years},
 "primary":{
   "mean_rel_24h_bps":mean,"median_rel_24h_bps":median,
   "negative_fraction":negative_fraction,
   "cluster_bootstrap_95":[ci[0],ci[1]],
   "bootstrap_clusters":"UTC_ISO_WEEK","bootstrap_resamples":10000,"bootstrap_seed":20260927,
   "asset_negative_fraction":asset_negative_fraction,
   "leave_one_out_min_bps":min(loo) if loo else None,
   "leave_one_out_max_bps":max(loo) if loo else None,
 },
 "gates":gates,
 "by_asset":asset_stats,
 "by_year":year_stats,
 "counts_by_month":dict(sorted(Counter(r["month"] for r in rows).items())),
 "counts_by_week":dict(sorted(Counter(r["iso_week"] for r in rows).items())),
 "events":rows,
 "source":{
   "blockscout_pages":{"absorb":absorb_pages,"buy":buy_pages},
   "binance_archives":sorted(archive_receipts,key=lambda x:(x["symbol"],x["month"])),
   "block_timestamp_count":len(block_time_cache),
 },
 "interpretation":{
   "mechanism_test_only":True,
   "fees_or_pnl":False,
   "tier_promotion_allowed":False,
   "2025_opened":False,
 },
 "firewall":{
   "protected_2025_opened":False,"fees_computed":False,"pnl_computed":False,
   "live_trading":False,"orders":False,"exchange_mutation":False,
   "capital":False,"paid_data":False,"main_merge":False,"post_outcome_tuning":False
 }
}
pre=json.dumps(receipt,sort_keys=True,separators=(",",":")).encode()
receipt["receipt_sha256_pre_self_field"]=sha256(pre)
out=os.path.join(OUTDIR,"COMPOUND_INVENTORY_PERSISTENCE_DISCOVERY_RECEIPT_V0.1.json")
with open(out,"w",encoding="utf-8") as f:
    json.dump(receipt,f,sort_keys=True,indent=2); f.write("\n")
print(json.dumps({
 "verdict":verdict,"sample":receipt["sample"],"primary":receipt["primary"],
 "gates":gates,"by_asset":asset_stats,"by_year":year_stats,
 "excluded_count":len(excluded),"receipt_sha256_pre_self_field":receipt["receipt_sha256_pre_self_field"]
},sort_keys=True,indent=2))
print(f"receipt={out}")
