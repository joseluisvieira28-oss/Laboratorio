import urllib.request,urllib.error,concurrent.futures,json,hashlib,re,ssl,os
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).parent;RAW=ROOT/'evidence/raw'
URLS={
'ECB_clock':'https://www.ecb.europa.eu/press/govcdec/mopo/html/index.en.html',
'ECB_calendar':'https://www.ecb.europa.eu/press/calendars/mgcgc/html/index.en.html',
'ECB_Apr2025':'https://www.ecb.europa.eu/press/pr/date/2025/html/ecb.mp250417~42727d0735.en.html',
'ECB_Jun2025':'https://www.ecb.europa.eu/press/pr/date/2025/html/ecb.mp250605~3b5f67d007.en.html',
'BoE_clock':'https://www.bankofengland.co.uk/monetary-policy',
'BoE_calendar':'https://www.bankofengland.co.uk/monetary-policy/upcoming-mpc-dates',
'BoJ_calendar':'https://www.boj.or.jp/en/about/calendar/index.htm',
'SNB_clock':'https://www.snb.ch/en/publications/communication/speeches/2025/ref_20251121_msl',
'SNB_Sep2026':'https://www.snb.ch/en/publications/communication/press-releases-restricted/pre_20260924',
'Dukascopy_method':'https://www.dukascopy.com/wiki/en/development/data-export/',
'HistData_method':'https://www.histdata.com/f-a-q/',
'MEXC_kline_docs':'https://www.mexc.com/api-docs/futures/market-endpoints/get-candlestick-data',
'MEXC_fee':'https://www.mexc.com/announcements/article/updates-to-api-futures-trading-fees-jun-1-2026-17827791535742',
'Coinbase_candle_docs':'https://docs.cdp.coinbase.com/api-reference/exchange-api/rest-api/products/get-product-candles',
'ECB_consensus_lead':'https://www.ecb.europa.eu/stats/ecb_surveys/survey_of_professional_forecasters/pdf/ecb.spf2026q3.en.pdf',
'ECB_SMA_method':'https://www.ecb.europa.eu/pub/pdf/ecbu/eb202108.en.pdf',
}
def get(x):
 label,url=x;start=datetime.now(timezone.utc).isoformat()
 try:
  ctx=ssl.create_default_context(cafile=os.environ.get('SSL_CERT_FILE'))
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'CryptoLab-Forex-SourceGate/0.1'}),timeout=30,context=ctx) as r:b=r.read();status=r.status;headers=dict(r.headers)
 except urllib.error.HTTPError as e:b=e.read();status=e.code;headers=dict(e.headers)
 except Exception as e:return {'label':label,'url':url,'error':str(e),'started_at_utc':start}
 p=RAW/(hashlib.sha256(b).hexdigest()+'.bin');p.write_bytes(b)
 return {'label':label,'url':url,'status':status,'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'raw_path':str(p.relative_to(ROOT)),'headers':headers,'started_at_utc':start,'completed_at_utc':datetime.now(timezone.utc).isoformat()}
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as p:rs=list(p.map(get,URLS.items()))
(ROOT/'evidence/MACRO_DOCUMENTATION_CERT_REPAIR_RECEIPT_V01.json').write_text(json.dumps({'requests':rs,'outcomes_opened':False,'not_consensus_vintage_proof':True,'tls_verification_disabled':False,'technical_repair':'trusted CA bundle supplied with SSL_CERT_FILE'},indent=2),encoding='utf-8')
print(json.dumps([{k:r.get(k) for k in ['label','status','bytes','error']} for r in rs],indent=2))
