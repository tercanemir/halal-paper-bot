"""Load the halal-compliant stock universe.

Source: a curated CSV at data/halal_us_stocks.csv. Update it manually from
Wahed HLAL ETF holdings or your preferred screener (Zoya, Musaffa, AAOIFI).
"""
import csv
from typing import NamedTuple

import config


class Stock(NamedTuple):
    symbol: str
    name: str
    sector: str


def load_universe() -> list[Stock]:
    out: list[Stock] = []
    with open(config.UNIVERSE_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(Stock(
                symbol=row["symbol"].strip().upper(),
                name=row["name"].strip(),
                sector=row["sector"].strip(),
            ))
    return out


def symbols() -> list[str]:
    return [s.symbol for s in load_universe()]


if __name__ == "__main__":
    stocks = load_universe()
    print(f"Loaded {len(stocks)} halal-compliant symbols:")
    for s in stocks:
        print(f"  {s.symbol:<6} {s.sector:<22} {s.name}")
