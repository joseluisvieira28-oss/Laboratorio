#!/usr/bin/env python3
from __future__ import annotations

import argparse, csv, hashlib, io, itertools, json, math, re, statistics, time, zipfile
from copy import deepcopy
from datetime import date, datetime, time as dt_time, timezone
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

import numpy as np
from bs4 import BeautifulSoup

getcontext().prec=50

ROOT=Path(__file__).parent
MASTER_PATH=ROOT/"NEWS_SHOCK_V03B_NFP_MASTER_CONSENSUS_V0.1.json"
FREEZE_PATH=ROOT/"NEWS_SHOCK_V03B_NFP_SURPRISE_STATISTICAL_FREEZE_V0.1.json"

EXPECTED_MASTER_FP="0133168b2355daaf71c2e3f1a0c7259e10f01b0c6b17b458c2771347bd5090c3"
EXPECTED_FREEZE_FP="29a983d6714934b068e130b0bd9598ca7b7090636567d814cd03c4a911982143"
SYMBOLS=("BTCUSDT","ETHUSDT")
BASE_URL="https://data.binance.vision/data/spot/daily/klines"
BLS_TEMPLATE="https://www.bls.gov/news.release/archives/empsit_{mmddyyyy}.htm"
NY=ZoneInfo("America/New_York")
ENTRY_LOCAL=dt_time(8,31)
EXIT_LOCAL=dt_time(8,45)
COST=Decimal("10")
ALPHA=Decimal("0.05")
TIMEFRAME_MS=60_000
CHECKSUM_RE=re.compile(r"^([0-9a-fA-F]{64})\s+\*?([^\s]+)\s*$")
BLS_UA="DreamAccountOS-NewsShock-NFP-V03B/0.1 research-only"
BINANCE_UA="DreamAccountOS-NewsShock-NFP-V03B/0.1 research-only"
MAX_EXACT=5_000_000
MC_REPS=1_000_000
MC_SEED=20260913

def canonical_hash(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()).hexdigest()

def load_hashed(path,expected,label):
    d=json.loads(Path(path).read_text(encoding="utf-8-sig"))
    supplied=d.get("fingerprint")
    unsigned=deepcopy(d); unsigned.pop("fingerprint",None)
    if supplied!=expected or canonical_hash(unsigned)!=expected:
        raise PermissionError(f"{label} fingerprint drift")
    return d

def sha256_bytes(b): return hashlib.sha256(b).hexdigest()
def sha256_file(p):
    h=hashlib.sha256()
    with Path(p).open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""):h.update(c)
    return h.hexdigest()

def fetch(url, allowed_prefixes, attempts=4):
    if not any(url.startswith(p) for p in allowed_prefixes):
        raise PermissionError(f"Network destination outside frozen authority: {url}")
    last=None
    for i in range(attempts):
        try:
            req=Request(url,headers={"User-Agent":BLS_UA if "bls.gov" in url else BINANCE_UA})
            with urlopen(req,timeout=60) as r:
                if getattr(r,"status",200)!=200: raise RuntimeError(f"HTTP {r.status}")
                raw=r.read()
            if not raw: raise RuntimeError("empty response")
            return raw
        except (HTTPError,URLError,TimeoutError,OSError,RuntimeError) as e:
            last=e
            if i<attempts-1: time.sleep(i+1)
    raise RuntimeError(f"Fetch failed: {url}: {last}")

def parse_dt_local(s,tz):
    z=timezone.utc if tz=="UTC" else ZoneInfo(tz)
    return datetime.fromisoformat(s).replace(tzinfo=z).astimezone(timezone.utc)

def merge_master_worklist(worklist,master):
    events=worklist.get("events")
    if not isinstance(events,list) or len(events)!=36: raise RuntimeError("Canonical worklist must contain 36 events")
    by={e.get("event_id"):e for e in events}
    expected={e["event_id"]:e for e in master["events"]}
    if set(by)!=set(expected): raise RuntimeError("Worklist event IDs differ from frozen master consensus")

    preexisting=0; filled=0
    for eid,m in expected.items():
        e=by[eid]
        mcons=m["consensus"]
        cons=e.get("consensus") or {}
        populated=[cons.get(k) is not None for k in ("payroll_k","unemployment_pct","ahe_mom_pct")]
        if any(populated):
            if not all(populated): raise RuntimeError(f"{eid}: partially populated prior consensus")
            for k in ("payroll_k","unemployment_pct","ahe_mom_pct"):
                if Decimal(str(cons[k]))!=Decimal(str(mcons[k])):
                    raise RuntimeError(f"{eid}: prior consensus conflicts with frozen master for {k}")
            preexisting+=1
        else:
            filled+=1
        # Verify frozen source precedes official release timestamp.
        p=m["provenance"]
        pub=parse_dt_local(p["published_at_local"],p["published_timezone"])
        rel=datetime.fromisoformat(e["release_utc"].replace("Z","+00:00"))
        if not pub<rel: raise RuntimeError(f"{eid}: frozen Reuters source is not pre-release")
        e["consensus"]=deepcopy(mcons)
        e["provenance"]={**deepcopy(p),"published_at_utc":pub.isoformat().replace("+00:00","Z")}
        e["status"]="CONSENSUS_COMPLETE_FROZEN_MASTER_REUTERS_PRE_RELEASE"

    return preexisting,filled

def bls_url(day):
    d=date.fromisoformat(day)
    if d.year not in (2022,2023,2024): raise PermissionError("BLS protected-year firewall")
    return BLS_TEMPLATE.format(mmddyyyy=d.strftime("%m%d%Y"))

def normalize_text(html):
    return re.sub(r"\s+"," ",BeautifulSoup(html,"html.parser").get_text(" ",strip=True)).strip()

def parse_bls_actual(day,raw):
    html=raw.decode("utf-8",errors="replace")
    text=normalize_text(html)
    d=date.fromisoformat(day)
    longdate=f"{d.strftime('%B')} {d.day}, {d.year}"
    if longdate.lower() not in text.lower():
        raise RuntimeError(f"{day}: BLS archive does not prove expected release date")
    if not re.search(r"8:30\s+a\.?m\.?\s*\(ET\)",text,re.I):
        raise RuntimeError(f"{day}: BLS archive does not prove 08:30 ET embargo")

    # Headline payroll first-release. Covers ordinary and "essentially unchanged (+N)" wording.
    m=re.search(r"Total nonfarm payroll employment.{0,140}?(?:rose|increased|grew|advanced)\s+by\s+([0-9,]+)",text,re.I)
    if m:
        payroll=Decimal(m.group(1).replace(",",""))/Decimal("1000")
    else:
        m=re.search(r"Total nonfarm payroll employment.{0,180}?(?:essentially\s+)?unchanged.{0,80}?\(([+-]?[0-9,]+)\)",text,re.I)
        if not m: raise RuntimeError(f"{day}: unable to parse headline payroll")
        payroll=Decimal(m.group(1).replace(",",""))/Decimal("1000")

    um=re.search(r"unemployment\s+rate.{0,100}?(?:at|to)\s+([0-9]+(?:\.[0-9]+)?)\s+percent",text,re.I)
    if not um: raise RuntimeError(f"{day}: unable to parse unemployment rate")
    unemp=Decimal(um.group(1))

    key="average hourly earnings for all employees on private nonfarm payrolls"
    pos=text.lower().find(key)
    if pos<0:
        # Newer line wraps may insert qualifiers; use looser key.
        pos=text.lower().find("average hourly earnings for all employees")
    if pos<0: raise RuntimeError(f"{day}: unable to locate AHE section")
    chunk=text[pos:pos+900]

    # Prefer BLS's explicit MoM percent if the release states it.
    am=re.search(
        r"(rose|increased|advanced|edged up|grew|decreased|declined|fell|edged down)"
        r"\s+by\s+([0-9]+)\s+cents,\s+or\s+([0-9]+(?:\.[0-9]+)?)\s+percent,\s+to\s+\$([0-9]+(?:\.[0-9]+)?)",
        chunk,re.I)
    if am:
        sign=-1 if am.group(1).lower() in {"decreased","declined","fell","edged down"} else 1
        ahe=(Decimal(am.group(3))*sign).quantize(Decimal("0.1"))
        ahe_method="BLS_EXPLICIT_MOM_PERCENT"
    else:
        # Legacy first-release prose sometimes gives cents + current level but omits percentage.
        am=re.search(
            r"(rose|increased|advanced|edged up|grew|decreased|declined|fell|edged down)"
            r"\s+by\s+([0-9]+)\s+cents(?:,)?\s+to\s+\$([0-9]+(?:\.[0-9]+)?)",
            chunk,re.I)
        if not am: raise RuntimeError(f"{day}: unable to parse AHE first-release change")
        sign=-1 if am.group(1).lower() in {"decreased","declined","fell","edged down"} else 1
        cents=Decimal(am.group(2))/Decimal("100")
        current=Decimal(am.group(3))
        previous=current-(Decimal(sign)*cents)
        if previous<=0: raise RuntimeError(f"{day}: invalid AHE previous level")
        rawpct=(current/previous-Decimal("1"))*Decimal("100")
        ahe=rawpct.quantize(Decimal("0.1"),rounding=ROUND_HALF_UP)
        ahe_method="BLS_CENTS_AND_LEVEL_DERIVED_ROUNDED_0.1"

    if abs(payroll)>Decimal("2000") or not (Decimal("2")<=unemp<=Decimal("10")) or abs(ahe)>Decimal("3"):
        raise RuntimeError(f"{day}: parsed BLS actual outside plausibility guard")
    return {
      "payroll_k":str(payroll),"unemployment_pct":str(unemp),"ahe_mom_pct":str(ahe),
      "ahe_method":ahe_method
    }

def sign_decimal(x):
    return 1 if x>0 else (-1 if x<0 else 0)

def label_events(worklist,actuals):
    rows=[]
    amap={x["event_id"]:x for x in actuals}
    for e in worklist["events"]:
        eid=e["event_id"]; c=e["consensus"]; a=amap[eid]["actuals"]
        sp=sign_decimal(Decimal(a["payroll_k"])-Decimal(str(c["payroll_k"])))
        su=sign_decimal(Decimal(str(c["unemployment_pct"]))-Decimal(a["unemployment_pct"]))
        sa=sign_decimal(Decimal(a["ahe_mom_pct"])-Decimal(str(c["ahe_mom_pct"])))
        vote=sp+su+sa
        label="HOTTER" if vote>0 else ("COOLER" if vote<0 else "NEUTRAL")
        shock=1 if label=="HOTTER" else (-1 if label=="COOLER" else 0)
        rows.append({
          "event_id":eid,"event_date":e["event_date"],"release_utc":e["release_utc"],
          "consensus":deepcopy(c),"actuals":deepcopy(a),
          "component_signs":{"payroll":sp,"unemployment":su,"ahe":sa},
          "vote_sum":vote,"label":label,"shock_sign":shock
        })
    return rows

def checksum_expected(text,filename):
    m=CHECKSUM_RE.fullmatch(text.strip())
    if not m or m.group(2)!=filename: raise RuntimeError("Invalid official Binance checksum file")
    return m.group(1).lower()

def target_times(day):
    d=date.fromisoformat(day)
    if d.year not in (2022,2023,2024): raise PermissionError("Binance protected-year firewall")
    en=datetime.combine(d,ENTRY_LOCAL,tzinfo=NY).astimezone(timezone.utc)
    ex=datetime.combine(d,EXIT_LOCAL,tzinfo=NY).astimezone(timezone.utc)
    return int(en.timestamp()*1000),int(ex.timestamp()*1000)

def parse_binance_day(raw,day,symbol):
    entry_ms,exit_ms=target_times(day)
    vals={}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        members=[n for n in z.namelist() if n.lower().endswith(".csv") and not n.endswith("/")]
        if len(members)!=1: raise RuntimeError(f"{symbol}/{day}: unexpected ZIP members")
        with z.open(members[0]) as f:
            reader=csv.reader(io.TextIOWrapper(f,encoding="utf-8-sig",newline=""))
            for row in reader:
                if not row: continue
                try: ts=int(row[0])
                except Exception: continue # optional header
                if ts>=1_000_000_000_000_000: ts//=1000
                if ts in (entry_ms,exit_ms):
                    op=Decimal(row[1])
                    if op<=0: raise RuntimeError(f"{symbol}/{day}: invalid open")
                    vals[ts]=op
    if set(vals)!={entry_ms,exit_ms}: raise RuntimeError(f"{symbol}/{day}: required exact opens missing")
    return vals[entry_ms],vals[exit_ms]

def permutation_p(returns,signs,asset):
    r=np.asarray([float(x) for x in returns],dtype=float)
    s=np.asarray(signs,dtype=int)
    n=len(r); hot=int((s==1).sum()); cool=int((s==-1).sum())
    if hot+cool!=n or hot==0 or cool==0: raise RuntimeError("Permutation requires both HOTTER and COOLER")
    observed=float(np.mean(-s*r))
    total=math.comb(n,hot)

    def stat_for_idx(idx):
        # All COOLER baseline => aligned +r. HOTTER selected => aligned -r.
        return (r.sum()-2.0*r[list(idx)].sum())/n

    if total<=MAX_EXACT:
        exceed=0
        for idx in itertools.combinations(range(n),hot):
            if stat_for_idx(idx)>=observed-1e-12: exceed+=1
        p=exceed/total
        method="EXACT_FIXED_COUNT_LABEL_PERMUTATION"
        reps=total
    else:
        # Deterministic, frozen Monte Carlo fallback based only on label cardinality.
        seed=int.from_bytes(hashlib.sha256(f"NFPV03B|{MC_SEED}|{asset}".encode()).digest()[:8],"big")%(2**32-1)
        rng=np.random.default_rng(seed)
        exceed=0; done=0; batch=10000
        while done<MC_REPS:
            b=min(batch,MC_REPS-done)
            scores=rng.random((b,n))
            idx=np.argpartition(scores,n-hot,axis=1)[:,n-hot:]
            selected=r[idx].sum(axis=1)
            stats=(r.sum()-2.0*selected)/n
            exceed+=int(np.sum(stats>=observed-1e-12))
            done+=b
        p=(1+exceed)/(1+MC_REPS)
        method="DETERMINISTIC_MONTE_CARLO_FIXED_COUNT_PERMUTATION"
        reps=MC_REPS
    return observed,p,method,reps,total

def asset_stats(asset,event_rows,market):
    directional=[e for e in event_rows if e["shock_sign"]!=0]
    gross=[]; signs=[]; detail=[]
    for e in directional:
        m=market[(asset,e["event_id"])]
        g=Decimal(m["gross_return_bps"])
        ag=Decimal(-e["shock_sign"])*g
        an=ag-COST
        gross.append(float(g)); signs.append(e["shock_sign"])
        detail.append({**e,"gross_return_bps":str(g),"aligned_gross_bps":str(ag),"aligned_net_bps":str(an)})
    aligned_g=[float(x["aligned_gross_bps"]) for x in detail]
    aligned_n=[float(x["aligned_net_bps"]) for x in detail]
    obs,p,method,reps,total=permutation_p(gross,signs,asset)
    loo=[]
    for i in range(len(aligned_n)):
        arr=aligned_n[:i]+aligned_n[i+1:]
        loo.append(float(statistics.mean(arr)))
    criteria={
      "mean_aligned_net_gt0":statistics.mean(aligned_n)>0,
      "median_aligned_gross_gt0":statistics.median(aligned_g)>0,
      "permutation_p_lte_0_05":p<=0.05,
      "every_leave_one_out_mean_aligned_net_gt0":min(loo)>0
    }
    return {
      "asset":asset,"directional_event_count":len(detail),
      "hotter_count":sum(x["shock_sign"]==1 for x in directional),
      "cooler_count":sum(x["shock_sign"]==-1 for x in directional),
      "mean_aligned_gross_bps":statistics.mean(aligned_g),
      "median_aligned_gross_bps":statistics.median(aligned_g),
      "mean_aligned_net_bps":statistics.mean(aligned_n),
      "minimum_leave_one_out_mean_aligned_net_bps":min(loo),
      "permutation_p_one_sided":p,"permutation_method":method,
      "permutation_repetitions_or_exact_assignments":reps,
      "unique_assignment_count":total,
      "criteria":criteria,"pass":all(criteria.values()),
      "events":detail
    }

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--worklist",default="T02_PUBLIC_SAFE_WORKLIST.json")
    ap.add_argument("--out",default="./results")
    args=ap.parse_args()

    master=load_hashed(MASTER_PATH,EXPECTED_MASTER_FP,"master consensus")
    freeze=load_hashed(FREEZE_PATH,EXPECTED_FREEZE_FP,"statistical freeze")
    work=json.loads(Path(args.worklist).read_text(encoding="utf-8-sig"))
    out=Path(args.out); out.mkdir(parents=True,exist_ok=True)
    raw_bls=out/"BLS_FIRST_RELEASE_RAW"; raw_bls.mkdir(exist_ok=True)
    raw_bin=out/"BINANCE_SPOT_RAW"; raw_bin.mkdir(exist_ok=True)

    print("="*72)
    print("NEWS SHOCK V0.3B — NFP SURPRISE — MASTER ONE-SHOT DISCOVERY")
    print("="*72)
    print("Master consensus fingerprint:",EXPECTED_MASTER_FP)
    print("Statistical freeze fingerprint:",EXPECTED_FREEZE_FP)
    print("2025 VALIDATION ACCESS: NO")
    print("2026 ACCESS: NO")
    print("LIVE TRADING: NO")

    preexisting,filled=merge_master_worklist(work,master)
    merged_path=out/"NFP_MASTER_36_EVENT_CONSENSUS_CORPUS_V0.1.json"
    merged_path.write_text(json.dumps(work,indent=2),encoding="utf-8")
    print(f"\nConsensus gate PASS: preexisting={preexisting}, filled_from_master={filled}, total=36")

    # BLS first-release actuals.
    actual_rows=[]
    for i,e in enumerate(work["events"],1):
        day=e["event_date"]; eid=e["event_id"]; url=bls_url(day)
        raw=fetch(url,("https://www.bls.gov/news.release/archives/",))
        rp=raw_bls/f"empsit_{date.fromisoformat(day).strftime('%m%d%Y')}.htm"
        rp.write_bytes(raw)
        actual=parse_bls_actual(day,raw)
        actual_rows.append({"event_id":eid,"event_date":day,"source_url":url,
                            "raw_sha256":sha256_bytes(raw),"actuals":actual})
        print(f"BLS {i:02d}/36 {day}: payroll={actual['payroll_k']} unemp={actual['unemployment_pct']} AHE={actual['ahe_mom_pct']}")

    actual_path=out/"NFP_BLS_FIRST_RELEASE_ACTUALS_V0.1.json"
    actual_path.write_text(json.dumps({
       "status":"BLS_FIRST_RELEASE_ACTUALS_COMPLETE_36_OF_36",
       "events":actual_rows,
       "guards":{"crypto_market_data_accessed":False,"2025_accessed":False,"2026_accessed":False}
    },indent=2),encoding="utf-8")

    labelled=label_events(work,actual_rows)
    counts={k:sum(e["label"]==k for e in labelled) for k in ("HOTTER","COOLER","NEUTRAL")}
    if counts["HOTTER"]==0 or counts["COOLER"]==0:
        raise RuntimeError("Fail closed: signal corpus lacks both HOTTER and COOLER events")
    label_path=out/"NFP_FROZEN_DISCOVERY_LABELS_V0.1.json"
    label_path.write_text(json.dumps({"formula_fingerprint":EXPECTED_FREEZE_FP,
                                      "counts":counts,"events":labelled},indent=2),encoding="utf-8")
    print("\nMacro provenance + formula gate PASS:",counts)
    print("No crypto market outcome was used to create consensus, actuals, formula or labels.")

    gate={
      "status":"PRE_DISCOVERY_GATE_PASS_MARKET_DATA_ACCESS_AUTHORIZED_FOR_2022_2024_ONLY",
      "master_consensus_fingerprint":EXPECTED_MASTER_FP,
      "statistical_freeze_fingerprint":EXPECTED_FREEZE_FP,
      "consensus_events":36,"actual_events":36,"label_counts":counts,
      "2025_access_authorized":False,"2026_access_authorized":False,
      "live_trading_authorized":False
    }
    gate_path=out/"NFP_PRE_DISCOVERY_GATE_V0.1.json"
    gate_path.write_text(json.dumps(gate,indent=2),encoding="utf-8")

    # Official Binance event-day acquisition and exact 08:31->08:45 returns.
    market={}
    manifest=[]
    for ei,e in enumerate(labelled,1):
        day=e["event_date"]
        for symbol in SYMBOLS:
            filename=f"{symbol}-1m-{day}.zip"
            url=f"{BASE_URL}/{symbol}/1m/{filename}"
            zraw=fetch(url,(BASE_URL+"/",))
            craw=fetch(url+".CHECKSUM",(BASE_URL+"/",))
            expected=checksum_expected(craw.decode("utf-8",errors="replace"),filename)
            actual_sha=sha256_bytes(zraw)
            if actual_sha!=expected: raise RuntimeError(f"{symbol}/{day}: CHECKSUM mismatch")
            ddir=raw_bin/symbol; ddir.mkdir(exist_ok=True)
            (ddir/filename).write_bytes(zraw)
            (ddir/(filename+".CHECKSUM")).write_bytes(craw)
            en,ex=parse_binance_day(zraw,day,symbol)
            g=(ex/en-Decimal("1"))*Decimal("10000")
            market[(symbol,e["event_id"])]={"entry":str(en),"exit":str(ex),"gross_return_bps":str(g)}
            manifest.append({"event_id":e["event_id"],"symbol":symbol,"archive_url":url,
                             "sha256":actual_sha,"checksum_pass":True})
        if ei%6==0 or ei==36:
            print(f"Binance event days processed: {ei}/36")

    # Integrity requires exact prices for both assets for all 36 events, including neutral.
    if len(market)!=72: raise RuntimeError("Market data integrity gate: expected 72 symbol-events")

    btc=asset_stats("BTCUSDT",labelled,market)
    eth=asset_stats("ETHUSDT",labelled,market)
    overall=btc["pass"] and eth["pass"]
    decision="DISCOVERY_SURVIVES_ELIGIBLE_FOR_SEPARATE_2025_VALIDATION_AUTHORIZATION" if overall else "NO_EDGE_STOP"

    result={
      "lab_id":"NEWS_SHOCK_LAB_V03B_NFP_SURPRISE",
      "phase":"DISCOVERY_2022_2024",
      "decision":decision,
      "label_counts":counts,
      "BTCUSDT":btc,"ETHUSDT":eth,
      "both_assets_required":True,
      "2025_validation_accessed":False,"2025_validation_authorized_now":False,
      "2026_accessed":False,"live_trading_authorized":False,
      "no_tuning_after_outcomes":True
    }
    (out/"NFP_DISCOVERY_RESULTS_V0.1.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
    (out/"NFP_BINANCE_SOURCE_MANIFEST_V0.1.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    close={
      "status":"DISCOVERY_CLOSED",
      "decision":decision,
      "master_consensus_fingerprint":EXPECTED_MASTER_FP,
      "statistical_freeze_fingerprint":EXPECTED_FREEZE_FP,
      "label_counts":counts,
      "BTC_pass":btc["pass"],"ETH_pass":eth["pass"],
      "BTC_mean_aligned_net_bps":btc["mean_aligned_net_bps"],
      "BTC_p":btc["permutation_p_one_sided"],
      "ETH_mean_aligned_net_bps":eth["mean_aligned_net_bps"],
      "ETH_p":eth["permutation_p_one_sided"],
      "2025_validation_accessed":False,"2026_accessed":False,
      "live_trading_authorized":False,
      "next_gate":"SEPARATE_2025_VALIDATION_FREEZE_ONLY_IF_DISCOVERY_SURVIVES" if overall else "STOP_NO_EDGE_NO_RESCUE"
    }
    (out/"NFP_DISCOVERY_CLOSEOUT_V0.1.json").write_text(json.dumps(close,indent=2),encoding="utf-8")

    print("\n"+"="*72)
    print("NFP V0.3B DISCOVERY COMPLETE")
    print("="*72)
    print("Label counts:",counts)
    for x in (btc,eth):
        print(f"{x['asset']}: N={x['directional_event_count']} mean_net={x['mean_aligned_net_bps']:.6f} "
              f"median_gross={x['median_aligned_gross_bps']:.6f} p={x['permutation_p_one_sided']:.8f} "
              f"LOO_min_net={x['minimum_leave_one_out_mean_aligned_net_bps']:.6f} PASS={x['pass']}")
        print("  permutation:",x["permutation_method"],"| assignments/reps:",x["permutation_repetitions_or_exact_assignments"])
    print("\nDECISION:",decision)
    print("2025 VALIDATION ACCESSED: NO")
    print("2026 ACCESSED: NO")
    print("LIVE TRADING AUTHORIZED: NO")
    print("NO POST-OUTCOME TUNING AUTHORIZED")
    print("Outputs:",out)

if __name__=="__main__":
    main()