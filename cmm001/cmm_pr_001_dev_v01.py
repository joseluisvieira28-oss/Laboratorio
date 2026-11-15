#!/usr/bin/env python3
import csv, hashlib, io, json, math, os, random, re, statistics, sys, time, urllib.request, zipfile
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, time as dtime, timedelta, timezone

UTC=timezone.utc
UA="CryptoLab-CMM-PR-001/0.1 development-only"
BASE=os.path.dirname(__file__)
OUT=os.path.join(BASE,"pr001_results")
os.makedirs(OUT,exist_ok=True)

PARENT=os.path.join(BASE,"discovery_results","CMM001_DAILY_STATE_LEDGER_V01.csv")
Y2025=os.path.join(BASE,"drv001_results","CMM_DRV_001_2025_STATE_LEDGER_V01.csv")
PARENT_BLOB="c30a38638dcbd8dd33a5a627ad15a3a7096011ca"
Y2025_BLOB="ee4c98340a29ef6c925ba07a543b7cce2e70920c"

START=date(2021,1,1)
END=date(2025,12,31)
SPOT_START=date(2020,12,1)
OLS_WINDOW=365
RESID_WINDOW=180
BOOT_REPS=5000
BOOT_BLOCK=7
BOOT_SEED=20260925

def git_blob(b):
    return hashlib.sha1(f"blob {len(b)}\0".encode()+b).hexdigest()

def f(x):
    if x in (None,""): return None
    try:
        v=float(x)
        return v if math.isfinite(v) else None
    except Exception: return None

def get_bytes(url,timeout=60,retries=4):
    last=None
    for i in range(retries):
        try:
            req=urllib.request.Request(url,headers={"User-Agent":UA})
            with urllib.request.urlopen(req,timeout=timeout) as r:
                return r.read(),r.status
        except Exception as e:
            last=e
            if i+1<retries: time.sleep(0.5*(i+1))
    raise last

def parse_checksum(b):
    t=b.decode("utf-8","replace").strip()
    x=t.split()[0].lower() if t else ""
    return x if re.fullmatch(r"[0-9a-f]{64}",x) else None

def download_zip(url):
    b,s=get_bytes(url); cb,cs=get_bytes(url+".CHECKSUM")
    exp=parse_checksum(cb); act=hashlib.sha256(b).hexdigest()
    if s!=200 or cs!=200 or exp!=act:
        raise RuntimeError(f"CHECKSUM_FAIL {url}")
    z=zipfile.ZipFile(io.BytesIO(b))
    if z.testzip() is not None: raise RuntimeError(f"CRC_FAIL {url}")
    return z,{"url":url,"sha256":act}

def months(a,b):
    y,m=a.year,a.month
    while (y,m)<=(b.year,b.month):
        yield y,m
        if m==12: y,m=y+1,1
        else: m+=1

def solve_linear(A,b):
    n=len(b)
    M=[list(map(float,A[i]))+[float(b[i])] for i in range(n)]
    for col in range(n):
        pivot=max(range(col,n),key=lambda r:abs(M[r][col]))
        if abs(M[pivot][col])<1e-12: return None
        if pivot!=col: M[col],M[pivot]=M[pivot],M[col]
        p=M[col][col]
        for j in range(col,n+1): M[col][j]/=p
        for r in range(n):
            if r==col: continue
            q=M[r][col]
            if q==0: continue
            for j in range(col,n+1): M[r][j]-=q*M[col][j]
    out=[M[i][n] for i in range(n)]
    return out if all(math.isfinite(x) for x in out) else None

def ols_coeff(cases):
    # cases: (y, [O,R,L])
    p=4
    A=[[0.0]*p for _ in range(p)]
    b=[0.0]*p
    for y,x3 in cases:
        x=[1.0]+list(x3)
        for i in range(p):
            b[i]+=x[i]*y
            for j in range(p): A[i][j]+=x[i]*x[j]
    return solve_linear(A,b)

def slope(xs,ys):
    if len(xs)<2:return None
    mx=statistics.fmean(xs); my=statistics.fmean(ys)
    den=sum((x-mx)**2 for x in xs)
    if den<=0:return None
    return sum((x-mx)*(y-my) for x,y in zip(xs,ys))/den

def ranks(vals):
    order=sorted(range(len(vals)),key=lambda i:vals[i])
    out=[0.0]*len(vals)
    k=0
    while k<len(order):
        j=k+1
        while j<len(order) and vals[order[j]]==vals[order[k]]: j+=1
        r=(k+1+j)/2.0
        for q in range(k,j): out[order[q]]=r
        k=j
    return out

def corr(xs,ys):
    if len(xs)<2:return None
    mx=statistics.fmean(xs); my=statistics.fmean(ys)
    dx=[x-mx for x in xs]; dy=[y-my for y in ys]
    den=math.sqrt(sum(x*x for x in dx)*sum(y*y for y in dy))
    return sum(a*b for a,b in zip(dx,dy))/den if den>0 else None

def spearman(xs,ys):
    return corr(ranks(xs),ranks(ys))

def percentile(vals,q):
    xs=sorted(vals)
    if not xs:return None
    pos=(len(xs)-1)*q
    lo=int(math.floor(pos)); hi=int(math.ceil(pos))
    if lo==hi:return xs[lo]
    w=pos-lo
    return xs[lo]*(1-w)+xs[hi]*w

def robust_z(v,hist):
    if len(hist)<RESID_WINDOW:return None
    ref=list(hist)[-RESID_WINDOW:]
    med=statistics.median(ref)
    mad=statistics.median(abs(x-med) for x in ref)
    scale=1.4826*mad
    if scale<=0 or not math.isfinite(scale):return None
    return (v-med)/scale

# -------------------------
# 1. IMMUTABLE STATE INPUTS
# -------------------------
state={}
for path,expected,kind in ((PARENT,PARENT_BLOB,"parent"),(Y2025,Y2025_BLOB,"2025")):
    with open(path,"rb") as fh:b=fh.read()
    if git_blob(b)!=expected:
        raise SystemExit(f"FAIL_CLOSED_{kind.upper()}_STATE_BLOB_MISMATCH")
    for r in csv.DictReader(io.StringIO(b.decode("utf-8"))):
        d=date.fromisoformat(r["date"])
        if kind=="parent" and d.year>2024:
            raise SystemExit("FAIL_CLOSED_PARENT_POST_2024")
        if kind=="2025" and d.year!=2025:
            raise SystemExit("FAIL_CLOSED_2025_LEDGER_YEAR")
        if START<=d<=END:
            state[d]={"O":f(r.get("O_z")),"R":f(r.get("R_z")),"L":f(r.get("L_z"))}

# -------------------------
# 2. OFFICIAL BTC SPOT DATA
# -------------------------
spot17={}; spot18={}; receipts=[]; errors=[]

def fetch_month(ym):
    y,m=ym; stamp=f"{y:04d}-{m:02d}"
    url=f"https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{stamp}.zip"
    z,rec=download_zip(url)
    pts=[]
    for member in z.namelist():
        if member.endswith("/"):continue
        raw=z.read(member).decode("utf-8-sig","replace")
        for row in csv.reader(io.StringIO(raw)):
            if len(row)<2:continue
            try:
                ts=int(row[0])
                if ts>10**14:ts//=1000
                dt=datetime.fromtimestamp(ts/1000,UTC)
                if dt.hour in (17,18) and dt.minute==0:
                    pts.append((dt.date(),dt.hour,float(row[1])))
            except Exception: pass
    return rec,pts

month_list=list(months(SPOT_START,END))
with ThreadPoolExecutor(max_workers=8) as ex:
    futs={ex.submit(fetch_month,ym):ym for ym in month_list}
    for fut in as_completed(futs):
        ym=futs[fut]
        try:
            rec,pts=fut.result(); receipts.append(rec)
            for d,h,p in pts:
                if h==17:spot17[d]=p
                elif h==18:spot18[d]=p
        except Exception as e:
            errors.append({"month":f"{ym[0]:04d}-{ym[1]:02d}","error":repr(e)})

expected_months=61
all_days=list(state.keys())
state_days_17=sum(1 for d in all_days if d in spot17)
state_days_18=sum(1 for d in all_days if d in spot18)
source_gates={
    "state_ledgers_bound":True,
    "spot_months_checksum_complete":len(receipts)==expected_months and not errors,
    "spot17_availability_ge_99_5pct":state_days_17/len(all_days)>=0.995 if all_days else False,
    "spot18_availability_ge_99_5pct":state_days_18/len(all_days)>=0.995 if all_days else False,
    "no_2026_fetched":all("2026" not in x["url"] for x in receipts),
}
source_pass=all(source_gates.values())

source_report={
    "lab_id":"CMM-PR-001","status":"DEVELOPMENT_ONLY","source_pass":source_pass,
    "source_gates":source_gates,"spot_receipts":len(receipts),"spot_errors":errors,
    "state_dates":len(all_days),"spot17_dates":state_days_17,"spot18_dates":state_days_18,
    "parent_event_or_pnl_ledger_read":False,"2026_accessed":False,
}
with open(os.path.join(OUT,"CMM_PR_001_SOURCE_REPORT_V01.json"),"w") as fh:
    json.dump(source_report,fh,indent=2,sort_keys=True)
if not source_pass:
    raise SystemExit(2)

# ------------------------------------------
# 3. CAUSAL WALK-FORWARD PRICE RESIDUAL
# ------------------------------------------
train=deque(maxlen=OLS_WINDOW)
resid_hist=deque(maxlen=RESID_WINDOW)
rows=[]

for d in sorted(state):
    xrow=state[d]
    x=[xrow["O"],xrow["R"],xrow["L"]]
    prev=d-timedelta(days=1)
    y=None
    if d in spot17 and prev in spot17 and spot17[d]>0 and spot17[prev]>0:
        y=math.log(spot17[d]/spot17[prev])
    complete=y is not None and all(v is not None for v in x)

    beta=None; yhat=None; resid=None; zres=None
    if complete and len(train)>=OLS_WINDOW:
        beta=ols_coeff(list(train))
        if beta is not None:
            yhat=beta[0]+sum(beta[i+1]*x[i] for i in range(3))
            resid=y-yhat
            zres=robust_z(resid,resid_hist)

    fwd=None
    nxt=d+timedelta(days=1)
    if d<=date(2025,12,30) and d in spot18 and nxt in spot18 and spot18[d]>0 and spot18[nxt]>0:
        fwd=math.log(spot18[nxt]/spot18[d])*10000.0

    rows.append({
        "date":d.isoformat(),"O_z":x[0],"R_z":x[1],"L_z":x[2],
        "btc_24h_17_return":y,
        "a":beta[0] if beta else None,"bO":beta[1] if beta else None,
        "bR":beta[2] if beta else None,"bL":beta[3] if beta else None,
        "yhat":yhat,"residual":resid,"zres_unclipped":zres,
        "zres_report":max(-8,min(8,zres)) if zres is not None else None,
        "fwd24_18_bps":fwd,
        "mr_gross_bps":(-1 if zres and zres>0 else (1 if zres and zres<0 else 0))*fwd
            if zres is not None and zres!=0 and fwd is not None else None,
    })

    # Strict causal ordering: current residual/case enter histories after current calculations.
    if resid is not None and math.isfinite(resid):
        resid_hist.append(resid)
    if complete:
        train.append((y,x))

valid=[r for r in rows if r["zres_unclipped"] is not None and r["fwd24_18_bps"] is not None]
xs=[r["zres_unclipped"] for r in valid]
ys=[r["fwd24_18_bps"] for r in valid]
mr=[r["mr_gross_bps"] for r in valid]

overall_beta=slope(xs,ys)
rho=spearman(xs,ys)
mean_mr=statistics.fmean(mr) if mr else None
median_mr=statistics.median(mr) if mr else None
hit=sum(x>0 for x in mr)/len(mr) if mr else None
mean_net10=mean_mr-10 if mean_mr is not None else None

annual={}
negative_years=0
for y in range(2021,2026):
    sub=[r for r in valid if int(r["date"][:4])==y]
    bx=slope([r["zres_unclipped"] for r in sub],[r["fwd24_18_bps"] for r in sub]) if len(sub)>=2 else None
    mg=statistics.fmean([r["mr_gross_bps"] for r in sub]) if sub else None
    annual[str(y)]={"n":len(sub),"beta_bps_per_z":bx,"mean_mr_gross_bps":mg}
    if len(sub)>=100 and bx is not None and bx<0: negative_years+=1

# ------------------------------------------
# 4. 7-OBSERVATION MOVING-BLOCK BOOTSTRAP
# ------------------------------------------
rng=random.Random(BOOT_SEED)
boot=[]
n=len(valid)
if n>=2:
    pairs=list(zip(xs,ys))
    starts=list(range(max(1,n-BOOT_BLOCK+1)))
    for _ in range(BOOT_REPS):
        sample=[]
        while len(sample)<n:
            s=starts[rng.randrange(len(starts))]
            sample.extend(pairs[s:min(n,s+BOOT_BLOCK)])
        sample=sample[:n]
        b=slope([p[0] for p in sample],[p[1] for p in sample])
        if b is not None and math.isfinite(b):boot.append(b)

boot_stats={
    "reps_requested":BOOT_REPS,"reps_valid":len(boot),"block_length":BOOT_BLOCK,"seed":BOOT_SEED,
    "p05":percentile(boot,0.05),"p50":percentile(boot,0.50),"p95":percentile(boot,0.95),
    "fraction_beta_ge_zero":sum(b>=0 for b in boot)/len(boot) if boot else None,
}

gates={
    "n_ge_500":len(valid)>=500,
    "overall_beta_lt_zero":overall_beta is not None and overall_beta<0,
    "bootstrap_p95_lt_zero":boot_stats["p95"] is not None and boot_stats["p95"]<0,
    "spearman_rho_lt_zero":rho is not None and rho<0,
    "mean_mr_gross_gt_zero":mean_mr is not None and mean_mr>0,
    "at_least_2_years_n100_beta_lt_zero":negative_years>=2,
}
survives=all(gates.values())
verdict="DEV_MECHANISM_SURVIVES__FORWARD_ONLY_REQUIRED" if survives else "DEV_MECHANISM_FAIL__CLOSE_EXACT_RESIDUAL"

# Evidence ledger
fields=["date","O_z","R_z","L_z","btc_24h_17_return","a","bO","bR","bL","yhat","residual",
        "zres_unclipped","zres_report","fwd24_18_bps","mr_gross_bps"]
with open(os.path.join(OUT,"CMM_PR_001_DEV_LEDGER_V01.csv"),"w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=fields);w.writeheader()
    for r in rows:w.writerow(r)

result={
    "lab_id":"CMM-PR-001","authority":"CMM_PR_001_DEV_AUTHORITY_V01",
    "classification":verdict,"promotion_credit":"ZERO","2026_accessed":False,
    "source_pass":True,
    "model":{"ols_prior_valid_window":OLS_WINDOW,"residual_prior_window":RESID_WINDOW,
             "features":["O_z","R_z","L_z"],"target_contemporaneous":"BTC direct 24h 17:00->17:00 log return",
             "future_target":"BTC 18:00->next-day 18:00 log return in bps"},
    "metrics":{"n":len(valid),"beta_bps_per_z":overall_beta,"spearman_rho":rho,
               "mean_mr_gross_bps":mean_mr,"median_mr_gross_bps":median_mr,
               "mr_positive_fraction":hit,"mean_mr_net10_bps_diagnostic":mean_net10},
    "annual":annual,"negative_beta_years_n100":negative_years,
    "bootstrap":boot_stats,"survival_gates":gates,
    "governance":{"tier_verdict":False,"forward_authorized":False,"live_trading_authorized":False,
                  "main_merge_authorized":False,"rescue_authorized":False}
}
with open(os.path.join(OUT,"CMM_PR_001_DEV_RESULT_V01.json"),"w") as fh:
    json.dump(result,fh,indent=2,sort_keys=True)

def fmt(v,n=4):
    return "NA" if v is None else f"{v:.{n}f}"

close=[
    "# CMM-PR-001 — PRICE-RESIDUAL DEVELOPMENT CLOSEOUT V0.1","",
    f"**CLASSIFICATION: {verdict}**","",
    "2021-2025 is development-only and earns ZERO promotion credit. 2026 was not accessed.","",
    "## Causal residual mechanism",
    f"- Valid ZRES/FWD24 observations: {len(valid)}",
    f"- Primary beta: {fmt(overall_beta)} bps future return per 1 residual-z",
    f"- Spearman rho: {fmt(rho,6)}",
    f"- Mean sign-mean-reversion gross: {fmt(mean_mr)} bps/day",
    f"- Median sign-mean-reversion gross: {fmt(median_mr)} bps/day",
    f"- Positive MR fraction: {fmt(hit*100 if hit is not None else None,2)}%",
    f"- Mean MR NET10 diagnostic: {fmt(mean_net10)} bps/day","",
    "## Moving-block bootstrap beta",
    f"- 5,000 requested / {len(boot)} valid; block length 7; seed {BOOT_SEED}",
    f"- p05 / median / p95: {fmt(boot_stats['p05'])} / {fmt(boot_stats['p50'])} / {fmt(boot_stats['p95'])}",
    f"- fraction beta >= 0: {fmt(boot_stats['fraction_beta_ge_zero'],6)}","",
    "## Frozen survival gates"
]
close += [f"- {k}: {'PASS' if v else 'FAIL'}" for k,v in gates.items()]
close += ["","## Governance",
          "- A DEV survival result can only justify a genuinely prospective forward test; it is not Tier 3/2/1.",
          "- A DEV failure closes this exact residual mechanism with no window/feature/threshold/horizon rescue.",
          "- No 2026 access, live trading, micro-live, orders, exchange mutation, alerts/webhooks, Render or main merge."]
with open(os.path.join(OUT,"CMM_PR_001_DEV_CLOSEOUT_V01.md"),"w") as fh:
    fh.write("\n".join(close)+"\n")

print(json.dumps(result,indent=2,sort_keys=True))
