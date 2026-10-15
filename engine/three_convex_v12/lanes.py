"""Four FINAL experimental CONVEX V5 alert lanes, strictly non-executing.

Full operator inventory: 3 V07 + 3 V11 + exactly 4 V12 = 10; no dynamic
additional markets, no user-configurable new lanes, no exchange transport.
"""
from datetime import datetime, timezone
from engine.three_convex_v05.signals import MS5, Bar, Halt, aggregate_complete, parent_signal_function

LANES = {
    "BNB_CONVEX_NATIVE_5M_EXPERIMENTAL": ("BNB_USDT", 1),
    "SOL_CONVEX_30M_EXPERIMENTAL": ("SOL_USDT", 6),
    "BNB_CONVEX_15M_EXPERIMENTAL": ("BNB_USDT", 3),
    "DOGE_CONVEX_4H_EXPERIMENTAL": ("DOGE_USDT", 48),
}
ASSETS = frozenset(asset for asset,_ in LANES.values())
EXPECTED_V07 = frozenset({"SOL_CONVEX_NATIVE_5M","SOL_CONVEX_1H","BNB_CONVEX_4H"})
EXPECTED_V11 = frozenset({"SOL_CONVEX_4H_EXPERIMENTAL","BNB_CONVEX_30M_EXPERIMENTAL","ETH_CONVEX_1H_EXPERIMENTAL"})
MAX_TOTAL_LANES = 10
assert len(LANES) == 4 and len(set(LANES)|EXPECTED_V07|EXPECTED_V11) == MAX_TOTAL_LANES

def decide(symbol, bars, now_ms, activation_ms, *, warmup_bars=250):
    """Only compute potential LONG on latest strictly completed and fresh bar."""
    if symbol not in ASSETS:
        raise Halt("V12_UNKNOWN_ASSET")
    if type(now_ms) is not int or type(activation_ms) is not int or activation_ms<0:
        raise Halt("V12_BAD_CLOCK_OR_ACTIVATION")
    if type(warmup_bars) is not int or warmup_bars < 250:
        raise Halt("V12_WARMUP_NOT_ALLOWED")
    if not bars:
        return []
    candle_list=[]
    for bar in bars:
        if not isinstance(bar, Bar):
            raise Halt("V12_NOT_CANONICAL_BAR")
        candle_list.append(bar.validate())
    if any(b.t != candle_list[0].t + i * MS5 for i,b in enumerate(candle_list)):
        raise Halt("V12_GAP_OR_DUPLICATE")
    if candle_list[-1].t + MS5 + 1000 > now_ms:
        raise Halt("V12_INCOMPLETE_BAR")
    out=[]
    fn=parent_signal_function()
    for lane,(asset,n) in LANES.items():
        if asset != symbol:
            continue
        resampled=aggregate_complete(candle_list,n)
        if len(resampled)<warmup_bars:
            continue
        last=resampled[-1]
        close_ms=last["t"]+n*MS5
        if close_ms!=candle_list[-1].t+MS5:
            continue
        # Reject replay, time leap and signals older than 3 minutes.
        if close_ms<activation_ms or not (1000<=now_ms-close_ms<=180000):
            continue
        flags,details=fn(resampled)
        if flags[-1]:
            out.append({
                "lane":lane,"symbol":symbol,"signal_close_ms":close_ms,
                "signal_id":f"{lane}:{close_ms}",
                "tf_minutes":n*5,
                "score":details[-1]["score"],
                "category":"V12_HISTORICAL_ONLY_EXPERIMENTAL",
                "direction_potential":"LONG",
                "not_order":True,
                "economic_edge_proven":False,
                "independent_oos_proven":False
            })
    return out

def message_for_signal(sig):
    """Fail closed on unrecognized payload: never forward arbitrary user text."""
    lane=sig.get("lane")
    if lane not in LANES:
        raise Halt("V12_LANE_NOT_ALLOWLISTED")
    if sig.get("symbol") != LANES[lane][0]:
        raise Halt("V12_LANE_ASSET_MISMATCH")
    close=sig.get("signal_close_ms")
    if type(close) is not int or sig.get("signal_id")!=f"{lane}:{close}":
        raise Halt("V12_SIGNAL_ID_NOT_BOUND_TO_CLOSE")
    timestamp=datetime.fromtimestamp(close/1000,timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        "🔬🎣 CONVEX V12 | SINAL EXPERIMENTAL (NÃO É ORDEM)\n"
        f"Estratégia: {lane}\nAtivo: {sig['symbol']} | LONG potencial\n"
        f"Vela fechada: {timestamp}\nID: {sig['signal_id']}\n"
        "Mesmo ativo pode ter sinais sobrepostos: NÃO CONTAR COMO TRADES INDEPENDENTES.\n"
        "Histórico apenas; OOS/forward/edge líquido NÃO COMPROVADOS.\n"
        "Execução e stop MEXC: NÃO CONFIRMADOS. Zero ordens automáticas."
    )
