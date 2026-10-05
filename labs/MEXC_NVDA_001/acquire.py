"""Unauthenticated public market GET only; raw evidence is never replaced."""
import concurrent.futures, datetime as dt, hashlib, json, pathlib, time, urllib.request
ROOT=pathlib.Path(__file__).resolve().parent
RAW=ROOT/'raw'; RAW.mkdir(exist_ok=True)
BASE='https://contract.mexc.com/api/v1/contract/'
ALLOWED=('detail','kline/','funding_rate/','depth/','depth_commits/','deals/','index_price/','fair_price/','ticker/')
def get(route, name):
    assert route.startswith(ALLOWED) and '..' not in route
    path=RAW/(name+'.json')
    if path.exists(): return json.loads(path.read_text())
    rec={'url':BASE+route,'request_start_ns':time.time_ns(),'monotonic_start_ns':time.monotonic_ns()}
    for attempt in range(3):
        try:
            with urllib.request.urlopen(rec['url'],timeout=20) as r:
                body=r.read(); rec.update(http_status=r.status,body_sha256=hashlib.sha256(body).hexdigest(),response=json.loads(body))
            break
        except Exception as e:
            rec['error']=str(e); time.sleep(attempt+1)
    rec['request_end_ns']=time.time_ns(); rec['monotonic_end_ns']=time.monotonic_ns()
    path.write_text(json.dumps(rec,separators=(',',':')))
    return rec
def main():
    freeze=ROOT/'PRE_OUTCOME_FREEZE.json'
    assert freeze.exists()
    info=get('detail','contract_detail')
    end=int(time.time()//60)*60-60
    state={'freeze_sha256':hashlib.sha256(freeze.read_bytes()).hexdigest(),'end':end,'start':1753228800}
    state_path=ROOT/'acquisition_manifest.json'
    if state_path.exists(): state=json.loads(state_path.read_text()); end=state['end']
    state_path.write_text(json.dumps(state,indent=2))
    jobs=[]
    for t in range(state['start'],end+1,86400):
        for label,seg in [('last',''),('index','index_price/'),('fair','fair_price/')]:
            jobs.append((f'kline/{seg}NVIDIA_USDT?interval=Min1&start={t}&end={min(t+86340,end)}',f'{label}_{t}'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futures=[pool.submit(get,*j) for j in jobs]
        for i,f in enumerate(concurrent.futures.as_completed(futures),1):
            f.result()
            if i%100==0: print(f'acquired {i}/{len(jobs)}',flush=True)
    page=1
    while True:
        rec=get(f'funding_rate/history?symbol=NVIDIA_USDT&page_num={page}&page_size=1000',f'funding_{page}')
        data=rec.get('response',{}).get('data',{})
        if not data.get('resultList') or page>=data.get('totalPage',page): break
        page+=1
    # Spot symbol identity census only, no accounts.
    try:
        url='https://api.mexc.com/api/v3/exchangeInfo'
        body=urllib.request.urlopen(url,timeout=25).read()
        (RAW/'spot_exchange_info.json').write_text(json.dumps({'url':url,'received_ns':time.time_ns(),'body_sha256':hashlib.sha256(body).hexdigest(),'response':json.loads(body)},separators=(',',':')))
    except Exception as e: (RAW/'spot_exchange_info.json').write_text(json.dumps({'url':url,'error':str(e)}))
    print('acquisition complete',flush=True)
if __name__=='__main__': main()
