"""Contemporary public spot filters and five-level liquidity witness, diagnostic only."""
from shadow import get,ASSETS,FOLDER
from experiment import OUT
from decimal import Decimal as D,ROUND_DOWN
import json,pandas as pd,time
quote=json.loads(sorted(FOLDER.glob('quote*'))[0].read_text())
rows=[];receipts={}
for a in ASSETS:
    info=get('exchangeInfo',symbol=a)['symbols'][0]
    filters={f['filterType']:f for f in info['filters']}
    receipts[a]=dict(fetched_ms=int(time.time()*1000),filters=filters,status=info['status'])
    depth=next(r['depth'] for r in quote['receipts'] if r['symbol']==a)
    bid,ask=D(depth['bids'][0][0]),D(depth['asks'][0][0])
    step=D(filters['LOT_SIZE']['stepSize'])
    minimum=D((filters.get('NOTIONAL') or filters.get('MIN_NOTIONAL'))['minNotional'])
    for capital in [100,250,500,1000,5000,10000]:
        size=D(capital)/15
        qty=(size/ask/step).to_integral_value(rounding=ROUND_DOWN)*step
        rows.append([a,capital,float(size),float(qty),float(minimum),float(step),float((ask-bid)/((ask+bid)/2)*10000),bool(qty*ask>=minimum),bool(qty<=D(depth['asks'][0][1]))])
(OUT/'current_filters.json').write_text(json.dumps(receipts,indent=2))
pd.DataFrame(rows,columns='asset capital entry_budget qty min_notional qty_step full_spread_bps passes_current_min top_ask_covers_size'.split()).to_csv(OUT/'current_execution.csv',index=False)
