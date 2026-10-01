#!/usr/bin/env python3
from __future__ import annotations
import html.parser, itertools, json, time, urllib.parse, urllib.request

PRODUCT_URL="https://www.optionsdx.com/product/btc-option-chains/"
AJAX_URL="https://www.optionsdx.com/?wc-ajax=get_variation"
PRODUCT_ID="1527"
MAX_LOOKUPS=250
PACE_SECONDS=0.12

class SelectParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__(); self.current_name=None; self.selects={}
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag.lower()=="select":
            name=attrs.get("name")
            if name and str(name).startswith("attribute_"):
                self.current_name=str(name); self.selects.setdefault(self.current_name,[])
        elif tag.lower()=="option" and self.current_name:
            v=attrs.get("value")
            if v: self.selects[self.current_name].append(str(v))
    def handle_endtag(self,tag):
        if tag.lower()=="select": self.current_name=None

def get_text(url):
    req=urllib.request.Request(url,headers={"User-Agent":"CryptoLab-ProcurementMetadata/0.1"},method="GET")
    with urllib.request.urlopen(req,timeout=45) as r: return r.read().decode("utf-8","replace")

def post_form(fields):
    data=urllib.parse.urlencode(fields).encode()
    req=urllib.request.Request(AJAX_URL,data=data,headers={
        "User-Agent":"CryptoLab-ProcurementMetadata/0.1",
        "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With":"XMLHttpRequest","Referer":PRODUCT_URL},method="POST")
    with urllib.request.urlopen(req,timeout=45) as r: return json.loads(r.read().decode("utf-8","replace"))

def norm(x): return str(x).strip().lower().replace("-"," ").replace("_"," ")

def main():
    out={"probe_id":"OVRP-OPTIONSDX-FULL-VARIATION-CENSUS-001","cash_spend_usd":0,
         "cart_used":False,"checkout_used":False,"account_created":False,"order_created":False,
         "market_payload_opened":False,"outcomes_opened":False}
    try: page=get_text(PRODUCT_URL)
    except Exception as e:
        out.update(classification="OPTIONSDX_CATALOG_ACQUISITION_FAILURE",error=f"{type(e).__name__}:{e}"); return write(out,2)
    p=SelectParser(); p.feed(page)
    sels={k:sorted(set(v)) for k,v in p.selects.items() if v}
    names=sorted(sels); combos=list(itertools.product(*(sels[n] for n in names)))
    out["selector_names"]=names; out["selector_value_counts"]={k:len(v) for k,v in sels.items()}
    out["visible_selector_cross_product"]=len(combos)
    if len(names)<2 or len(combos)>MAX_LOOKUPS:
        out.update(classification="OPTIONSDX_CATALOG_METADATA_PARTIAL",error="selector_shape_or_cap"); return write(out,2)

    rows=[]; unresolved=[]; errors=[]
    for i,combo in enumerate(combos,1):
        attrs=dict(zip(names,combo)); fields={"product_id":PRODUCT_ID}; fields.update(attrs)
        try: obj=post_form(fields)
        except Exception as e:
            errors.append(f"{i}:{type(e).__name__}:{str(e)[:180]}"); time.sleep(PACE_SECONDS); continue
        if not isinstance(obj,dict) or not obj.get("variation_id"):
            unresolved.append(attrs); time.sleep(PACE_SECONDS); continue
        price=obj.get("display_price"); regular=obj.get("display_regular_price")
        if not isinstance(price,(int,float)):
            unresolved.append(attrs); time.sleep(PACE_SECONDS); continue
        rows.append({"variation_id":obj.get("variation_id"),"attributes":attrs,
                     "display_price":float(price),
                     "display_regular_price":float(regular) if isinstance(regular,(int,float)) else None,
                     "variation_is_active":obj.get("variation_is_active"),
                     "is_in_stock":obj.get("is_in_stock"),"is_purchasable":obj.get("is_purchasable")})
        time.sleep(PACE_SECONDS)

    zero=[r for r in rows if r["display_price"]==0.0]
    intraday=[]
    for r in zero:
        vals=[norm(v) for v in r["attributes"].values()]
        if any(v in {"30 minutes","15 minutes","5 minutes","minutely","1 minute","1m","5m","15m","30m"} for v in vals):
            intraday.append(r)

    out.update(lookup_count=len(combos),resolved_price_count=len(rows),unresolved_lookup_count=len(unresolved),
               error_count=len(errors),errors=errors[:20],resolved_variations=rows,
               distinct_display_prices=sorted({r["display_price"] for r in rows}),
               zero_price_variation_count=len(zero),zero_price_variations=zero,
               zero_price_intraday_count=len(intraday),zero_price_intraday_variations=intraday)
    if intraday: cls="OPTIONSDX_FREE_INTRADAY_VARIATION_FOUND"
    elif zero and len(rows)==len(combos): cls="OPTIONSDX_ZERO_PRICE_EOD_ONLY"
    elif not zero and len(rows)==len(combos): cls="OPTIONSDX_NO_ZERO_PRICE_VARIATION_VISIBLE"
    else: cls="OPTIONSDX_CATALOG_METADATA_PARTIAL"
    out["classification"]=cls
    return write(out,0 if len(rows)>0 else 2)

def write(x,code):
    open("optionsdx_full_variation_census_v01.json","w").write(json.dumps(x,indent=2,sort_keys=True)+"\n")
    print(json.dumps(x,sort_keys=True)); return code

if __name__=="__main__": raise SystemExit(main())
