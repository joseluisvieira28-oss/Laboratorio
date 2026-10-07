"""Bounded creation metadata probes near frozen/manifest deployment periods."""
import concurrent.futures as cf
import json
from tmfcb_v04_factory_archive import scan_range, FACTORY, PAIR, keccak, OUT

# These are source-date search brackets, not claimed deployment boundaries.
WINDOWS=[('OGV',15050000,15150000),('SYRUP',21100000,21200000),
         ('LBR_V2',18000000,18100000),('POL',18426253,18526253),
         ('G',20250000,20350000),('HIFI',16300000,16400000),
         ('T',13912436,14012436),('TBTC_V2',13042356,13142356)]

def main():
    factories=[(FACTORY,PAIR),('0x1f98431c8ad98523631ae4a59f267346ea31f984',
                 keccak(b'PoolCreated(address,address,uint24,int24,address)'))]
    results=[]
    with cf.ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(scan_range,a,b,f,e):(label,a,b,f) for label,a,b in WINDOWS for f,e in factories}
        for future in cf.as_completed(futures):
            label,a,b,f=futures[future]
            try:
                pages,creations,complete=future.result()
                results.append({'target_window':label,'from':a,'to':b,'factory':f,
                                'complete':complete,'pages':pages,'creations':creations})
            except Exception as exc:
                results.append({'target_window':label,'from':a,'to':b,'factory':f,'complete':False,'error':str(exc)})
            (OUT/'targeted_factory_windows.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
            print(json.dumps({'finished':len(results),'total':len(futures),
                             'creations':sum(len(r.get('creations',[])) for r in results)}),flush=True)

if __name__=='__main__': main()
