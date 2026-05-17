"""Daily runner: fetch prices, decide, execute (paper), snapshot equity.

Run with: python tick.py
Designed to be triggered once per trading day (e.g. by GitHub Actions cron).
"""
import logging
import sys
from datetime import datetime, timezone

import config
import market
import paper_book
import universe
from strategy import decide

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("tick")


def main() -> int:
    now = datetime.now(timezone.utc)
    today = now.date()
    log.info("tick start %s", today)

    symbols = universe.symbols()
    log.info("universe: %d symbols", len(symbols))

    # Get prices for universe + any currently held position (in case it was removed from universe)
    held = list(paper_book.load_positions().keys())
    all_syms = sorted(set(symbols) | set(held))
    prices = market.latest_close(all_syms)
    log.info("prices: %d/%d quoted", len(prices), len(all_syms))

    orders = decide(today, prices)
    log.info("decisions: %d order(s)", len(orders))

    # Execute SELLs first to free cash, then BUYs
    sells = [o for o in orders if o.action == "SELL"]
    buys = [o for o in orders if o.action == "BUY"]

    for o in sells:
        price = prices.get(o.symbol)
        if not price:
            log.warning("SELL %s skipped: no price", o.symbol)
            continue
        paper_book.sell(now, o.symbol, o.quantity, price, o.reason)
        log.info("SELL %s qty=%.4f @ $%.2f  reason=%s", o.symbol, o.quantity, price, o.reason)

    # Recompute available cash after sells
    cash = paper_book.load_cash()
    for o in buys:
        price = prices.get(o.symbol)
        if not price:
            log.warning("BUY %s skipped: no price", o.symbol)
            continue
        cost = o.quantity * price
        if cost > cash:
            # Scale down to fit available cash
            scaled_qty = round(cash / price, 4)
            if scaled_qty <= 0:
                log.warning("BUY %s skipped: cash exhausted", o.symbol)
                continue
            log.info("BUY %s scaled %.4f -> %.4f (cash limit)", o.symbol, o.quantity, scaled_qty)
            o.quantity = scaled_qty
            cost = scaled_qty * price
        paper_book.buy(now, o.symbol, o.quantity, price, o.reason)
        cash -= cost
        log.info("BUY  %s qty=%.4f @ $%.2f  reason=%s", o.symbol, o.quantity, price, o.reason)

    # Snapshot end-of-day equity
    final_cash = paper_book.load_cash()
    pos_value = paper_book.positions_value(prices)
    paper_book.append_equity_snapshot(today, final_cash, pos_value)
    log.info("eod cash=$%.2f positions=$%.2f equity=$%.2f",
             final_cash, pos_value, final_cash + pos_value)

    return 0


if __name__ == "__main__":
    sys.exit(main())
