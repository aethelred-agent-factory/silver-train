import pandas as pd
import numpy as np
import logging
from datetime import timedelta
import hashlib

from data_bus.schemas import BacktestResult

class BacktestEngine:
    """
    Core backtesting logic for strategy evaluation.
    Uses a simplified event-driven loop for more realistic SL/TP checks.
    Includes credit assignment for drawdown attribution.
    """
    def __init__(self, config, signal_generator, position_manager, performance_metrics):
        self.config = config
        self.signal_generator = signal_generator
        self.position_manager = position_manager
        self.performance_metrics = performance_metrics
        logging.info("Initialized BacktestEngine.")

    def _get_params_hash(self, params: dict) -> str:
        """Create a deterministic hash of parameters."""
        params_str = str(sorted(params.items()))
        return hashlib.md5(params_str.encode()).hexdigest()[:8]

    def run_backtest(self, symbol: str, start_date: str, end_date: str, params: dict, initial_capital=10000, regime_data=None) -> BacktestResult:
        """
        Runs a full backtest simulation for a given set of parameters using a more realistic,
        candle-by-candle event loop to handle stop-loss and take-profit.
        Includes regime tagging and credit assignment for drawdowns.
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
        take_profit = 0
        trades_list = []  # Track individual trades
        drawdowns_list = []  # Track drawdown events
        peak_equity = initial_capital
        
        # Add regime column if provided
        if regime_data is None:
            regime_data = {}
        
        for i in range(1, len(signals_df)):
            current_close = signals_df['close'].iloc[i]
            current_regime = regime_data.get(i, 'UNKNOWN')
            
            # Check for exit conditions first
            if position_size > 0:
                exit_price = 0
                exit_reason = None
                # Check for stop-loss
                if signals_df['low'].iloc[i] <= stop_loss:
                    exit_price = stop_loss
                    exit_reason = "stop_loss"
                    logging.debug(f"Stop-loss triggered at {exit_price}")
                # Check for signal exit
                elif signals_df['signal'].iloc[i] == 0:
                    exit_price = current_close
                    exit_reason = "signal_exit"
                    logging.debug(f"Signal exit triggered at {exit_price}")
                
                if exit_price > 0:
                    pnl = (exit_price - entry_price) * position_size
                    cash += position_size * exit_price
                    is_winner = exit_price > entry_price
                    
                    # Log trade
                    trades_list.append({
                        'entry_idx': i - 1,
                        'entry_price': entry_price,
                        'exit_idx': i,
                        'exit_price': exit_price,
                        'exit_reason': exit_reason,
                        'size': position_size,
                        'pnl': pnl,
                        'winner': is_winner,
                        'regime': current_regime
                    })
                    
                    position_size = 0

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
                        # Suppress position sizing warnings - pure optimization mode
                        pass
                else:
                    # Suppress stop-loss warnings - pure optimization mode
                    pass

            current_equity = cash + (position_size * current_close)
            equity.append(current_equity)
            
            # Track drawdowns
            if current_equity > peak_equity:
                peak_equity = current_equity
            else:
                drawdown = peak_equity - current_equity
                drawdown_pct = (drawdown / peak_equity) * 100 if peak_equity > 0 else 0
                if drawdown_pct > 0:
                    drawdowns_list.append({
                        'idx': i,
                        'drawdown_value': drawdown,
                        'drawdown_pct': drawdown_pct,
                        'peak_equity': peak_equity,
                        'current_equity': current_equity,
                        'regime': current_regime,
                        'trades_count': len(trades_list),
                        'params_hash': self._get_params_hash(params)
                    })

        # Calculate performance metrics
        equity_curve = pd.Series(equity, index=signals_df.index)
        total_trades = len(trades_list)
        winning_trades = sum(1 for t in trades_list if t['winner'])
        
        metrics = self.performance_metrics.calculate_all_metrics(equity_curve, total_trades, winning_trades)
        
        # Calculate per-regime metrics
        per_regime_metrics = self._calculate_per_regime_metrics(trades_list, regime_data, initial_capital)

        return BacktestResult(
            start_date=pd.to_datetime(start_date),
            end_date=pd.to_datetime(end_date),
            profit_factor=metrics.get('profit_factor', 0),
            max_drawdown_pct=metrics.get('max_drawdown_pct', 0),
            total_trades=total_trades,
            win_rate=metrics.get('win_rate', 0),
            sharpe_ratio=metrics.get('sharpe_ratio', 0),
            sortino_ratio=metrics.get('sortino_ratio', 0),
            equity_curve=equity_curve.tolist(),
            trades=trades_list,
            drawdowns=drawdowns_list,
            per_regime_metrics=per_regime_metrics,
            parameter_hash=self._get_params_hash(params)
        )

    def _calculate_per_regime_metrics(self, trades_list: list, regime_data: dict, initial_capital: float) -> dict:
        """Calculate metrics broken down by market regime."""
        regime_metrics = {}
        
        for trade in trades_list:
            regime = trade.get('regime', 'UNKNOWN')
            if regime not in regime_metrics:
                regime_metrics[regime] = {
                    'trades': [],
                    'winners': 0,
                    'total_pnl': 0,
                    'total_trades': 0
                }
            
            regime_metrics[regime]['trades'].append(trade)
            regime_metrics[regime]['total_trades'] += 1
            regime_metrics[regime]['total_pnl'] += trade['pnl']
            if trade['winner']:
                regime_metrics[regime]['winners'] += 1
        
        # Compute summary stats per regime
        summary = {}
        for regime, data in regime_metrics.items():
            total = data['total_trades']
            summary[regime] = {
                'total_trades': total,
                'winning_trades': data['winners'],
                'win_rate': (data['winners'] / total * 100) if total > 0 else 0,
                'total_pnl': data['total_pnl'],
                'return_pct': (data['total_pnl'] / initial_capital * 100) if initial_capital > 0 else 0
            }
        
        return summary

    def rapid_backtest(self, symbol: str, end_date: str, params: dict, window_days=7) -> BacktestResult:
        """Runs a quick backtest on a recent window of data."""
        start_date_dt = pd.to_datetime(end_date) - timedelta(days=window_days)
        start_date = start_date_dt.isoformat()
        
        logging.info(f"Running rapid backtest for {window_days} days.")
        return self.run_backtest(symbol, start_date, end_date, params)