"""Wrapper around yfinance for price data."""
import logging
from datetime import datetime, timedelta

import pandas as pd
import yfinance as yf

log = logging.getLogger("market")


def latest_close(symbols: list[str]) -> dict[str, float]:
    """Return the most recent daily close price for each symbol."""
    if not symbols:
        return {}
    df = yf.download(
        symbols,
        period="5d",
        interval="1d",
        progress=False,
        auto_adjust=True,
        group_by="ticker" if len(symbols) > 1 else None,
    )
    out: dict[str, float] = {}
    if len(symbols) == 1:
        sym = symbols[0]
        if not df.empty:
            out[sym] = float(df["Close"].iloc[-1])
    else:
        for sym in symbols:
            try:
                close = df[sym]["Close"].dropna()
                if not close.empty:
                    out[sym] = float(close.iloc[-1])
            except (KeyError, AttributeError):
                log.warning("no close price for %s", sym)
    return out


def history(symbols: list[str], days: int) -> pd.DataFrame:
    """Return adjusted close prices for the last `days` calendar days."""
    end = datetime.utcnow()
    start = end - timedelta(days=days + 30)  # pad for weekends/holidays
    df = yf.download(
        symbols,
        start=start,
        end=end,
        interval="1d",
        progress=False,
        auto_adjust=True,
        group_by="ticker" if len(symbols) > 1 else None,
    )
    if len(symbols) == 1:
        return df[["Close"]].rename(columns={"Close": symbols[0]})
    closes = pd.DataFrame()
    for sym in symbols:
        try:
            closes[sym] = df[sym]["Close"]
        except (KeyError, AttributeError):
            log.warning("no history for %s", sym)
    return closes.dropna(how="all")


def momentum_scores(symbols: list[str], lookback_days: int) -> dict[str, float]:
    """Total return over the lookback window for each symbol."""
    closes = history(symbols, lookback_days + 5)
    out: dict[str, float] = {}
    for sym in closes.columns:
        series = closes[sym].dropna()
        if len(series) < lookback_days // 2:
            continue
        start_price = series.iloc[0]
        end_price = series.iloc[-1]
        if start_price > 0:
            out[sym] = (end_price - start_price) / start_price
    return out
