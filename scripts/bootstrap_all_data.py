#!/usr/bin/env python3
"""
Bootstrap Data Loader
Convenience script to load all required market data at once.
"""
import logging
import os
import subprocess
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Required symbols
SYMBOLS = ["BTC/USDT", "ETH/USDT", "SOL/USDT", "AVAX/USDT"]

# Data range
START_DATE = "2025-06-01T00:00:00Z"
END_DATE = "2026-01-31T23:59:59Z"
TIMEFRAME = "1h"


def bootstrap_all_data():
    """
    Loads all required market data from exchange.
    """
    logger.info("=" * 80)
    logger.info("BOOTSTRAP: Loading Real Market Data")
    logger.info("=" * 80)
    logger.info(f"Symbols: {', '.join(SYMBOLS)}")
    logger.info(f"Date Range: {START_DATE} to {END_DATE}")
    logger.info(f"Timeframe: {TIMEFRAME}")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)

    script_path = os.path.join(os.path.dirname(__file__), "load_historical_data.py")

    for i, symbol in enumerate(SYMBOLS, 1):
        logger.info(f"\n[{i}/{len(SYMBOLS)}] Loading {symbol}...")

        cmd = [
            "python",
            script_path,
            "--symbol",
            symbol,
            "--start",
            START_DATE,
            "--end",
            END_DATE,
            "--timeframe",
            TIMEFRAME,
        ]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(result.stdout)
            if result.returncode == 0:
                logger.info(f"✓ Successfully loaded {symbol}")
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to load {symbol}")
            logger.error(e.stderr)
            logger.warning("Continuing with next symbol...")
        except Exception as e:
            logger.error(f"Error loading {symbol}: {e}")
            logger.warning("Continuing with next symbol...")

    logger.info("\n" + "=" * 80)
    logger.info("BOOTSTRAP COMPLETE")
    logger.info("=" * 80)
    logger.info("Verifying data...")
    logger.info("\nTo verify data was loaded:")
    logger.info("  ls -la data/market/")
    logger.info("\nYou can now run:")
    logger.info("  python src/main.py")
    logger.info("=" * 80)


if __name__ == "__main__":
    try:
        bootstrap_all_data()
    except KeyboardInterrupt:
        logger.info("\nBootstrap interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Bootstrap failed: {e}")
        sys.exit(1)
