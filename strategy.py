"""Clenow "Stocks on the Move" — published momentum strategy.

Sources (cite-able, parameters from the book, not invented):
- Clenow, Andreas (2015) "Stocks on the Move: Beating the Market with Hedge Fund
  Momentum Strategies". Chapter 7 has the full rule set.
- Reference implementations:
    * https://github.com/teddykoker/blog (notebook 2019-05-19)
    * https://github.com/skyte/momentum
    * https://github.com/Suchismit4/NiftyOnTheMove

Rules implemented here:
1. Momentum score = annualized exp regression slope * R^2 over 90 days
2. Trend filter: drop stocks below their 100-day moving average
3. Market regime filter: only open new positions when SPY > 200-day MA
4. Selection: top-N by momentum, equal weight
5. Exit: stock falls out of top-N OR drops below 100-day MA
6. Rebalance: weekly (Wednesday in the book; we follow the same)
7. Initial run: if portfolio empty, do an immediate rebalance regardless of weekday

Simplification vs the book:
- We use EQUAL weight instead of ATR-based risk parity sizing. Book's ATR
  sizing requires per-stock daily volatility and is non-trivial; equal weight
  is also a valid published approach (Asness/Moskowitz). Future work.
"""
from dataclasses import dataclass
from datetime import date

import config
import market
import paper_book
import universe


@dataclass
class Order:
    action: str    # "BUY" or "SELL"
    symbol: str
    quantity: float
    reason: str


REBALANCE_WEEKDAY = 2          # Wednesday (per Clenow). Mon=0, Sun=6.
TREND_FILTER_DAYS = 100        # 100-day MA filter
REGIME_BENCHMARK = "SPY"
REGIME_MA_DAYS = 200


def _is_rebalance_day(today: date) -> bool:
    return today.weekday() == REBALANCE_WEEKDAY


def _passes_trend_filter(symbols: list[str]) -> set[str]:
    """Keep only symbols whose latest close > 100-day MA."""
    flags = market.above_moving_average(symbols, TREND_FILTER_DAYS)
    return {s for s, ok in flags.items() if ok}


def _rank_by_momentum(symbols: list[str]) -> list[tuple[str, float]]:
    scores = market.momentum_scores(symbols, lookback_days=config.MOMENTUM_LOOKBACK_DAYS)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def stop_loss_orders(price_map: dict[str, float]) -> list[Order]:
    """Per Clenow rule 5: exit if stock drops below its 100-day MA.

    Approximation: we also keep the simple % stop-loss as a safety net
    against thin-data symbols where MA can't be computed.
    """
    orders: list[Order] = []
    positions = paper_book.load_positions()
    if not positions:
        return orders

    above_ma = market.above_moving_average(list(positions.keys()), TREND_FILTER_DAYS)
    for symbol, pos in positions.items():
        sell = False
        reason = ""
        if symbol in above_ma and not above_ma[symbol]:
            sell = True
            reason = "exit_below_100ma"
        else:
            current = price_map.get(symbol)
            if current and pos["avg_cost"] > 0:
                loss = (pos["avg_cost"] - current) / pos["avg_cost"]
                if loss >= config.STOP_LOSS_PCT:
                    sell = True
                    reason = f"hard_stop {loss:.1%}"
        if sell:
            orders.append(Order("SELL", symbol, pos["quantity"], reason))
    return orders


def rebalance_orders(price_map: dict[str, float]) -> list[Order]:
    """Per Clenow: drop stocks that fell out of top-N, add new ones up to N positions.

    Market regime filter gates new BUYs (not exits — we still let losers leave).
    """
    universe_syms = universe.symbols()

    eligible = _passes_trend_filter(universe_syms)
    ranked = _rank_by_momentum(list(eligible))
    target_set = [s for s, score in ranked[: config.TOP_N] if score > 0]

    current = paper_book.load_positions()
    orders: list[Order] = []

    # Sells: any current holding not in target
    for symbol in list(current.keys()):
        if symbol not in target_set:
            orders.append(Order("SELL", symbol, current[symbol]["quantity"], "rebalance_exit"))

    if not market.market_regime_ok(REGIME_BENCHMARK, REGIME_MA_DAYS):
        # bear market: do not open new positions. Existing exits still apply.
        return orders

    # Buys: equal-weight target_set with current equity
    cash = paper_book.load_cash()
    equity = cash + paper_book.positions_value(price_map)
    if not target_set:
        return orders
    per_slot = equity / len(target_set)

    for symbol in target_set:
        price = price_map.get(symbol)
        if not price or price <= 0:
            continue
        current_qty = current.get(symbol, {"quantity": 0})["quantity"]
        deficit_value = per_slot - current_qty * price
        if deficit_value > price:
            qty = round(deficit_value / price, 4)
            orders.append(Order("BUY", symbol, qty, f"rebalance_rank_{target_set.index(symbol)+1}"))

    return orders


def decide(today: date, price_map: dict[str, float]) -> list[Order]:
    """Daily entry point: stop-loss always; rebalance Wed or when empty."""
    orders = stop_loss_orders(price_map)
    if _is_rebalance_day(today) or not paper_book.load_positions():
        orders.extend(rebalance_orders(price_map))
    return orders
