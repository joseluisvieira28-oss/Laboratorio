#!/usr/bin/env python3
import argparse,datetime as dt,json,urllib.parse,urllib.request,urllib.error,time
from pathlib import Path

ap=argparse.ArgumentParser()
ap.add_argument("--requirements",required=True)
ap.add_argument("--registry",required=True)
ap.add_argument("--validation",required=True)
args=ap.parse_args()

OUT=Path("labs/DEFI_LIQUIDATION_SHOCK_001/MARKET_DATA_SOURCE_FEASIBILITY_RECEIPT_V0.1.json")

def find_one(root,name):
    hits=sorted(Path(root).rglob(name))
    if not hits:return None,None
    return json.loads(hits[0].read_text()),str(hits[0])

req,rp=find_one(args.requirements,"MARKET_MAPPING_REQUIREMENTS_RECEIPT_V0.1.json")
val,vp=find_one(args.validation,"MARKET_DATA_MAPPING_REGISTRY_VALIDATION_RECEIPT_V0.1.json")
reg=json.loads(Path(args.registry).read_text()) if Path(args.registry).exists() else None
errors=[]

if not req or req.get("classification")!="MARKET_MAPPING_REQUIREMENTS_SOURCE_PASS":
    errors.append({"reason":"requirements_not_pass","classification":(req or {}).get("classification")})
if not val or val.get("classification")!="MARKET_DATA_MAPPING_REGISTRY_PASS":
    errors.append({"reason":"mapping_registry_validation_not_pass","classification":(val or {}).get("classification")})
if not reg:errors.append({"reason":"mapping_registry_missing"})

needs={x["target_identity"]:x for x in (req or {}).get("requirements") or []}
mapping={x["target_identity"]:x for x in (reg or {}).get("mappings") or [] if x.get("target_identity")}

def http_json(url,retries=5):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"Accept":"application/json","User-Agent":"crypto-lab-dls-market-feasibility/0.1"})
            with urllib.request.urlopen(q,timeout=45) as r:return int(r.status),json.loads(r.read())
        except urllib.error.HTTPError as e:
            last={"http":e.code}
            if e.code in (429,500,502,503,504):time.sleep(min(15,2**i));continue
            return int(e.code),None
        except Exception as e:last={"error":type(e).__name__,"detail":str(e)[:200]};time.sleep(min(15,2**i))
    return None,last

def head(url,retries=5):
    last=None
    for i in range(retries):
        try:
            q=urllib.request.Request(url,headers={"User-Agent":"crypto-lab-dls-market-feasibility/0.1"},method="HEAD")
            with urllib.request.urlopen(q,timeout=45) as r:return int(r.status),dict(r.headers)
        except urllib.error.HTTPError as e:
            if e.code in (404,403,405):return int(e.code),{}
            last={"http":e.code}
            if e.code in (429,500,502,503,504):time.sleep(min(15,2**i));continue
            return int(e.code),{}
        except Exception as e:last={"error":type(e).__name__,"detail":str(e)[:200]};time.sleep(min(15,2**i))
    return None,last or {}

def parse_date(s):
    return dt.date.fromisoformat(str(s)[:10])

results=[]
for target,need in sorted(needs.items()):
    row=mapping.get(target) or {}
    status=row.get("status")
    inferential=bool(need.get("inferential_dependency"))
    res={"target_identity":target,"mapping_status":status,"inferential_dependency":inferential,
         "monthly_probe_count":len(need.get("monthly_probe_dates") or []),"route_pass":False}

    if status=="MARKET_MAPPING_UNAVAILABLE":
        res["reason"]="mapping_unavailable"
        if inferential:errors.append({"reason":"inferential_mapping_unavailable","target_identity":target})
        results.append(res);continue

    if status=="BINANCE_DIRECT":
        symbol=row.get("symbol");base=row.get("base_asset");quote=row.get("quote_asset")
        url="https://api.binance.com/api/v3/exchangeInfo?"+urllib.parse.urlencode({"symbol":symbol})
        st,obj=http_json(url)
        res["product_metadata_http_status"]=st
        symbols=(obj or {}).get("symbols") or []
        exact=[x for x in symbols if x.get("symbol")==symbol and x.get("baseAsset")==base and x.get("quoteAsset")==quote]
        res["product_metadata_exact_match"]=len(exact)==1
        current_expected=row.get("current_product_metadata_expected")
        historical_ok=(current_expected is False and bool(row.get("historical_product_metadata_authority")))
        res["historical_product_authority_used"]=bool(len(exact)!=1 and historical_ok)
        if len(exact)!=1 and not historical_ok:
            res["reason"]="binance_product_metadata_mismatch_without_historical_authority"
            if inferential:errors.append({"reason":"inferential_binance_product_mismatch","target_identity":target,"http_status":st})
            results.append(res);continue

        listing=row.get("listing_start_utc")
        listing_date=parse_date(listing) if listing else None
        probes=[]
        all_ok=True
        for day in need.get("monthly_probe_dates") or []:
            d=parse_date(day)
            if listing_date and d<listing_date:
                probes.append({"date":day,"status":"PRE_LISTING_SOURCE_BOUNDARY"})
                all_ok=False
                continue
            zip_url=str(row.get("archive_route_template")).replace("{symbol}",symbol).replace("{date}",day)
            sum_url=str(row.get("checksum_route_template")).replace("{symbol}",symbol).replace("{date}",day)
            zs,zh=head(zip_url);cs,ch=head(sum_url)
            ok=(zs==200 and cs==200)
            probes.append({"date":day,"zip_head_status":zs,"checksum_head_status":cs,"pass":ok})
            if not ok:all_ok=False
        res["monthly_probes"]=probes
        res["route_pass"]=all_ok
        if inferential and not all_ok:
            errors.append({"reason":"inferential_binance_route_probe_failed","target_identity":target})
        results.append(res);continue

    if status=="OKX_DIRECT":
        inst=row.get("instrument_id")
        url="https://www.okx.com/api/v5/public/instruments?"+urllib.parse.urlencode({"instType":"SPOT","instId":inst})
        st,obj=http_json(url)
        data=(obj or {}).get("data") or []
        exact=[x for x in data if x.get("instId")==inst and x.get("baseCcy")==row.get("base_asset") and x.get("quoteCcy")==row.get("quote_asset")]
        res["product_metadata_http_status"]=st
        res["product_metadata_exact_match"]=len(exact)==1
        res["history_payload_probed"]=False
        res["route_authority_present"]=bool(row.get("historical_candle_route_authority"))
        res["route_pass"]=len(exact)==1 and res["route_authority_present"]
        if inferential and not res["route_pass"]:
            errors.append({"reason":"inferential_okx_metadata_route_failed","target_identity":target})
        results.append(res);continue

    res["reason"]="invalid_mapping_status"
    errors.append({"reason":"invalid_mapping_status","target_identity":target,"status":status})
    results.append(res)

classification="MARKET_DATA_SOURCE_PASS" if not errors else "MARKET_DATA_SOURCE_BLOCKED"
receipt={"schema_version":"0.1","lab_id":"DEFI-LIQUIDATION-SHOCK-001","classification":classification,
 "requirements_classification":(req or {}).get("classification"),
 "mapping_validation_classification":(val or {}).get("classification"),
 "target_count":len(results),"route_pass_count":sum(1 for x in results if x.get("route_pass")),
 "results":results,"error_count":len(errors),"errors":errors,
 "probe_freeze":"MARKET_DATA_ROUTE_METADATA_PROBE_FREEZE_V0.1.md",
 "archive_payload_downloaded":False,"candles_opened":False,"prices_opened":False,
 "firewall":{"returns_computed":False,"pnl_computed":False,"economic_outcomes_opened":False,
             "protected_2025_2026_opened":False,"post_outcome_tuning":False,
             "live_trading":False,"merge_main":False}}
OUT.write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n")
print(json.dumps({"classification":classification,"target_count":len(results),
                  "route_pass_count":receipt["route_pass_count"],"error_count":len(errors)},indent=2))
if classification!="MARKET_DATA_SOURCE_PASS":raise SystemExit(2)
