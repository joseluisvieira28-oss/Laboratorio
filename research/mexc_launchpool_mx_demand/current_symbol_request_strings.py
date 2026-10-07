import requests,re,json
URL="https://static.mocortech.com/production/web-v4-home-seo/65/_next/static/chunks/1z3331wy82let.js"
t=requests.get(URL,timeout=30).text
out=set()
for m in re.finditer(r'request\(([^)]{0,800})\)',t):
    x=m.group(0)
    l=x.lower()
    if "spot" in l or "symbol" in l or "/api/" in l:
        out.add(x)
for q in re.findall(r'["\']([^"\']{3,300})["\']',t):
    l=q.lower()
    if ("/api/" in l or "/spot/" in l) and ("symbol" in l or "spot" in l):
        out.add(q)
print(json.dumps(sorted(out),ensure_ascii=False,indent=2))
