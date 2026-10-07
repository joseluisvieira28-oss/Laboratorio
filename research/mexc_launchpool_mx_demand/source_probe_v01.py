import ccxt, json, os, re, hashlib
OUT="artifacts/mexc_launchpool_mx_demand_v01_source"
os.makedirs(OUT,exist_ok=True)
ex=ccxt.mexc({"enableRateLimit":True})

def canon(x):
    return json.dumps(x,sort_keys=True,ensure_ascii=False,default=str)

def walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj,list):
        for v in obj:
            yield from walk(v)

def is_article_dict(d):
    keys={str(k).lower() for k in d}
    has_title=any(("title" in k or k in {"name","subject"}) for k in keys)
    has_identity=any(("id" in k or "url" in k or "time" in k or "date" in k or "publish" in k) for k in keys)
    return has_title and has_identity

def articles_from(resp):
    out=[]
    seen=set()
    for d in walk(resp):
        if is_article_dict(d):
            s=canon(d)
            if s not in seen:
                seen.add(s); out.append(d)
    return out

def recursive_values(obj,keyname):
    vals=[]
    if isinstance(obj,dict):
        for k,v in obj.items():
            if str(k).lower()==keyname.lower():
                vals.append(v)
            vals.extend(recursive_values(v,keyname))
    elif isinstance(obj,list):
        for v in obj: vals.extend(recursive_values(v,keyname))
    return vals

schemes=[
 ("pageNum","pageSize"),
 ("page","pageSize"),
 ("pageNum","limit"),
 ("page","limit"),
]
scheme_results=[]
chosen=None
for page_key,size_key in schemes:
    try:
        p1=ex.spot_public_get_announcements({page_key:1,size_key:100})
        p2=ex.spot_public_get_announcements({page_key:2,size_key:100})
        a1=articles_from(p1); a2=articles_from(p2)
        h1=hashlib.sha256(canon(p1).encode()).hexdigest()
        h2=hashlib.sha256(canon(p2).encode()).hexdigest()
        rec={"page_key":page_key,"size_key":size_key,"page1_articles":len(a1),"page2_articles":len(a2),"responses_differ":h1!=h2}
        scheme_results.append(rec)
        if chosen is None and len(a1)>0 and h1!=h2:
            chosen=(page_key,size_key,p1)
    except Exception as e:
        scheme_results.append({"page_key":page_key,"size_key":size_key,"error":repr(e)})

if chosen is None:
    base=ex.spot_public_get_announcements({})
    chosen=("pageNum","pageSize",base)

page_key,size_key,first=chosen
tps=[x for x in recursive_values(first,"totalPage") if isinstance(x,(int,float,str))]
total_page=None
for x in tps:
    try:
        n=int(x)
        if n>0: total_page=max(total_page or 0,n)
    except: pass
if total_page is None: total_page=1
total_page=min(total_page,500)

pages=[]
all_articles=[]
seen_articles=set()
last_hashes=set()
for page in range(1,total_page+1):
    try:
        resp=first if page==1 else ex.spot_public_get_announcements({page_key:page,size_key:100})
        h=hashlib.sha256(canon(resp).encode()).hexdigest()
        if page>1 and h in last_hashes:
            break
        last_hashes.add(h)
        arts=articles_from(resp)
        pages.append({"page":page,"articles":len(arts),"hash":h})
        for a in arts:
            s=canon(a)
            if s not in seen_articles:
                seen_articles.add(s); all_articles.append(a)
    except Exception as e:
        pages.append({"page":page,"error":repr(e)})
        break

def textish(d):
    vals=[]
    for k,v in d.items():
        if isinstance(v,(str,int,float)):
            vals.append(str(v))
    return " ".join(vals)

launch=[a for a in all_articles if "launchpool" in textish(a).lower()]
mx_title_or_row=[a for a in launch if re.search(r"\bMX\b",textish(a),re.I)]

summary={
 "endpoint":"MEXC public announcements via CCXT spotPublicGetAnnouncements",
 "authenticated":False,
 "market_prices_opened":False,
 "pagination_scheme":{"page_key":page_key,"size_key":size_key},
 "reported_total_page":total_page,
 "pages_fetched":len(pages),
 "unique_articles":len(all_articles),
 "launchpool_articles_by_list_metadata":len(launch),
 "launchpool_rows_with_MX_in_list_metadata":len(mx_title_or_row),
 "scheme_results":scheme_results,
 "article_sample_keys":sorted(list(all_articles[0].keys())) if all_articles else [],
}
for name,obj in [
 ("source_probe_summary.json",summary),
 ("pages.json",pages),
 ("all_articles.json",all_articles),
 ("launchpool_articles.json",launch),
 ("launchpool_mx_list_metadata.json",mx_title_or_row),
]:
    with open(f"{OUT}/{name}","w",encoding="utf-8") as f:
        json.dump(obj,f,ensure_ascii=False,indent=2,default=str)

print(json.dumps(summary,indent=2))
