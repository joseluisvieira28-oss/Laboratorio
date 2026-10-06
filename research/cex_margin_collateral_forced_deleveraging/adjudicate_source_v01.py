"""Conservative source diagnostic; tags are NOT accepted mechanism events."""
import collections,datetime,gzip,hashlib,json,pathlib,re
P=pathlib.Path(__file__).parent
def text_nodes(v):
    if isinstance(v,dict):
        if v.get('node')=='text': yield v.get('text','')
        for x in v.get('child',[]):yield from text_nodes(x)
    elif isinstance(v,list):
        for x in v:yield from text_nodes(x)
def normalize(body):
    try:return ' '.join(text_nodes(json.loads(body)))
    except (ValueError,TypeError):return re.sub('<[^>]+>',' ',str(body))
def main():
    raw=json.loads((P/'SOURCE_DETAIL_RECEIPT.json').read_text()); rows=[]
    for x in raw:
        d=x.get('data');a=x['catalog_entry'];t=normalize(d.get('body','')) if d else ''
        negative=bool(re.search(r'existing positions.{0,100}will not be affected',t,re.I))
        positive=bool(re.search(r'existing positions.{0,100}will be affected',t,re.I))
        dates=re.findall(r'(202[45]-\d{2}-\d{2})\s+(\d{2}:\d{2})(?::\d{2})?\s*\(UTC\)',t)
        tags=[]
        if not d:tags.append('DETAIL_TRANSPORT_FAILURE')
        if negative:tags.append('EXISTING_POSITIONS_EXCLUDED')
        if positive:tags.append('EXISTING_POSITIONS_AFFECTED_PROVISIONAL')
        if re.search(r'(updated|amended) on',t,re.I):tags.append('BODY_DECLARES_REVISION')
        if re.search(r'automatic settlement|automatically settl',t,re.I):tags.append('SETTLEMENT_CONFOUND_REQUIRES_REJECTION_OR_BINDING_REVIEW')
        if re.search(r'collateral',a['title'],re.I):tags.append('COLLATERAL_TO_DERIVATIVE_BINDING_NOT_ESTABLISHED')
        tags.append('PRE_EFFECTIVE_CONTENT_NOT_VERIFIED')
        rows.append({'article_code':a['code'],'title':a['title'],'catalog_publication_ms':a['releaseDate'],'official_url':'https://www.binance.com/en/support/announcement/detail/'+a['code'],'transport':x['transport'],'cms_metadata':{k:d.get(k) for k in ['publishDate','lastUpdateTime','version']} if d else None,'source_text':t,'source_text_sha256':hashlib.sha256(t.encode()).hexdigest(),'body_timestamp_mentions_utc':dates,'diagnostic_tags':tags,'accepted_independent_event':False})
    summary={'detail_attempts':len(rows),'detail_successes':sum(x.get('data') is not None for x in raw),'detail_transport_failures':sum(x.get('data') is None for x in raw),'diagnostic_tag_counts':dict(collections.Counter(tag for x in rows for tag in x['diagnostic_tags'])),'accepted_independent_clusters':0,'event_market_coverage':'NOT_COMPUTED_NO_ACCEPTED_EVENT_UNIVERSE','market_outcomes_opened':0,'normalizer_note':'Body text/timestamp tags are source diagnostics only; not directional old/new table classification or final historical event count.'}
    (P/'SOURCE_DETAIL_SUMMARY.json').write_text(json.dumps(summary,indent=2))
    b=json.dumps(rows,ensure_ascii=False,indent=2).encode();(P/'SOURCE_NORMALIZED_EVIDENCE.json.gz').write_bytes(gzip.compress(b,mtime=0))
    print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
