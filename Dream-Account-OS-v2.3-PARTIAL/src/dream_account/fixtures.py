from .models import Book, Candle


def candles(base: float, breakout: float | None = None) -> list[Candle]:
    rows = []
    for i in range(24):
        price = base + i * 0.02
        rows.append(Candle(i * 900000, price, price + 0.25, price - 0.25, price + 0.05, 1000 + i * 5, (i + 1) * 900000 - 1))
    if breakout is not None:
        rows[-2] = Candle(22 * 900000, breakout - 0.2, breakout + 0.8, breakout - 0.3, breakout + 0.5, 2500, 23 * 900000 - 1)
        rows[-1] = Candle(23 * 900000, breakout + 0.4, breakout + 0.6, breakout - 0.45, breakout + 0.15, 1800, 24 * 900000 - 1)
    return rows


def liquid_book(mid: float = 100.0) -> Book:
    bids = [(mid - 0.01 * i, 100) for i in range(1, 101)]
    asks = [(mid + 0.01 * i, 100) for i in range(1, 101)]
    return Book(bids[0][0], asks[0][0], bids, asks)
