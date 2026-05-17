"""Decide what to BUY and SELL based on momentum + stop-loss rules.

Pure function: given current state and prices, return a list of orders.
No side effects, no broker calls. tick.py executes the orders via paper_book.
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


def _is_rebalance_day(today: date) -> bool:
    """True only on the first Mon-Fri of the month."""
    if today.weekday() >= 5:
        return False
    for d in range(1, today.day):
        if date(today.year, today.month, d).weekday() < 5:
            return False
    return True


def stop_loss_orders(price_map: dict[str, float]) -> list[Order]:
    """Sell any position whose unrealized loss exceeds the stop-loss threshold."""
    orders: list[Order] = []
    for symbol, pos in paper_book.load_positions().items():
        current = price_map.get(symbol)
        if current is None or pos["avg_cost"] <= 0:
            continue
        loss_pct = (pos["avg_cost"] - current) / pos["avg_cost"]
        if loss_pct >= config.STOP_LOSS_PCT:
            orders.append(Order(
                action="SELL",
                symbol=symbol,
                quantity=pos["quantity"],
                reason=f"stop_loss {loss_pct:.1%}",
            ))
    return orders


def rebalance_orders(price_map: dict[str, float]) -> list[Order]:
    """Pick top-N by 6-month momentum. Sell what's out, buy what's in. Equal weight."""
    symbols = universe.symbols()
    scores = market.momentum_scores(symbols, config.MOMENTUM_LOOKBACK_DAYS)
    if not scores:
        return []

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    targets = [s for s, score in ranked[: config.TOP_N] if score > 0]

    current = paper_book.load_positions()
    cash = paper_book.load_cash()
    equity = cash + paper_book.positions_value(price_map)
    per_target_value = equity / max(len(targets), 1) if targets else 0

    orders: list[Order] = []

    # Sells: any current holding not in targets
    for symbol in list(current.keys()):
        if symbol not in targets:
            orders.append(Order(
                action="SELL",
                symbol=symbol,
                quantity=current[symbol]["quantity"],
                reason="rebalance_exit",
            ))

    # Buys: any target not currently held OR underweight
    for symbol in targets:
        price = price_map.get(symbol)
        if not price or price <= 0:
            continue
        current_qty = current.get(symbol, {"quantity": 0})["quantity"]
        current_value = current_qty * price
        deficit = per_target_value - current_value
        if deficit > price:  # at least 1 share to add
            qty_to_add = deficit / price
            orders.append(Order(
                action="BUY",
                symbol=symbol,
                quantity=round(qty_to_add, 4),
                reason=f"rebalance_target_rank_{targets.index(symbol)+1}",
            ))

    return orders


def decide(today: date, price_map: dict[str, float]) -> list[Order]:
    """Run all decision rules in order. Stop-loss always; rebalance once a month."""
    orders = stop_loss_orders(price_map)
    if _is_rebalance_day(today):
        orders.extend(rebalance_orders(price_map))
    return orders
