#!/usr/bin/env python3
import json, math, random, statistics, time, urllib.parse, urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

START=int(datetime(2024,1,1,tzinfo=timezone.utc).timestamp()*1000)
END=int(datetime(2025,12,31,23,59,59,tzinfo=timezone.utc).timestamp()*1000)
ASSETS=["BTC","ETH","SOL","XRP","DOGE","ADA","AVAX","LINK","LTC","BCH"]
THRESHOLDS=[0.0,0.25,0.50,1.00]
OUT=Path("research/funding_dispersion/out"); OUT.mkdir(parents=True,exist_ok=True)

def get(url, tries=5):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-Research/1.0"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req,timeout=30) as r:
                return json.loads(r.read().decode())
        except Exception:
            if i==tries-1: raise
            time.sleep(1.5*(i+1))

def bybit(asset):
    sym=asset+"USDT"; end=END; rows={}
    while end>=START:
        q=urllib.parse.urlencode({"category":"linear","symbol":sym,"endTime":end,"limit":200})
        j=get("https://api.bybit.com/v5/market/funding/history?"+q)
        if j.get("retCode")!=0: raise RuntimeError(("bybit",asset,j))
        xs=j.get("result",{}).get("list",[])
        if not xs: break
        for x in xs:
            ts=int(x["fundingRateTimestamp"])
            if START<=ts<=END: rows[ts]=float(x["fundingRate"])
        oldest=min(int(x["fundingRateTimestamp"]) for x in xs)
        if oldest<=START or oldest>=end: break
        end=oldest-1; time.sleep(.05)
    return rows

def okx(asset):
    inst=f"{asset}-USDT-SWAP"; after=None; rows={}
    while True:
        p={"instId":inst,"limit":"400"}
        if after is not None: p["after"]=str(after)
        j=get("https://www.okx.com/api/v5/public/funding-rate-history?"+urllib.parse.urlencode(p))
        if j.get("code")!="0": raise RuntimeError(("okx",asset,j))
        xs=j.get("data",[])
        if not xs: break
        for x in xs:
            ts=int(x["fundingTime"])
            if START<=ts<=END:
                # realizedRate is authoritative when present; fundingRate fallback.
                v=x.get("realizedRate") or x.get("fundingRate")
                rows[ts]=float(v)
        oldest=min(int(x["fundingTime"]) for x in xs)
        if oldest<=START: break
        if after is not None and oldest>=after: break
        after=oldest; time.sleep(.05)
    return rows

def norm(rows):
    ts=sorted(rows); out={}
    for i in range(1,len(ts)):
        hours=(ts[i]-ts[i-1])/3600000
        if 0.5<=hours<=12:
            out[ts[i]]=rows[ts[i]]*10000/hours
    return out

def boot_ci(vals, n=4000):
    if len(vals)<2: return [None,None]
    rng=random.Random(2601001); means=[]
    for _ in range(n):
        means.append(sum(rng.choice(vals) for __ in vals)/len(vals))
    means.sort()
    return [means[int(.025*n)],means[int(.975*n)-1]]

records=[]; source={}
for a in ASSETS:
    try:
        b=bybit(a); o=okx(a)
        bn,on=norm(b),norm(o)
        common=sorted(set(bn)&set(on))
        source[a]={"bybit":len(b),"okx":len(o),"common_norm":len(common)}
        # At t, current settled differential forms signal; outcome is NEXT common settled differential.
        for i in range(len(common)-1):
            t,nxt=common[i],common[i+1]
            # cap gap to 12h to avoid stale / delisting jumps
            if nxt-t>12*3600000: continue
            cur=bn[t]-on[t]; future=bn[nxt]-on[nxt]
            s=1 if cur>0 else (-1 if cur<0 else 0)
            # short higher-funding venue / long lower-funding venue => signed future differential
            carry=s*future
            records.append({"asset":a,"t":t,"next_t":nxt,"lag_disp_bph":cur,"next_disp_bph":future,"signed_next_carry_bph":carry,"year":datetime.fromtimestamp(nxt/1000,timezone.utc).year})
    except Exception as e:
        source[a]={"error":repr(e)}

def metrics(rs):
    vals=[r["signed_next_carry_bph"] for r in rs]
    pos=sum(v>0 for v in vals); neg=[-v for v in vals if v<0]
    gains=sum(v for v in vals if v>0)
    losses=sum(neg)
    byasset=defaultdict(list); byyear=defaultdict(list)
    for r in rs: byasset[r["asset"]].append(r["signed_next_carry_bph"]); byyear[r["year"]].append(r["signed_next_carry_bph"])
    positive_by_asset={a:sum(v for v in vs if v>0) for a,vs in byasset.items()}
    total_pos=sum(positive_by_asset.values())
    concentration=max(positive_by_asset.values())/total_pos if total_pos else None
    ci=boot_ci(vals)
    return {
      "N":len(vals),"mean_bph":statistics.fmean(vals) if vals else None,
      "median_bph":statistics.median(vals) if vals else None,
      "win_rate":pos/len(vals) if vals else None,
      "pf_like":gains/losses if losses else None,
      "bootstrap95_mean_bph":ci,
      "max_positive_asset_concentration":concentration,
      "assets":{a:{"N":len(vs),"mean_bph":statistics.fmean(vs)} for a,vs in sorted(byasset.items())},
      "years":{str(y):{"N":len(vs),"mean_bph":statistics.fmean(vs)} for y,vs in sorted(byyear.items())}
    }

results={}
for th in THRESHOLDS:
    rs=[r for r in records if abs(r["lag_disp_bph"])>=th]
    m=metrics(rs)
    eligible_assets=sum(1 for x in m["assets"].values() if x["N"]>=30)
    lo=m["bootstrap95_mean_bph"][0]
    promotion=(th>0 and m["N"]>=300 and eligible_assets>=5 and (m["mean_bph"] or 0)>0 and lo is not None and lo>0 and (m["win_rate"] or 0)>=.55 and (m["max_positive_asset_concentration"] or 1)<=.40 and all(str(y) in m["years"] and m["years"][str(y)]["mean_bph"]>0 for y in (2024,2025)))
    m["eligible_assets_ge30"]=eligible_assets; m["promotion_gate_pass"]=promotion
    results[str(th)]=m

survivors=[k for k,v in results.items() if v["promotion_gate_pass"]]
verdict="RESEARCH_SURVIVOR_ONLY" if survivors else ("SOURCE_BLOCKED" if not records else "NO_EDGE")
payload={"experiment":"FUNDING-DISPERSION-DN-001","window":["2024-01-01","2025-12-31"],"source":source,"records":len(records),"thresholds":results,"survivor_thresholds":survivors,"verdict":verdict}
(OUT/"stage_a_results.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
with (OUT/"observations.csv").open("w",encoding="utf-8") as f:
    f.write("asset,t,next_t,lag_disp_bph,next_disp_bph,signed_next_carry_bph,year\n")
    for r in records: f.write(",".join(str(r[k]) for k in ["asset","t","next_t","lag_disp_bph","next_disp_bph","signed_next_carry_bph","year"])+"\n")
lines=["# FUNDING-DISPERSION-DN-001 — Stage A result","",f"**Verdict: {verdict}**",f"Eligible observations: {len(records)}","", "| Threshold bps/hour | N | Mean next carry | Win rate | Bootstrap 95% CI | Assets>=30 | Gate |","|---:|---:|---:|---:|---|---:|---|"]
for th in THRESHOLDS:
    m=results[str(th)]; ci=m["bootstrap95_mean_bph"]
    lines.append(f"| {th:.2f} | {m['N']} | {(m['mean_bph'] or 0):.4f} | {(m['win_rate'] or 0):.2%} | [{ci[0] if ci[0] is not None else 'NA'}, {ci[1] if ci[1] is not None else 'NA'}] | {m['eligible_assets_ge30']} | {'PASS' if m['promotion_gate_pass'] else 'FAIL'} |")
lines += ["","Stage A tests persistence of funding dispersion only. It is not executable PnL and grants no trading authority.","2026 remained unopened."]
(OUT/"STAGE_A_RESULT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
print(json.dumps(payload,indent=2))
