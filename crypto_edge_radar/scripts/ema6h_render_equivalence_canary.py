from __future__ import annotations
from datetime import datetime
import hashlib,json
from http.server import BaseHTTPRequestHandler,HTTPServer
from radar.ema6h_source_resilience import OFFICIAL_BINANCE_SPOT_ENDPOINTS
from radar.strategies.ema6h_50x200_regime_forward import BinanceSpotKlineFeed
def ms(x): return int(datetime.fromisoformat(x.replace("Z","+00:00")).timestamp()*1000)
samples=[("BTCUSDT","15m",ms("2026-09-26T00:00:00Z"),ms("2026-09-26T02:00:00Z")),("SOLUSDT","15m",ms("2026-09-26T00:00:00Z"),ms("2026-09-26T02:00:00Z")),("BTCUSDT","1d",ms("2026-09-22T00:00:00Z"),ms("2026-09-27T00:00:00Z"))]
now_ms=ms("2026-09-27T18:45:00Z"); rows=[]; good={}
for label,url in OFFICIAL_BINANCE_SPOT_ENDPOINTS:
 e={"label":label,"base_url":url,"samples":{}}; ok=True
 for symbol,interval,start_ms,end_ms in samples:
  key=f"{symbol}:{interval}:{start_ms}:{end_ms}"
  try:
   f=BinanceSpotKlineFeed(timeout=12,max_attempts=1,retry_backoff_seconds=0); f.base_url=url
   cs=f.klines(symbol,interval,start_ms=start_ms,end_ms=end_ms,now_ms=now_ms)
   sci=[[c.open_time,c.open,c.high,c.low,c.close,c.volume,c.close_time] for c in cs]
   h=hashlib.sha256(json.dumps(sci,separators=(",",":")).encode()).hexdigest()
   e["samples"][key]={"status":"PASS","rows":len(cs),"sha256":h}; good.setdefault(key,{}).setdefault(h,[]).append(label)
  except Exception as ex:
   ok=False; e["samples"][key]={"status":"ERROR","error_class":type(ex).__name__,"error":str(ex)[:240]}
 e["all_samples_pass"]=ok; rows.append(e)
successful=[x for x in rows if x["all_samples_pass"]]
divergence={k:v for k,v in good.items() if len(v)!=1}
passed=len(successful)>=2 and len(good)==len(samples) and all(sum(len(z) for z in v.values())>=2 for v in good.values()) and not divergence
receipt={"schema_version":"EMA6H_BINANCE_OFFICIAL_HOST_EQUIVALENCE_V0.1","classification":"PASS_EXACT_SCIENTIFIC_FIELD_EQUIVALENCE" if passed else "FAIL_CLOSED_SOURCE_EQUIVALENCE","pass":passed,"fully_successful_hosts":[x["label"] for x in successful],"sample_count":len(samples),"divergence":divergence,"endpoints":rows,"science_changed":False,"authenticated_exchange_api_used":False,"orders_created":False,"exchange_mutation_performed":False,"live_capital_enabled":False}
print("EMA6H_RENDER_EQUIVALENCE "+json.dumps(receipt,sort_keys=True),flush=True)

import urllib.request
archive_urls=[
 "https://data.binance.vision/data/spot/daily/klines/BTCUSDT/15m/BTCUSDT-15m-2026-09-26.zip.CHECKSUM",
 "https://data.binance.vision/data/spot/daily/klines/SOLUSDT/15m/SOLUSDT-15m-2026-09-26.zip.CHECKSUM",
]
archive_probe=[]
for url in archive_urls:
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"crypto-edge-radar/ema6h-archive-probe-v0.1"}),timeout=15) as resp:
   body=resp.read()
   archive_probe.append({"url":url,"status":"PASS","http_status":resp.status,"bytes":len(body),"sha256":hashlib.sha256(body).hexdigest()})
 except Exception as ex:
  archive_probe.append({"url":url,"status":"ERROR","error_class":type(ex).__name__,"error":str(ex)[:240]})
print("EMA6H_ARCHIVE_PROBE "+json.dumps({"classification":"ARCHIVE_REACHABLE" if all(x["status"]=="PASS" for x in archive_probe) else "ARCHIVE_UNREACHABLE","results":archive_probe,"science_changed":False,"authenticated_exchange_api_used":False,"exchange_mutation_performed":False},sort_keys=True),flush=True)

class H(BaseHTTPRequestHandler):
 def do_GET(self):
  b=json.dumps(receipt,sort_keys=True).encode(); self.send_response(200); self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b))); self.end_headers(); self.wfile.write(b)
 def log_message(self,*a): pass
HTTPServer(("0.0.0.0",10000),H).serve_forever()
