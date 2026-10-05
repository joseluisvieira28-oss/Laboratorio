#!/usr/bin/env python3
import json,requests
HEADERS={
 "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/139 Safari/537.36",
 "Accept":"application/json, text/plain, */*","Accept-Language":"en-US,en;q=0.9",
 "Referer":"https://www.nasdaq.com/market-activity/earnings"
}
cases=["2026-07-30","07-30-2026","07/30/2026","2026-08-05","08-05-2026","08/05/2026"]
out=[]
for d in cases:
 r=requests.get("https://api.nasdaq.com/api/calendar/earnings",params={"date":d},headers=HEADERS,timeout=30)
 try:j=r.json()
 except Exception:j={"_text":r.text[:2000]}
 data=j.get("data") if isinstance(j,dict) else None
 rows=(data or {}).get("rows") if isinstance(data,dict) else None
 out.append({"date_arg":d,"http":r.status_code,"data_keys":list(data.keys()) if isinstance(data,dict) else None,
             "row_count":len(rows) if isinstance(rows,list) else None,"sample_rows":rows[:5] if isinstance(rows,list) else None,
             "status":j.get("status") if isinstance(j,dict) else None})
print(json.dumps(out,indent=2))
