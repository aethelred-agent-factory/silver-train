import os
import sys

import yaml
from dotenv import load_dotenv

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_bus.market_data_bus import MarketDataBus
from src.utils.logging_config import setup_logging


def load_config(config_dir="strategy_optimizer/config"):
    """Loads all YAML configuration files."""
    config = {}
    config_files = [
        os.path.join(config_dir, "system_config.yaml"),
        os.path.join(config_dir, "audit_rules.yaml"),
        os.path.join(config_dir, "regime_config.yaml"),
        os.path.join(config_dir, "parameter_bounds.yaml"),
        os.path.join(config_dir, "safe_baseline.yaml"),
    ]
    for file_path in config_files:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                config_key = os.path.basename(file_path).replace(".yaml", "")
                config[config_key] = yaml.safe_load(f)
        else:
            print(f"Warning: config file not found {file_path}")
    return config


def load_historical_data(
    symbol: str, start_date: str, end_date: str, timeframe: str = "1h"
):
    """
    Loads historical market data for a given symbol and date range.
    """
    setup_logging()
    load_dotenv(dotenv_path="strategy_optimizer/.env")
    print(
        f"Loading historical data for {symbol} from {start_date} to {end_date} ({timeframe})..."
    )

    # Load configuration
    config = load_config()

    # Initialize MarketDataBus
    market_data_bus = MarketDataBus(config)

    # Ingest candles
    market_data_bus.ingest_candles(symbol, start_date, end_date, timeframe)

    print("Historical data loading complete.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Load historical market data.")
    parser.add_argument(
        "--symbol", type=str, required=True, help="Trading pair symbol (e.g., BTC/USDT)"
    )
    parser.add_argument(
        "--start",
        type=str,
        required=True,
        help="Start date (ISO 8601 format, e.g., 2023-01-01T00:00:00Z)",
    )
    parser.add_argument(
        "--end",
        type=str,
        required=True,
        help="End date (ISO 8601 format, e.g., 2023-01-31T23:59:59Z)",
    )
    parser.add_argument(
        "--timeframe", type=str, default="1h", help="Timeframe (e.g., 1m, 5m, 1h, 1d)"
    )

    args = parser.parse_args()

    load_historical_data(args.symbol, args.start, args.end, args.timeframe)
