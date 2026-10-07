"""Inspect advertised archive services. Sources only, no node execution."""
import concurrent.futures,json,pathlib
import forensic_scrt287_v54 as c
c.OUT=pathlib.Path(__file__).resolve().parent/'forensic_v59'
SEEDS={
 'secret3_archive_redirect':'https://docs.scrt.network/operators/archive',
 'secret3_rpc_lcd_redirect':'https://docs.scrt.network/operators/rpc-lcd',
 'secret3_archive_docs':'https://docs.scrt.network/operators/archive/',
 'secret3_rpc_lcd_docs':'https://docs.scrt.network/operators/rpc-lcd/',
}
def main():
 c.OUT.mkdir(exist_ok=True);(c.OUT/'raw').mkdir(exist_ok=True)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as p:rows=list(p.map(c.fetch,SEEDS.items()))
 (c.OUT/'receipt.json').write_text(json.dumps({'scope':'SOURCE_ONLY_NO_MARKET_DATA','rows':rows,'H':None,'T0':None,'exhaustion':False},indent=2)+'\n',encoding='utf-8')
 print([(r['id'],r.get('status'),r.get('location')) for r in rows])
if __name__=='__main__':main()
