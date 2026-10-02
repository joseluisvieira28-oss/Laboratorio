# Exact source-gate selection algorithm factored for a single forward polling round.
import concurrent.futures
import math
from priority_source_gates_v013 import get, positive, valid_ticker

def options_round(evidence, round_id):
    errors = []
    accepted = {}
    for currency in ('BTC','ETH'):
        try:
            instruments, recv, meta_ref = get('get_instruments',
                {'currency':currency,'kind':'option','expired':'false'}, evidence,
                f'options-{round_id}-{currency}-instruments.json')
            eligible = [m for m in instruments if m.get('is_active') is True
                        and m.get('kind')=='option' and m.get('base_currency')==currency
                        and 7*86400000 <= m['expiration_timestamp']-recv <= 30*86400000]
            expiry = min(m['expiration_timestamp'] for m in eligible)
            eligible = [m for m in eligible if m['expiration_timestamp']==expiry]
            summary, _, sum_ref = get('get_book_summary_by_currency',
                {'currency':currency,'kind':'option'}, evidence,
                f'options-{round_id}-{currency}-summary.json')
            summaries = {r['instrument_name']:r for r in summary}
            choices = []
            for side in ('call','put'):
                scored = []
                for m in eligible:
                    if m['option_type'] != side:
                        continue
                    s = summaries.get(m['instrument_name'],{})
                    f = s.get('underlying_price'); iv = s.get('mark_iv')
                    if not positive(f) or not positive(iv):
                        continue
                    if (side=='call' and m['strike']<=f) or (side=='put' and m['strike']>=f):
                        continue
                    vol = iv/100; tau = (expiry-recv)/(365.25*86400000)
                    d1 = (math.log(f/m['strike']) + .5*vol*vol*tau)/(vol*math.sqrt(tau))
                    delta = .5*(1+math.erf(d1/math.sqrt(2))) - (side=='put')
                    scored.append((abs(abs(delta)-.25),m['instrument_name'],m))
                choices.extend(x[2] for x in sorted(scored)[:2])
            candidates = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
                futures = {pool.submit(get,'ticker',{'instrument_name':m['instrument_name']},
                            evidence,f'options-{round_id}-{m["instrument_name"]}-ticker.json'):m
                           for m in choices}
                for fut,m in futures.items():
                    t, received, ref = fut.result()
                    candidates.append({'instrument':m['instrument_name'],'option_type':m['option_type'],
                        'valid':valid_ticker(t,m,received),'ticker':t,'received_at_ms':received,
                        'raw_sha256':ref['sha256'],'metadata_sha256':meta_ref['sha256'],
                        'selection_summary_sha256':sum_ref['sha256']})
            pair = []
            for side in ('call','put'):
                valid = [r for r in candidates if r['valid'] and r['option_type']==side]
                if valid:
                    pair.append(min(valid,key=lambda r:(abs(abs(r['ticker']['greeks']['delta'])-.25),r['instrument'])))
            ok = len(pair)==2 and abs(pair[0]['ticker']['timestamp']-pair[1]['ticker']['timestamp'])<=5000
            accepted[currency] = {'passed':ok,'expiry_ms':expiry,'candidates':candidates,
                                  'selected_pair':pair if ok else []}
        except Exception as exc:
            errors.append({'round':round_id,'currency':currency,'type':type(exc).__name__,'error':str(exc)})
            accepted[currency] = {'passed':False}
    return accepted, errors
