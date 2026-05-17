"""Simulated portfolio: cash, positions, trade log, equity history.

Every order goes through here. No real broker contact. All state lives in
plain CSV/JSON files so a human can audit them or git-diff over time.
"""
import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import config


def _ensure_file(path: Path, header: Optional[str] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists() and header is not None:
        path.write_text(header + "\n", encoding="utf-8")


def load_positions() -> dict[str, dict]:
    if not config.POSITIONS_FILE.exists():
        return {}
    return json.loads(config.POSITIONS_FILE.read_text(encoding="utf-8"))


def save_positions(positions: dict[str, dict]) -> None:
    config.POSITIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    config.POSITIONS_FILE.write_text(
        json.dumps(positions, indent=2, sort_keys=True), encoding="utf-8"
    )


def load_cash() -> float:
    """Cash is derived: starting cash minus net cost of all trades so far."""
    if not config.TRADES_FILE.exists():
        return config.STARTING_CASH
    net = 0.0
    with open(config.TRADES_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            qty = float(row["quantity"])
            price = float(row["price"])
            if row["action"] == "BUY":
                net += qty * price
            elif row["action"] == "SELL":
                net -= qty * price
    return config.STARTING_CASH - net


def append_trade(
    when: datetime,
    symbol: str,
    action: str,
    quantity: float,
    price: float,
    reason: str,
) -> None:
    assert action in ("BUY", "SELL")
    _ensure_file(
        config.TRADES_FILE,
        header="timestamp,symbol,action,quantity,price,value,reason",
    )
    with open(config.TRADES_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            when.isoformat(timespec="seconds"),
            symbol,
            action,
            f"{quantity:.6f}",
            f"{price:.4f}",
            f"{quantity * price:.2f}",
            reason,
        ])


def append_equity_snapshot(when: date, cash: float, positions_value: float) -> None:
    _ensure_file(
        config.EQUITY_FILE,
        header="date,cash,positions_value,equity",
    )
    with open(config.EQUITY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            when.isoformat(),
            f"{cash:.2f}",
            f"{positions_value:.2f}",
            f"{cash + positions_value:.2f}",
        ])


def buy(
    when: datetime,
    symbol: str,
    quantity: float,
    price: float,
    reason: str = "",
) -> None:
    positions = load_positions()
    pos = positions.get(symbol, {"quantity": 0.0, "avg_cost": 0.0, "first_bought": when.isoformat()})
    old_qty = pos["quantity"]
    new_qty = old_qty + quantity
    pos["avg_cost"] = (pos["avg_cost"] * old_qty + price * quantity) / new_qty if new_qty > 0 else price
    pos["quantity"] = new_qty
    if "first_bought" not in pos:
        pos["first_bought"] = when.isoformat()
    positions[symbol] = pos
    save_positions(positions)
    append_trade(when, symbol, "BUY", quantity, price, reason)


def sell(
    when: datetime,
    symbol: str,
    quantity: float,
    price: float,
    reason: str = "",
) -> None:
    positions = load_positions()
    if symbol not in positions:
        raise ValueError(f"no position in {symbol} to sell")
    pos = positions[symbol]
    if quantity > pos["quantity"] + 1e-9:
        raise ValueError(f"selling {quantity} {symbol} but only hold {pos['quantity']}")
    pos["quantity"] -= quantity
    if pos["quantity"] < 1e-9:
        del positions[symbol]
    else:
        positions[symbol] = pos
    save_positions(positions)
    append_trade(when, symbol, "SELL", quantity, price, reason)


def positions_value(price_map: dict[str, float]) -> float:
    total = 0.0
    for symbol, pos in load_positions().items():
        price = price_map.get(symbol)
        if price is not None:
            total += pos["quantity"] * price
    return total
