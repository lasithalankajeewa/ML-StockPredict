"""Central configuration for SmartStock AI paths and dataset filenames."""

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

MODEL_DIR = PROJECT_ROOT / "models"
REPORT_DIR = PROJECT_ROOT / "reports"
FIGURES_DIR = REPORT_DIR / "figures"

CALENDAR_FILENAME = "calendar.csv"
SALES_FILENAME = "sales_train_evaluation.csv"
PRICES_FILENAME = "sell_prices.csv"

# Use one store while developing and validating memory-intensive transformations.
DEVELOPMENT_STORE_ID = "CA_1"
