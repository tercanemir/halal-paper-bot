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

# Strategy parameters (Clenow "Stocks on the Move", chapter 7)
TOP_N = int(os.getenv("TOP_N", "5"))                                      # number of positions
MOMENTUM_LOOKBACK_DAYS = int(os.getenv("MOMENTUM_LOOKBACK_DAYS", "90"))   # book uses 90 trading days
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.15"))                 # safety net only; main exit is below 100-day MA
