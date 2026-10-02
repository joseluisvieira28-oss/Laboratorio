#!/usr/bin/env python3
import json, re

p="artifacts/mexc_event_futures/browser_source_v011.json"
j=json.load(open(p,encoding="utf-8"))

def relevant(s):
    x=(s or "").lower()
    return any(k in x for k in ["event","predict","payout","timeunit","btc_usdt","future"])

print("=== V0.11.1 EVIDENCE SUMMARY ===")
print("VERDICT="+j.get("verdict",""))
print("PAGES")
for x in j.get("pages",[]):
    print(json.dumps({
      "status":x.get("status"),"final_url":x.get("final_url"),
      "title":x.get("title"),"body_chars":x.get("body_chars"),
      "visible_matches":x.get("visible_matches",[])[:20]
    },ensure_ascii=False))

print("RELEVANT_CANDIDATE_ROUTES")
seen=set()
for s in j.get("candidate_routes",[]):
    if relevant(s) and s not in seen:
        seen.add(s); print(s)
        if len(seen)>=80: break

print("RELEVANT_ABORTED_NON_GETS")
seen=set()
for x in j.get("aborted_non_gets",[]):
    u=x.get("url","")
    key=(x.get("method"),u)
    if relevant(u) and key not in seen:
        seen.add(key); print(json.dumps(x,ensure_ascii=False))
        if len(seen)>=80: break

print("RELEVANT_NETWORK_GETS")
seen=set()
for x in j.get("network_gets",[]):
    u=x.get("url","")
    if relevant(u) and u not in seen:
        seen.add(u); print(json.dumps(x,ensure_ascii=False))
        if len(seen)>=80: break

print("RESPONSE_PREVIEW_HINTS")
count=0
for x in j.get("response_previews",[]):
    preview=x.get("preview","")
    if relevant(preview) or relevant(x.get("url","")):
        snippets=[]
        low=preview.lower()
        for kw in ["payout","prediction-futures","event-futures","timeunit","btc_usdt"]:
            i=low.find(kw)
            if i>=0:
                snippets.append(preview[max(0,i-120):i+len(kw)+220].replace("\n"," "))
        print(json.dumps({
          "url":x.get("url"),"status":x.get("status"),
          "content_type":x.get("content_type"),"sha256":x.get("sha256"),
          "snippets":snippets[:5]
        },ensure_ascii=False))
        count+=1
        if count>=50: break
