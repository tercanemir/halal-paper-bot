"""Human-readable portfolio status. Run with: python status.py"""
import csv
import sys
from datetime import datetime, timezone

import config
import market
import paper_book


def fmt_money(v: float) -> str:
    sign = "" if v >= 0 else "-"
    return f"{sign}${abs(v):,.2f}"


def main() -> int:
    positions = paper_book.load_positions()
    cash = paper_book.load_cash()

    price_map: dict[str, float] = {}
    if positions:
        price_map = market.latest_close(list(positions.keys()))

    pos_value = paper_book.positions_value(price_map)
    equity = cash + pos_value
    pnl = equity - config.STARTING_CASH
    pnl_pct = (pnl / config.STARTING_CASH) * 100

    print(f"=== Halal Paper Bot — {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} ===\n")
    print(f"Cash:             {fmt_money(cash):>14}")
    print(f"Positions value:  {fmt_money(pos_value):>14}")
    print(f"Equity:           {fmt_money(equity):>14}")
    print(f"PnL vs start:     {fmt_money(pnl):>14}  ({pnl_pct:+.2f}%)\n")

    if positions:
        print(f"Open positions ({len(positions)}):")
        print(f"  {'Symbol':<8}{'Qty':>10}{'Avg cost':>12}{'Current':>12}{'Value':>14}{'Unreal PnL':>14}")
        for symbol, pos in positions.items():
            qty = pos["quantity"]
            avg = pos["avg_cost"]
            cur = price_map.get(symbol, 0)
            value = qty * cur
            unreal = (cur - avg) * qty
            print(f"  {symbol:<8}{qty:>10.4f}{avg:>12.2f}{cur:>12.2f}{value:>14,.2f}{unreal:>14,.2f}")
        print()

    # Recent trades
    if config.TRADES_FILE.exists():
        print("Recent trades (last 10):")
        with open(config.TRADES_FILE, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for row in rows[-10:]:
            ts = row["timestamp"][:16]
            print(f"  {ts}  {row['action']:<4} {row['symbol']:<6} qty={float(row['quantity']):>10.4f} "
                  f"@ ${float(row['price']):>8.2f}  ({row['reason']})")
    else:
        print("No trades yet.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
