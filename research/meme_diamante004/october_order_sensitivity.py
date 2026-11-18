#!/usr/bin/env python3
"""MEME004: licensed 2h sample, research-only constant-product quote feasibility."""
import collections,gzip,hashlib,json,math,pathlib,statistics,sys,datetime

P=dict(age_lo=120,age_hi=2400,threshold_sol=2.,lookback=120,
       buyers=5,buy_flow_sol=1.,buy_fraction=.60,largest_buyer=.45,
       min_delay=30,max_delay=180,hold=300,late=120,
       stake=.05,fee=.017,overhead=.0001)

def load(path):
    toks=collections.defaultdict(lambda:{"create":None,"trades":[],"migration":None,"ambig":0})
    kinds=collections.Counter();invalid=0;gaps=[]
    with gzip.open(path,"rt",encoding="utf-8") as f:
        for lineno,raw in enumerate(f):
            if not raw.strip():continue
            try:
                e=json.loads(raw);t=float(e["t"])/1000.
                kind=e.get("type");kinds[str(kind)]+=1
                mint=e.get("mint")
                if kind=="gap":gaps.append(t);continue
                if not mint:continue
                tok=toks[mint]
                if kind=="create":tok["create"]=t;continue
                if kind=="migrate":
                    tok["migration"]=t if tok["migration"] is None else min(t,tok["migration"])
                    continue
                if kind!="trade":continue
                try:
                    vs=float(e["vs"])/1e9;vt=float(e["vt"])
                    curve=float(e["curveSol"]);sol=float(e["sol"])
                    who=str(e["wallet"]);side=e["side"]
                    seq=(int(e.get("slot",0)),int(e.get("off",0)),int(e.get("i",lineno)),lineno)
                    if not (vs>0 and vt>0 and curve>=0 and sol>0 and
                        side in ("buy","sell") and who and all(math.isfinite(q) for q in (vs,vt,curve,sol))):
                        raise ValueError("invalid")
                    tok["trades"].append(dict(t=t,seq=seq,vs=vs,vt=vt,curve=curve,sol=sol,side=side,who=who))
                except (KeyError,ValueError,TypeError,OverflowError):
                    invalid+=1
            except (KeyError,ValueError,TypeError,json.JSONDecodeError):
                invalid+=1
    for tok in toks.values():
        tok["trades"].sort(key=lambda z:(z["t"],z["seq"]))
        for a,b in zip(tok["trades"],tok["trades"][1:]):
            if a["seq"][:3]==b["seq"][:3]:tok["ambig"]+=1
    return toks,kinds,invalid,gaps

def signal(rows,created,filtered):
    for i,r in enumerate(rows):
        age=r["t"]-created
        if age>P["age_hi"]:break
        if age<P["age_lo"] or r["curve"]<P["threshold_sol"]:continue
        if filtered:
            buys=collections.defaultdict(float);b=s=0.
            for h in rows[:i+1]:
                if r["t"]-P["lookback"]<=h["t"]<=r["t"]:
                    if h["side"]=="buy":
                        buys[h["who"]]+=h["sol"];b+=h["sol"]
                    else:s+=h["sol"]
            if (len(buys)<P["buyers"] or b<P["buy_flow_sol"]
                or b+s<=0 or b/(b+s)<P["buy_fraction"]
                or max(buys.values(),default=0)/b>P["largest_buyer"]):
                continue
        return i
    return None

def estimate(rows,idx,migration,slip):
    if idx is None:return {"status":"NO_SIGNAL"}
    sig=rows[idx];t0=sig["t"]
    entry=next((r for r in rows[idx+1:] if
                t0+P["min_delay"]<=r["t"]<=t0+P["max_delay"]
                and r["curve"]>=P["threshold_sol"]),None)
    if entry is None:return {"status":"NO_OBSERVED_ENTRY"}
    if migration is not None and migration<=entry["t"]:
        return {"status":"MIGRATED_BEFORE_ENTRY"}
    te=entry["t"]+P["hold"]
    exit_=next((r for r in rows if
        te<=r["t"]<=te+P["late"] and r["seq"]>entry["seq"]),None)
    if exit_ is None:return {"status":"NO_OBSERVED_EXIT"}
    if migration is not None and migration<=exit_["t"]:
        return {"status":"MIGRATED_BEFORE_EXIT"}
    net_buy=P["stake"]/(1+P["fee"])
    tokens=net_buy*entry["vt"]/(entry["vs"]+net_buy)
    if tokens<=0:return {"status":"ENTRY_QUOTE_INVALID"}
    sol_gross=tokens*(1-slip)*exit_["vs"]/(exit_["vt"]+tokens*(1-slip))
    if sol_gross<=0 or sol_gross>exit_["curve"]:
        return {"status":"EXIT_RESERVE_BLOCKED"}
    net=sol_gross*(1-slip)*(1-P["fee"])-P["overhead"]
    return {"status":"INDICATIVE_QUOTE_NOT_FILL","net_pct":100*(net/P["stake"]-1)}

def summarize(values,n):
    ans=dict(signals=n,quote_outcomes=len(values),
             mean_quote_pct=round(statistics.mean(values),4) if values else None,
             median_quote_pct=round(statistics.median(values),4) if values else None,
             positive_quote_fraction=round(sum(v>0 for v in values)/len(values),4) if values else None,
             adversarial_missing_minus100pct_mean=round((sum(values)-100*(n-len(values)))/n,4) if n else None)
    return ans

def audit(path):
    toks,kinds,bad,gaps=load(path)
    stats=collections.Counter();status=collections.Counter();values=collections.defaultdict(list)
    day_counts=collections.defaultdict(set)
    for mint,tok in toks.items():
        stats["mint_records"]+=1
        rows=tok["trades"];created=tok["create"];migration=tok["migration"]
        if not rows:stats["no_parseable_trades"]+=1;continue
        span=rows[-1]["t"]-rows[0]["t"]
        if span>=300:stats["trades_span_5m"]+=1
        if created is None:stats["exclude_no_create"]+=1;continue
        if tok["ambig"]:stats["retained_ambiguous_mints"]+=1
        if any(created<=g<=rows[-1]["t"] for g in gaps):
            stats["exclude_global_gap"]+=1;continue
        for label,filtered in [("reserve_only",False),("diverse_flow",True)]:
            i=signal(rows,created,filtered)
            if i is None:continue
            stats[label+"_signals"]+=1
            day_counts[label].add(datetime.datetime.fromtimestamp(rows[i]["t"],datetime.timezone.utc).date().isoformat())
            for slip in [0.,.02,.05]:
                z=estimate(rows,i,migration,slip)
                if slip==.02:status[label+"_"+z["status"]]+=1
                if z["status"]=="INDICATIVE_QUOTE_NOT_FILL":
                    values[(label,slip)].append(z["net_pct"])
    summary={"source":"launchtape free 2h October research sample",
        "source_sha256":hashlib.sha256(path.read_bytes()).hexdigest(),
        "event_types":dict(kinds),"invalid_trades":bad,
        "counts":dict(stats),"statuses_2pct_slippage":dict(status),
        "distinct_calendar_days":{k:len(v) for k,v in day_counts.items()},
        "fee_and_size":P,"outcomes":{},
        "scientific_verdict":"INCONCLUSIVE: two-hour sample, missing complete universe/point-in-time quotes",
        "economic_verdict":"NO-GO: SENSITIVITY ONLY, ambiguous multi-leg transaction ordering retained, no independent executable fills"}
    for label in ("reserve_only","diverse_flow"):
        for slip in (0.,.02,.05):
            summary["outcomes"][label+"_slippage_"+str(slip)]=summarize(
                values[(label,slip)],stats[label+"_signals"])
    return summary
if __name__=="__main__":
    path=pathlib.Path(sys.argv[1])
    report=audit(path)
    print("MEME004_SENSITIVITY_RESULT="+json.dumps(report,sort_keys=True))
    pathlib.Path("meme004_october_summary.json").write_text(
        json.dumps(report,sort_keys=True,indent=2)+"\n",encoding="utf8")
