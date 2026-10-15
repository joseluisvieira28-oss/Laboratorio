"""Additional V5-CONVEX experimental signals. Pure read-only computation; no orders."""
from engine.three_convex_v05.signals import (
    MS5, Bar, Halt, aggregate_complete, parent_signal_function,
)
LANES = {
    "SOL_CONVEX_4H_EXPERIMENTAL": ("SOL_USDT", 48),
    "BNB_CONVEX_30M_EXPERIMENTAL": ("BNB_USDT", 6),
    "ETH_CONVEX_1H_EXPERIMENTAL": ("ETH_USDT", 12),
}

def experimental_signals(symbol, bars, now_ms, activation_ms, *, warmup_bars=250):
    """Evaluate only an already-completed timeframe, no backfill or look-ahead.

    Caller supplies authenticated-source-agnostic validated public Binance 5m
    bars with timestamps; no feed/parity/execution claim is inferred here.
    """
    if symbol not in {"SOL_USDT", "BNB_USDT", "ETH_USDT"}:
        raise Halt("UNSUPPORTED_EXPERIMENTAL_SYMBOL")
    if type(now_ms) is not int or type(activation_ms) is not int:
        raise Halt("INVALID_CLOCK")
    if not bars or type(warmup_bars) is not int or warmup_bars < 250:
        raise Halt("UNPROVEN_WARMUP")
    candles=[b.validate() if isinstance(b,Bar) else None for b in bars]
    if any(b is None for b in candles):
        raise Halt("NONCANONICAL_FIVE_MINUTE_BAR")
    if any(b.t != candles[0].t+i*MS5 for i,b in enumerate(candles)):
        raise Halt("GAP_OR_DUPLICATE_FIVE_MINUTE_BARS")
    if candles[-1].t + MS5 + 1000 > now_ms:
        raise Halt("INCOMPLETE_BAR")
    signal_fn=parent_signal_function()
    out=[]
    for lane,(asset,n) in LANES.items():
        if asset!=symbol:continue
        tf=aggregate_complete(candles,n)
        if len(tf)<warmup_bars:continue
        last=tf[-1]
        close=last["t"]+n*MS5
        if close != candles[-1].t+MS5:continue
        if close<activation_ms or not 1000<=now_ms-close<=180000:
            continue
        flags,details=signal_fn(tf)
        if flags[-1]:
            out.append({
                "lane":lane,"symbol":symbol,"signal_close_ms":close,
                "signal_id":f"{lane}:{close}",
                "tf_minutes":n*5,
                "score":details[-1]["score"],
                "category":"EXPERIMENTAL_HISTORICAL_ONLY",
                "not_an_order":True,
                "independent_oos_proven":False,
                "execution_profit_proven":False,
            })
    return out

def experimental_message(signal):
    lane=signal.get("lane")
    if lane not in LANES or signal.get("symbol")!=LANES[lane][0]:
        raise Halt("BAD_EXPERIMENTAL_SIGNAL_IDENTITY")
    close=signal.get("signal_close_ms")
    if type(close) is not int or signal.get("signal_id")!=f"{lane}:{close}":
        raise Halt("BAD_SIGNAL_CLOSE_BINDING")
    from datetime import datetime, timezone
    date=datetime.fromtimestamp(close/1000,timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    return (
        "🔬🎣 CONVEX V5 | SINAL EXPERIMENTAL (NÃO É ORDEM)\n"
        f"Estratégia: {lane}\nMercado: {signal['symbol']} | LONG potencial\n"
        f"Vela fechada: {date}\nSignal ID: {signal['signal_id']}\n"
        "HISTÓRICO APENAS | OOS e rentabilidade não comprovados\n"
        "MEXC: nenhuma ordem enviada ou preenchimento confirmado"
    )
