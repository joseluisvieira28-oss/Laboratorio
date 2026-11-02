#!/usr/bin/env python3
"""Independent OFFLINE categorical audit of pinned original public Kraken derivatives market catalog."""
import collections
import hashlib
import json
import pathlib
D=pathlib.Path("original_kraken_source")
O=pathlib.Path("artifacts/kraken_offline_public_catalog_product_classifier_v01a")
O.mkdir(parents=True,exist_ok=True)
WANTED={
    "instruments":"1ae10c12e086886c32bdbb45fa1feeb453d022b8943deefaee62d18f0f9fdde3",
    "tickers":"32c817a539f5c83b9baa9db38aa60aa0bcac902f990624d746d2b8167929ba65"}
receipt={"study":"KRAKEN_PUBLIC_DERIVATIVES_ORIGINAL_223_INSTRUMENT_TYPE_AUDIT_V01A",
         "original_source_artifact":13145817208,
         "status":"AUDIT_FAIL","fresh_market_http_calls":0,"wallet_calls":0,"orders":0,
         "eligible_account_checked":False,"real_options_rfq_quote_seen":False}
try:
    data={}
    for k,h in WANTED.items():
        raw=(D/(k+"_original.json")).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==h,("SHA_ORIGINAL_MISMATCH",k)
        j=json.loads(raw)
        assert j.get("result")=="success" and len(j[k])==223,("ORIGINAL_NUMBER_MISMATCH",k)
        data[k]=j[k]
    inst=data["instruments"];tics=data["tickers"]
    def category_count(k):
        return dict(sorted(collections.Counter(str(x.get(k,"NULL")) for x in inst).items()))
    tset={str(x.get("symbol","")) for x in tics}
    iset={str(x.get("symbol","")) for x in inst}
    matched=len(iset&tset)
    option_like=[]
    for x in inst:
        attrs=" ".join(str(x.get(k,"")) for k in ("symbol","type","category","tags","pair","base"))
        if any(t in attrs.lower() for t in ("option","_call_","_put_","_c_","_p_","-call-","-put-"," call "," put ")):
            option_like.append({"symbol":str(x.get("symbol","")),"type":str(x.get("type","")),
                                "category":str(x.get("category",""))})
    receipt.update({
      "original_source_sha256_verified":2,
      "official_public_instrument_count":len(inst),
      "official_public_ticker_count":len(tics),
      "instrument_types":category_count("type"),
      "instrument_categories":category_count("category"),
      "instrument_symbol_matches_ticker_count":matched,
      "instruments_without_same_symbol_ticker":len(iset-tset),
      "tickers_without_same_symbol_instrument":len(tset-iset),
      "option_like_instrument_by_full_category_symbol_type":option_like[:15],
      "option_like_count":len(option_like),
      "interpretation":"Kraken public derivatives endpoint catalog cannot be substituted for authenticated options RFQ bid/ask. Zero option-like entries is NOT proof options platform does not exist.",
      "status":"ORIGINAL_KRAKEN_CATALOG_TYPE_OFFLINE_AUDIT_PASS"})
except Exception as ex:
    receipt.update({"error":type(ex).__name__+":"+str(ex)[:200]})
(O/"receipt.json").write_text(json.dumps(receipt,sort_keys=True,indent=2)+"\n")
print("KRAKEN_ORIGINAL_OFFLINE_PRODUCT_AUDIT",json.dumps(receipt,sort_keys=True),flush=True)
if receipt["status"]!="ORIGINAL_KRAKEN_CATALOG_TYPE_OFFLINE_AUDIT_PASS":raise SystemExit(2)
