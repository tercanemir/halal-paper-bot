"""Project configuration. All knobs live here."""
import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
UNIVERSE_FILE = DATA_DIR / "halal_us_stocks.csv"
TRADES_FILE = DATA_DIR / "trades.csv"
POSITIONS_FILE = DATA_DIR / "positions.json"
EQUITY_FILE = DATA_DIR / "equity_history.csv"

# Paper portfolio
STARTING_CASH = float(os.getenv("STARTING_CASH", "10000"))

# Strategy parameters
TOP_N = int(os.getenv("TOP_N", "5"))                    # how many stocks to hold
MOMENTUM_LOOKBACK_DAYS = int(os.getenv("MOMENTUM_LOOKBACK_DAYS", "126"))  # ~6 months
REBALANCE_DAY_OF_MONTH = int(os.getenv("REBALANCE_DAY_OF_MONTH", "1"))    # rebalance on first trading day of month
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.15"))                 # 15% stop loss
