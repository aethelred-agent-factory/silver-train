import pandas as pd
import numpy as np
import logging
from datetime import timedelta

from data_bus.schemas import BacktestResult

class BacktestEngine:
    """
    Core backtesting logic for strategy evaluation.
    Uses a simplified event-driven loop for more realistic SL/TP checks.
    """
    def __init__(self, config, signal_generator, position_manager, performance_metrics):
        self.config = config
        self.signal_generator = signal_generator
        self.position_manager = position_manager
        self.performance_metrics = performance_metrics
        logging.info("Initialized BacktestEngine.")

    def run_backtest(self, symbol: str, start_date: str, end_date: str, params: dict, initial_capital=10000) -> BacktestResult:
        """
        Runs a full backtest simulation for a given set of parameters using a more realistic,
        candle-by-candle event loop to handle stop-loss and take-profit.
        """
        logging.info(f"Running backtest for {symbol} from {start_date} to {end_date}")

        signals_df = self.signal_generator.generate_signals(symbol, start_date, end_date, params)
        if signals_df.empty:
            logging.warning("No signals generated, cannot run backtest.")
            return None

        # Event-driven simulation
        equity = [initial_capital]
        cash = initial_capital
        position_size = 0
        entry_price = 0
        stop_loss = 0
        take_profit = 0 # Can be added later
        trades = 0
        winning_trades = 0

        for i in range(1, len(signals_df)):
            current_close = signals_df['close'].iloc[i]
            
            # Check for exit conditions first
            if position_size > 0:
                exit_price = 0
                # Check for stop-loss
                if signals_df['low'].iloc[i] <= stop_loss:
                    exit_price = stop_loss
                    logging.debug(f"Stop-loss triggered at {exit_price}")
                # Check for signal exit
                elif signals_df['signal'].iloc[i] == 0:
                    exit_price = current_close
                    logging.debug(f"Signal exit triggered at {exit_price}")
                
                if exit_price > 0:
                    cash += position_size * exit_price
                    if exit_price > entry_price:
                        winning_trades += 1
                    position_size = 0
                    trades += 1

            # Check for entry conditions
            if signals_df['signal'].iloc[i] == 1 and position_size == 0:
                entry_price = current_close
                sl_price = self.position_manager.place_stop_loss(
                    entry_price=entry_price,
                    atr=signals_df['atr'].iloc[i],
                    multiplier=params.get('stop_multiplier', 2.0)
                )
                if entry_price > sl_price:
                    size = self.position_manager.calculate_position_size(
                        capital=cash,
                        risk_pct=params.get('risk_pct', 1.0),
                        entry_price=entry_price,
                        stop_loss_price=sl_price
                    )
                    if size * entry_price <= cash:
                        position_size = size
                        stop_loss = sl_price
                        cash -= position_size * entry_price
                        logging.debug(f"Entry triggered at {entry_price}, size {position_size}, SL {stop_loss}")
                    else:
                        logging.warning("Insufficient cash for entry.")
                else:
                    logging.warning("Stop-loss price was not below entry, skipping trade.")

            current_equity = cash + (position_size * current_close)
            equity.append(current_equity)

        # 3. Calculate performance metrics
        equity_curve = pd.Series(equity, index=signals_df.index)
        metrics = self.performance_metrics.calculate_all_metrics(equity_curve, trades, winning_trades)

        return BacktestResult(
            start_date=pd.to_datetime(start_date),
            end_date=pd.to_datetime(end_date),
            profit_factor=metrics.get('profit_factor', 0),
            max_drawdown_pct=metrics.get('max_drawdown_pct', 0),
            total_trades=trades,
            win_rate=metrics.get('win_rate', 0),
            sharpe_ratio=metrics.get('sharpe_ratio', 0),
            sortino_ratio=metrics.get('sortino_ratio', 0),
            equity_curve=equity_curve.tolist()
        )

    def rapid_backtest(self, symbol: str, end_date: str, params: dict, window_days=7) -> BacktestResult:
        """Runs a quick backtest on a recent window of data."""
        start_date_dt = pd.to_datetime(end_date) - timedelta(days=window_days)
        start_date = start_date_dt.isoformat()
        
        logging.info(f"Running rapid backtest for {window_days} days.")
        return self.run_backtest(symbol, start_date, end_date, params)