#!/usr/bin/env python3
"""
MEXC-WTI-EIA-FUNDAMENTAL-001 V1.5

Discovery-only fundamental study:
official EIA commercial crude inventory change -> later MEXC WTI return.

Rule frozen before EIA XLS values are opened.
No retrospective OOS is authorized.
"""
from __future__ import annotations
import csv, hashlib, io, json, math, os, time
from datetime import datetime, timezone, date
from pathlib import Path
import requests
import xlrd

HERE=Path(__file__).resolve().parent
RULE_PATH=HERE/"MEXC_WTI_EIA_FUNDAMENTAL_RULE_V1.5.json"
RULE=json.loads(RULE_PATH.read_text(encoding="utf-8"))

MEXC="https://api.mexc.com"
EIA_XLS=RULE["source_authority"]["public_xls"]
UA="CryptoLab-MEXC-WTI-EIA-Fundamental/1.5"
STEP=300
OUT=Path("artifacts/mexc_global_assets/mexc_wti_eia_fundamental_v15")
RAW=OUT/"raw"

def ts(s):
    return int(datetime.fromisoformat(s.replace("Z","+00:00")).timestamp())

def iso(t):
    return datetime.fromtimestamp(t,tz=timezone.utc).isoformat().replace("+00:00","Z")

EVENTS=[ts(x) for x in RULE["discovery_events_utc"]]
HARD=ts("2026-09-01T00:00:00Z")

def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def sha_file(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save_bytes(name,raw,meta=None):
    RAW.mkdir(parents=True,exist_ok=True)
    p=RAW/name
    p.write_bytes(raw)
    if meta is not None:
        (RAW/(name+".meta.json")).write_text(
            json.dumps(meta,indent=2,sort_keys=True),encoding="utf-8")

def get_url(url,params=None,retries=5):
    last=None
    for i in range(retries):
        try:
            r=requests.get(url,params=params,headers={"User-Agent":UA},timeout=30)
            raw=r.content
            if r.status_code!=200:
                raise RuntimeError(f"HTTP_{r.status_code}:{r.url}:{raw[:300]!r}")
            return raw,r
        except Exception as e:
            last=e
            time.sleep(0.8*(i+1))
    raise last

def parse_date_cell(book,cell):
    try:
        if cell.ctype==xlrd.XL_CELL_DATE:
            return xlrd.xldate_as_datetime(cell.value,book.datemode).date()
        if cell.ctype==xlrd.XL_CELL_TEXT:
            s=str(cell.value).strip()
            for fmt in ("%Y-%m-%d","%m/%d/%Y","%m/%d/%y"):
                try:
                    return datetime.strptime(s,fmt).date()
                except ValueError:
                    pass
    except Exception:
        return None
    return None

def parse_eia_xls(raw):
    book=xlrd.open_workbook(file_contents=raw)
    records={}
    provenance=[]
    for sh in book.sheets():
        header=None
        date_col=None
        value_col=None
        scan_rows=min(sh.nrows,30)
        for r in range(scan_rows):
            vals=[str(sh.cell_value(r,c)).strip() for c in range(sh.ncols)]
            for c,v in enumerate(vals):
                if v.lower()=="date":
                    # Prefer a populated column to the right of Date.
                    candidates=[cc for cc in range(c+1,sh.ncols) if vals[cc]]
                    if candidates:
                        header=r; date_col=c; value_col=candidates[0]
                        break
            if header is not None:
                break
        if header is None:
            continue

        for r in range(header+1,sh.nrows):
            d=parse_date_cell(book,sh.cell(r,date_col))
            if d is None:
                continue
            cell=sh.cell(r,value_col)
            try:
                if cell.ctype==xlrd.XL_CELL_NUMBER:
                    v=float(cell.value)
                else:
                    s=str(cell.value).replace(",","").strip()
                    if not s:
                        continue
                    v=float(s)
            except Exception:
                continue
            if v>0:
                records[d]=v
                provenance.append({"sheet":sh.name,"row":r,"date":d.isoformat()})
    return records,provenance,[sh.name for sh in book.sheets()]

def map_release_to_inventory(records,t0):
    release_date=datetime.fromtimestamp(t0,tz=timezone.utc).date()
    dates=sorted(d for d in records if d<release_date)
    if len(dates)<2:
        raise RuntimeError(f"EIA_NO_PRIOR_WEEK:{release_date}")
    current_date=dates[-1]
    prior_date=dates[-2]
    if current_date.weekday()!=4 or prior_date.weekday()!=4:
        raise RuntimeError(f"EIA_WEEK_END_NOT_FRIDAY:{release_date}:{current_date}:{prior_date}")
    if (current_date-prior_date).days not in (7,14):
        # Allow a rare missing reporting week only as source evidence; scoring still uses the
        # immediately prior official weekly observation.
        raise RuntimeError(f"EIA_WEEK_GAP_UNEXPECTED:{release_date}:{current_date}:{prior_date}")
    current=records[current_date]
    prior=records[prior_date]
    return {
      "release_t0":t0,
      "week_end":current_date,
      "prior_week_end":prior_date,
      "current_stock_kb":current,
      "prior_stock_kb":prior,
      "inventory_delta_kb":current-prior
    }

def fetch_mexc_event(t0,seq):
    # Entry raw start T0+5m; maximum 60m hold exits observable at T0+65m,
    # requiring raw start through T0+60m.
    start=t0
    end=t0+60*60
    if end+STEP>=HARD:
        raise RuntimeError(f"DISCOVERY_BOUNDARY_VIOLATION:{iso(t0)}")
    url=MEXC+f"/api/v1/contract/kline/{RULE['mexc_symbol']}"
    raw,r=get_url(url,{"interval":"Min5","start":start,"end":end})
    meta={
      "event_t0_utc":iso(t0),"url":r.url,
      "requested_raw_start":start,"requested_raw_end":end,
      "captured_at_utc":datetime.now(timezone.utc).isoformat(),
      "sha256":sha_bytes(raw),"bytes":len(raw)
    }
    save_bytes(f"mexc_event_{seq:03d}.json",raw,meta)
    j=r.json()
    if not isinstance(j,dict) or j.get("success") is not True:
        raise RuntimeError(f"MEXC_NON_SUCCESS:{j}")
    d=j.get("data") or {}
    times=d.get("time") or []; opens=d.get("open") or []; closes=d.get("close") or []
    if not (len(times)==len(opens)==len(closes)):
        raise RuntimeError(f"MEXC_KLINE_LENGTH_MISMATCH:{iso(t0)}")
    ro={}; co={}
    for s,o,c in zip(times,opens,closes):
        try:s=int(s); o=float(o); c=float(c)
        except Exception:continue
        if s<start or s>end:
            raise RuntimeError(f"MEXC_TIMESTAMP_OUTSIDE_REQUEST:{iso(t0)}:{s}")
        obs=s+STEP
        if obs>=HARD:
            raise RuntimeError(f"MEXC_PROTECTED_OBS:{iso(t0)}:{obs}")
        if o>0 and c>0:
            ro[s]=o; co[obs]=c
    entry=t0+STEP
    need_raw={entry}
    need_obs={entry+int(h)*60 for h in RULE["horizons_min"]}
    missing_raw=sorted(x for x in need_raw if x not in ro)
    missing_obs=sorted(x for x in need_obs if x not in co)
    return {
      "t0":t0,"raw_open":ro,"close_obs":co,
      "usable":not missing_raw and not missing_obs,
      "missing_raw":missing_raw,"missing_obs":missing_obs,
      "rows":len(ro),"raw_sha256":meta["sha256"]
    }

def mean(xs): return sum(xs)/len(xs) if xs else None
def median(xs):
    if not xs:return None
    y=sorted(xs); n=len(y)
    return y[n//2] if n%2 else (y[n//2-1]+y[n//2])/2
def thirds(xs):
    n=len(xs)
    if n==0:return [None,None,None]
    cuts=[0,n//3,(2*n)//3,n]
    return [mean(xs[cuts[i]:cuts[i+1]]) for i in range(3)]
def logsumexp(xs):
    m=max(xs); return m+math.log(sum(math.exp(x-m) for x in xs))
def binom_tail_half(w,n):
    if n<=0:return None
    ln2=math.log(2.0)
    logs=[math.lgamma(n+1)-math.lgamma(k+1)-math.lgamma(n-k+1)-n*ln2 for k in range(w,n+1)]
    return min(1.0,math.exp(logsumexp(logs)))

def score(mapped,prices,threshold,horizon):
    vals=[]; deltas=[]; obs=[]
    by_t0={x["t0"]:x for x in prices}
    for m in mapped:
        t0=m["release_t0"]
        p=by_t0[t0]
        if not p["usable"]:
            continue
        delta=m["inventory_delta_kb"]
        if delta==0 or abs(delta)<threshold:
            continue
        # Frozen intuitive fundamental direction.
        side=1 if delta<0 else -1
        entry_t=t0+STEP
        entry=p["raw_open"][entry_t]
        exit_obs=entry_t+horizon*60
        exit_px=p["close_obs"][exit_obs]
        gross=side*10000.0*(exit_px/entry-1.0)
        vals.append(gross); deltas.append(delta)
        obs.append({
          "release_t0_utc":iso(t0),
          "week_end":m["week_end"].isoformat(),
          "prior_week_end":m["prior_week_end"].isoformat(),
          "inventory_delta_kb":delta,
          "side":"LONG" if side>0 else "SHORT",
          "entry_t_utc":iso(entry_t),
          "exit_observable_utc":iso(exit_obs),
          "gross_bps":gross
        })
    n=len(vals); wins=sum(x>0 for x in vals); mg=mean(vals)
    return {
      "n":n,"wins":wins,"losses":n-wins,
      "win_rate":wins/n if n else None,
      "mean_gross_bps":mg,
      "median_gross_bps":median(vals),
      "p_value_vs_50":binom_tail_half(wins,n) if n else None,
      "third_means_gross_bps":thirds(vals),
      "mean_abs_inventory_delta_kb":mean([abs(x) for x in deltas]),
      "median_abs_inventory_delta_kb":median([abs(x) for x in deltas]),
      "economic_hurdles_cleared":{
        str(c):(mg>float(c) if mg is not None else False)
        for c in RULE["economic_hurdles_roundtrip_bps"]
      },
      "cost_scenarios_mean_net_bps":{
        str(c):(mg-float(c) if mg is not None else None)
        for c in RULE["cost_scenarios_roundtrip_bps"]
      },
      "observations":obs
    }

def eligible(r):
    g=RULE["discovery_gate"]
    return (
      r["n"]>=g["min_n"]
      and r["mean_gross_bps"] is not None and r["mean_gross_bps"]>0
      and r["win_rate"] is not None and r["win_rate"]>0.5
      and r["p_value_vs_50"] is not None
      and all(x is not None and x>0 for x in r["third_means_gross_bps"])
    )

def holm(cells):
    e=[x for x in cells if x["eligible"]]
    e.sort(key=lambda x:x["discovery"]["p_value_vs_50"])
    m=len(e); selected=[]
    for rank,x in enumerate(e,1):
        cutoff=RULE["discovery_gate"]["family_wise_alpha"]/(m-rank+1)
        x["holm_cutoff"]=cutoff
        if x["discovery"]["p_value_vs_50"]<=cutoff:
            selected.append(x)
        else:
            break
    return selected,m

def compact(r):
    x=dict(r); x.pop("observations",None); return x

def main():
    forbidden={"MEXC_API_KEY","MEXC_SECRET_KEY","EIA_API_KEY","API_KEY","SECRET_KEY","PRIVATE_KEY"}
    if any(k.upper() in forbidden for k in os.environ):
        raise SystemExit("FAIL_CLOSED:CREDENTIAL_LIKE_ENV_DETECTED")
    if RULE.get("outcomes_opened_at_freeze")!=0:
        raise SystemExit("FAIL_CLOSED:FREEZE_INVALID")
    if RULE.get("inventory_thresholds_frozen_before_xls_values") is not True:
        raise SystemExit("FAIL_CLOSED:THRESHOLD_PROVENANCE_INVALID")
    if RULE.get("inverse_mode_authorized") is not False:
        raise SystemExit("FAIL_CLOSED:INVERSE_MODE_NOT_ALLOWED")
    if RULE.get("retrospective_oos_authorized") is not False:
        raise SystemExit("FAIL_CLOSED:RETROSPECTIVE_OOS_NOT_ALLOWED")

    OUT.mkdir(parents=True,exist_ok=True)
    print("RULE_SHA256=",sha_file(RULE_PATH))
    print("PRE_EIA_VALUES_FREEZE_PASS")

    # 1) Official EIA source gate.
    raw,r=get_url(EIA_XLS)
    eia_meta={
      "url":r.url,"captured_at_utc":datetime.now(timezone.utc).isoformat(),
      "sha256":sha_bytes(raw),"bytes":len(raw),"status_code":r.status_code
    }
    save_bytes("EIA_WCESTUS1w.xls",raw,eia_meta)
    records,prov,sheets=parse_eia_xls(raw)
    mapped=[map_release_to_inventory(records,t0) for t0 in EVENTS]

    # Validate mappings without printing values before the source gate.
    source_gate={
      "eia_xls_sha256":eia_meta["sha256"],
      "eia_xls_bytes":eia_meta["bytes"],
      "sheet_names":sheets,
      "parsed_weekly_records":len(records),
      "mapped_discovery_releases":len(mapped),
      "all_current_week_ends_friday":all(x["week_end"].weekday()==4 for x in mapped),
      "all_prior_week_ends_friday":all(x["prior_week_end"].weekday()==4 for x in mapped),
      "all_values_positive":all(x["current_stock_kb"]>0 and x["prior_stock_kb"]>0 for x in mapped),
      "verdict":"EIA_WCESTUS1_SOURCE_PASS"
    }
    print(json.dumps({
      "SOURCE_GATE_ONLY":True,
      "VALUES_NOT_PRINTED":True,
      **source_gate
    },indent=2,sort_keys=True))
    if len(mapped)!=len(EVENTS) or not source_gate["all_values_positive"]:
        raise RuntimeError("EIA_SOURCE_GATE_FAIL")

    # 2) MEXC event-window coverage, still before scoring.
    prices=[]
    for i,t0 in enumerate(EVENTS,1):
        prices.append(fetch_mexc_event(t0,i))
        time.sleep(0.04)
    bad=[{
      "release_t0_utc":iso(x["t0"]),"rows":x["rows"],
      "missing_raw":[iso(v) for v in x["missing_raw"]],
      "missing_obs":[iso(v) for v in x["missing_obs"]]
    } for x in prices if not x["usable"]]
    print(json.dumps({
      "MEXC_COVERAGE_ONLY":True,
      "SCORING_NOT_YET_STARTED":True,
      "usable_events":sum(x["usable"] for x in prices),
      "total_events":len(prices),
      "bad_events":bad
    },indent=2,sort_keys=True))
    if any(not x["usable"] for x in prices):
        raise RuntimeError("MEXC_DISCOVERY_COVERAGE_INCOMPLETE")

    # 3) Frozen Discovery.
    cells=[]
    for th in RULE["abs_inventory_change_thresholds_kb"]:
        for h in RULE["horizons_min"]:
            rr=score(mapped,prices,float(th),int(h))
            cells.append({
              "inventory_threshold_kb":th,
              "horizon_min":h,
              "eligible":eligible(rr),
              "discovery":compact(rr)
            })

    selected,pre_holm=holm(cells)

    report={
      "family_id":RULE["family_id"],"version":RULE["version"],
      "generated_at_utc":datetime.now(timezone.utc).isoformat(),
      "rule_sha256":sha_file(RULE_PATH),
      "eia_source_gate":source_gate,
      "discovery_events":len(EVENTS),
      "discovery_cells":cells,
      "pre_holm_eligible_count":pre_holm,
      "holm_selected_count":len(selected),
      "holm_selected":[{
        "inventory_threshold_kb":x["inventory_threshold_kb"],
        "horizon_min":x["horizon_min"],
        "n":x["discovery"]["n"],
        "wins":x["discovery"]["wins"],
        "win_rate":x["discovery"]["win_rate"],
        "mean_gross_bps":x["discovery"]["mean_gross_bps"],
        "p":x["discovery"]["p_value_vs_50"],
        "holm_cutoff":x.get("holm_cutoff"),
        "economic_hurdles_cleared":x["discovery"]["economic_hurdles_cleared"],
        "cost_scenarios_mean_net_bps":x["discovery"]["cost_scenarios_mean_net_bps"]
      } for x in selected],
      "verdict":"WTI_EIA_FUNDAMENTAL_DISCOVERY_CANDIDATES_SURVIVE__FORWARD_REQUIRED"
                if selected else
                "NO_WTI_EIA_FUNDAMENTAL_DISCOVERY_CANDIDATE_AT_FROZEN_V15_GATE",
      "retrospective_oos_opened":False,
      "september_used_for_scoring":False,
      "future_forward_required_for_confirmation":True,
      "inverse_mode_used":False,
      "consensus_used":False,
      "post_outcome_tuning":False,
      "private_endpoints_used":False,"account_reads":False,"wallets_used":False,
      "orders":False,"exchange_mutation":False,"live_trading_authorized":False
    }
    (OUT/"MEXC_WTI_EIA_FUNDAMENTAL_CLOSEOUT_V15.json").write_text(
      json.dumps(report,indent=2,sort_keys=True),encoding="utf-8")

    rows=[]
    selected_keys={(x["inventory_threshold_kb"],x["horizon_min"]) for x in selected}
    for x in cells:
        rr=x["discovery"]
        rows.append({
          "inventory_threshold_kb":x["inventory_threshold_kb"],
          "horizon_min":x["horizon_min"],
          "n":rr["n"],"wins":rr["wins"],"win_rate":rr["win_rate"],
          "mean_gross_bps":rr["mean_gross_bps"],
          "p_value_vs_50":rr["p_value_vs_50"],
          "eligible":x["eligible"],
          "selected":(x["inventory_threshold_kb"],x["horizon_min"]) in selected_keys
        })
    with (OUT/"MEXC_WTI_EIA_FUNDAMENTAL_MATRIX_V15.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    print(json.dumps({
      "verdict":report["verdict"],
      "pre_holm_eligible_count":pre_holm,
      "holm_selected_count":len(selected),
      "holm_selected":report["holm_selected"],
      "retrospective_oos_opened":False,
      "future_forward_required_for_confirmation":True,
      "live_trading_authorized":False
    },indent=2,sort_keys=True))

if __name__=="__main__":
    main()
