"""Yahoo Finance data + Clenow-style momentum helpers.

Citations:
- Clenow, Andreas (2015) "Stocks on the Move"
- Momentum formula adapted from teddykoker/blog (notebook 2019-05-19)
- Companion implementation: skyte/momentum
"""
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yfinance as yf
from scipy.stats import linregress

log = logging.getLogger("market")

TRADING_DAYS_PER_YEAR = 252


def _extract_closes(df: pd.DataFrame, symbols: list[str]) -> pd.DataFrame:
    """yfinance returns MultiIndex columns even for single symbols on newer versions.
    Normalize to a flat DataFrame: one column per symbol of close prices."""
    if df.empty:
        return pd.DataFrame()
    out = pd.DataFrame(index=df.index)
    if isinstance(df.columns, pd.MultiIndex):
        for sym in symbols:
            if ("Close", sym) in df.columns:
                out[sym] = df[("Close", sym)]
            elif (sym, "Close") in df.columns:
                out[sym] = df[(sym, "Close")]
    elif "Close" in df.columns and len(symbols) == 1:
        out[symbols[0]] = df["Close"]
    return out.dropna(how="all")


def latest_close(symbols: list[str]) -> dict[str, float]:
    if not symbols:
        return {}
    df = yf.download(symbols, period="5d", interval="1d", progress=False, auto_adjust=True)
    closes = _extract_closes(df, symbols)
    out: dict[str, float] = {}
    for sym in symbols:
        if sym in closes.columns:
            series = closes[sym].dropna()
            if not series.empty:
                out[sym] = float(series.iloc[-1])
        else:
            log.warning("no close price for %s", sym)
    return out


def history(symbols: list[str], days: int) -> pd.DataFrame:
    end = datetime.utcnow()
    start = end - timedelta(days=days + 40)
    df = yf.download(symbols, start=start, end=end, interval="1d",
                     progress=False, auto_adjust=True)
    return _extract_closes(df, symbols)


def clenow_momentum(closes: pd.Series) -> float:
    """Annualized exponential regression slope * R^2 over the input window.

    Verbatim port from teddykoker/blog implementation. The original code:
        def momentum(closes):
            returns = np.log(closes)
            x = np.arange(len(returns))
            slope, _, rvalue, _, _ = linregress(x, returns)
            return ((1 + slope) ** 252) * (rvalue ** 2)
    """
    series = closes.dropna()
    if len(series) < 30:
        return float("nan")
    returns = np.log(series.values)
    x = np.arange(len(returns))
    slope, _, rvalue, _, _ = linregress(x, returns)
    return float(((1 + slope) ** TRADING_DAYS_PER_YEAR) * (rvalue ** 2))


def momentum_scores(symbols: list[str], lookback_days: int = 90) -> dict[str, float]:
    closes = history(symbols, lookback_days + 5)
    out: dict[str, float] = {}
    for sym in closes.columns:
        window = closes[sym].dropna().tail(lookback_days)
        if len(window) < lookback_days // 2:
            continue
        score = clenow_momentum(window)
        if not np.isnan(score):
            out[sym] = score
    return out


def _calendar_days_for_trading_days(trading_days: int) -> int:
    # ~5/7 of calendar days are trading days; add buffer for holidays.
    return int(trading_days * 1.6) + 20


def moving_average(symbol: str, window: int) -> tuple[float, float] | tuple[None, None]:
    """Return (latest_close, latest_MA) for the symbol."""
    df = history([symbol], _calendar_days_for_trading_days(window))
    if df.empty or symbol not in df.columns:
        return None, None
    series = df[symbol].dropna()
    if len(series) < window:
        return None, None
    return float(series.iloc[-1]), float(series.tail(window).mean())


def above_moving_average(symbols: list[str], window: int) -> dict[str, bool]:
    """For each symbol: True if latest close > rolling mean over the window."""
    closes = history(symbols, _calendar_days_for_trading_days(window))
    out: dict[str, bool] = {}
    for sym in closes.columns:
        series = closes[sym].dropna()
        if len(series) < window:
            continue
        out[sym] = float(series.iloc[-1]) > float(series.tail(window).mean())
    return out


def market_regime_ok(benchmark: str = "SPY", window: int = 200) -> bool:
    """Per Clenow: only open new positions when benchmark > its long MA."""
    last, ma = moving_average(benchmark, window)
    if last is None:
        log.warning("regime check skipped: no data for %s", benchmark)
        return True  # be permissive on data failure
    return last > ma
