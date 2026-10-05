"""Pooled public HTTP transport. Preserve proxy/TLS settings and raw timing."""
import time
import urllib.parse
import collector as c


class PublicHTTP:
    def __init__(self, client=None):
        if client is None:
            import httpx
            client=httpx.Client(timeout=12,follow_redirects=False,trust_env=True,
                                limits=httpx.Limits(max_connections=8,max_keepalive_connections=8,keepalive_expiry=120),
                                headers={'User-Agent':'CryptoLab-FX-PooledBurnIn/0.2','Accept-Encoding':'identity'})
        self.client=client

    def fetch(self, source, url=None):
        import ecb_watcher as ecb
        url=url or c.SOURCES[source]
        additional=['https://data-api.binance.vision/api/v3/depth?symbol=EURUSDT&limit=5000',
                    'https://api.mexc.com/api/v1/contract/depth/EUR_USDT?limit=1000']
        if url not in c.SOURCES.values() and url not in additional and not ecb.allowed_release(url,'2026-10-29'):
            raise PermissionError('URL_NOT_ALLOWLISTED')
        row={'source':source,'url':url,'started_ms':time.time_ns()//1_000_000,
             'transport':'HTTPX_POOLED_TLS_VERIFIED_TRUST_ENV'}
        begin=time.monotonic_ns();raw=b''
        try:
            with self.client.stream('GET',url) as response:
                row.update(http_status=response.status_code,headers=dict(response.headers))
                chunks=[];size=0
                for part in response.iter_raw():
                    size+=len(part)
                    if size>4_000_000:raise ValueError('RESPONSE_TOO_LARGE')
                    chunks.append(part)
                raw=b''.join(chunks)
                if 300<=response.status_code<400:raise PermissionError('REDIRECT_NOT_ALLOWED')
                if response.status_code!=200:row['error']='HTTP_ERROR'
        except Exception as exc:
            row['error']=type(exc).__name__+': '+str(exc)
        row.update(received_ms=time.time_ns()//1_000_000,
                   rtt_ms=(time.monotonic_ns()-begin)/1_000_000,
                   raw_sha256=c.digest(raw),raw_bytes=len(raw))
        return row,raw

    def close(self):self.client.close()
