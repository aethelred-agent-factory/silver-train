#!/usr/bin/env python3
"""
Walk-Forward Validation Script
Tests Iteration 3 parameters across 100 random 90-day windows
"""

import sys

sys.path.insert(0, "src")

import logging
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import yaml

logging.basicConfig(level=logging.WARNING)


def load_config():
    """Load all configuration files."""
    config = {}
    for fname in os.listdir("config"):
        if fname.endswith(".yaml"):
            with open(f"config/{fname}") as f:
                key = fname.replace(".yaml", "")
                config[key] = yaml.safe_load(f)
    return config


def get_available_date_range(config):
    """Get available data range from market data and load full dataset."""
    from data_bus.market_data_bus import MarketDataBus

    mdb = MarketDataBus(config)

    # Load BTC/USDT data to find min/max dates
    data = mdb.get_candles("BTC/USDT", "2025-06-01T00:00:00Z", "2026-02-01T00:00:00Z")
    if data.empty:
        print("ERROR: No historical data available")
        return None, None

    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True)

    return data


def generate_rolling_windows(data, window_candles=504, num_windows=20):
    """Generate rolling windows from the available data (504 candles = 21 days at 1h bars).

    With limited data (1000 candles = ~42 days), we create overlapping windows
    of 504 candles each with 100-candle stride.
    """
    windows = []
    max_windows_possible = max(1, (len(data) - window_candles) // 100 + 1)
    actual_windows = min(num_windows, max_windows_possible)

    for i in range(actual_windows):
        start_idx = i * 100
        end_idx = start_idx + window_candles

        if end_idx > len(data):
            break

        start_date = data["timestamp"].iloc[start_idx]
        end_date = data["timestamp"].iloc[end_idx - 1]

        windows.append((start_date, end_date))

    return windows


def run_validation(config, data, windows, params):
    """Run backtests on all windows."""
    from backtesting.backtest_engine import BacktestEngine
    from backtesting.performance_metrics import PerformanceMetrics
    from backtesting.position_manager import PositionManager
    from data_bus.market_data_bus import MarketDataBus
    from optimizer.signal_generator import SignalGenerator
    from processors.indicator_engine import IndicatorEngine
    from processors.regime_classifier import RegimeClassifier

    # Initialize components
    mdb = MarketDataBus(config)
    ie = IndicatorEngine(config, mdb)
    rc = RegimeClassifier(config, ie)
    sg = SignalGenerator(config, ie, rc)
    pm = PositionManager(config)
    perf = PerformanceMetrics(config)

    engine = BacktestEngine(config, sg, pm, perf)

    results = []

    print(f"\nRunning {len(windows)} walk-forward backtests...")
    print(f"Parameters: min_score={params['min_score']}, risk_pct={params['risk_pct']}")
    print("-" * 100)

    for idx, (start_dt, end_dt) in enumerate(windows, 1):
        start_iso = start_dt.isoformat()
        end_iso = end_dt.isoformat()

        try:
            result = engine.run_backtest(
                symbol="BTC/USDT",
                start_date=start_iso,
                end_date=end_iso,
                params=params,
                initial_capital=10000,
            )

            if result is None:
                print(f"  Window {idx:2d}: FAILED (no signals)")
                continue

            # Extract metrics
            profit_pct = (
                ((result.profit_factor - 1) * 100) if result.profit_factor > 0 else 0
            )

            # Calculate profit from equity curve
            if result.equity_curve and len(result.equity_curve) > 1:
                final_equity = result.equity_curve[-1]
                profit_pct = ((final_equity - 10000) / 10000) * 100

            window_result = {
                "start_date": start_dt.strftime("%Y-%m-%d %H:%M"),
                "end_date": end_dt.strftime("%Y-%m-%d %H:%M"),
                "profit_pct": profit_pct,
                "win_rate_pct": result.win_rate if result.win_rate else 0,
                "max_drawdown_pct": result.max_drawdown_pct
                if result.max_drawdown_pct
                else 0,
                "num_trades": result.total_trades if result.total_trades else 0,
                "sharpe_ratio": result.sharpe_ratio if result.sharpe_ratio else 0,
            }

            results.append(window_result)

            status = "✓" if profit_pct > 0 else "✗"
            print(
                f"  Window {idx:2d}: {window_result['start_date']} → {window_result['end_date']:19s} | "
                f"Profit: {profit_pct:+7.2f}% | Win: {window_result['win_rate_pct']:6.1f}% | "
                f"DD: {window_result['max_drawdown_pct']:7.2f}% | Trades: {window_result['num_trades']:2d} {status}"
            )

        except Exception as e:
            print(f"  Window {idx:2d}: ERROR - {str(e)[:50]}")
            continue

    return results


def calculate_summary(results):
    """Calculate summary statistics."""
    if not results:
        print("\nERROR: No valid results to summarize")
        return None

    df = pd.DataFrame(results)

    profitable_count = (df["profit_pct"] > 0).sum()
    profitable_pct = (profitable_count / len(df)) * 100

    summary = {
        "total_windows": len(df),
        "profitable_windows": profitable_count,
        "profitable_pct": profitable_pct,
        "median_profit": df["profit_pct"].median(),
        "mean_profit": df["profit_pct"].mean(),
        "min_profit": df["profit_pct"].min(),
        "max_profit": df["profit_pct"].max(),
        "profit_std": df["profit_pct"].std(),
        "median_win_rate": df["win_rate_pct"].median(),
        "mean_win_rate": df["win_rate_pct"].mean(),
        "worst_drawdown": df["max_drawdown_pct"].min(),
        "median_drawdown": df["max_drawdown_pct"].median(),
        "mean_drawdown": df["max_drawdown_pct"].mean(),
        "median_trades": df["num_trades"].median(),
        "mean_trades": df["num_trades"].mean(),
        "median_sharpe": df["sharpe_ratio"].median(),
    }

    return summary, df


def print_summary(summary):
    """Print summary statistics to console."""
    if summary is None:
        return

    summary_stats, _ = summary

    print("\n" + "=" * 80)
    print("WALK-FORWARD VALIDATION SUMMARY")
    print("=" * 80)
    print(f"\nTest Configuration:")
    print(f"  Windows tested: {summary_stats['total_windows']}")
    print(f"  Window size: 21 days (504 hourly candles)")
    print(f"  Iteration 3 Parameters: min_score=1.6, risk_pct=1.95")
    print(f"\nProfitability Statistics:")
    print(
        f"  Profitable windows: {summary_stats['profitable_windows']}/{summary_stats['total_windows']} "
        f"({summary_stats['profitable_pct']:.1f}%)"
    )
    print(f"  Median profit: {summary_stats['median_profit']:+.2f}%")
    print(f"  Mean profit: {summary_stats['mean_profit']:+.2f}%")
    print(
        f"  Profit range: {summary_stats['min_profit']:+.2f}% to {summary_stats['max_profit']:+.2f}%"
    )
    print(f"  Profit std dev: {summary_stats['profit_std']:.2f}%")
    print(f"\nWin Rate Statistics:")
    print(f"  Median win rate: {summary_stats['median_win_rate']:.1f}%")
    print(f"  Mean win rate: {summary_stats['mean_win_rate']:.1f}%")
    print(f"\nRisk Statistics:")
    print(f"  Worst drawdown: {summary_stats['worst_drawdown']:.2f}%")
    print(f"  Median drawdown: {summary_stats['median_drawdown']:.2f}%")
    print(f"  Mean drawdown: {summary_stats['mean_drawdown']:.2f}%")
    print(f"\nTrade Statistics:")
    print(f"  Median trades per window: {summary_stats['median_trades']:.0f}")
    print(f"  Mean trades per window: {summary_stats['mean_trades']:.1f}")
    print(f"  Median Sharpe ratio: {summary_stats['median_sharpe']:.2f}")
    print("\n" + "=" * 80)


def main():
    """Main execution."""
    print("=" * 80)
    print("WALK-FORWARD VALIDATION - Iteration 3 Parameters")
    print("=" * 80)

    # Load config
    config = load_config()

    # Iteration 3 best parameters
    params = {
        "min_score": 1.6,
        "rsi_oversold": 30,
        "rsi_overbought": 70,
        "stop_multiplier": 2.0,
        "target_multiplier": 2.0,
        "risk_pct": 1.95,
    }

    # Get date range
    print("\nScanning historical data...")
    data = get_available_date_range(config)
    if data is None:
        return

    min_date = data["timestamp"].min()
    max_date = data["timestamp"].max()
    print(
        f"Available data: {min_date.strftime('%Y-%m-%d %H:%M')} to {max_date.strftime('%Y-%m-%d %H:%M')}"
    )
    print(
        f"Total data points: {len(data)} candles ({len(data) / 24:.1f} days at 1h bars)"
    )

    # Generate windows
    print("\nGenerating rolling 21-day windows...")
    windows = generate_rolling_windows(data, window_candles=504, num_windows=20)
    print(f"Generated {len(windows)} windows")

    # Run validation
    results = run_validation(config, data, windows, params)

    # Calculate summary
    if results:
        summary = calculate_summary(results)
        print_summary(summary)

        # Save to CSV
        df_results = pd.DataFrame(results)
        csv_path = "validation_results.csv"
        df_results.to_csv(csv_path, index=False)
        print(f"\nResults saved to {csv_path}")

        # Also save summary stats
        summary_stats, _ = summary
        summary_df = pd.DataFrame([summary_stats])
        summary_path = "validation_summary.csv"
        summary_df.to_csv(summary_path, index=False)
        print(f"Summary saved to {summary_path}")
    else:
        print("\nERROR: No valid results to process")


if __name__ == "__main__":
    main()
