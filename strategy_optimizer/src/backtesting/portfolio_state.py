import logging
from datetime import datetime, timezone
from typing import Optional, Dict

class PortfolioState:
    """
    Tracks paper trading portfolio state across iterations.
    Maintains equity, positions, and drawdown from peak.
    """
    def __init__(self, initial_capital: float = 10000.0):
        self.initial_capital = initial_capital
        self.current_equity = initial_capital
        self.cash = initial_capital
        self.peak_equity = initial_capital
        self.max_drawdown_pct = 0.0
        
        # Position tracking
        self.positions = {}  # symbol -> {quantity, entry_price, entry_time}
        
        # Trade history
        self.trade_history = []  # [{entry_price, exit_price, quantity, pnl, ...}]
        
        # Equity history for metrics
        self.equity_curve = [initial_capital]
        self.equity_timestamps = [datetime.now(timezone.utc)]
        
        logging.info(f"Initialized PortfolioState with capital: {initial_capital}")

    def enter_position(self, symbol: str, quantity: float, entry_price: float, timestamp: Optional[datetime] = None):
        """
        Records entry into a position (paper trade).
        """
        if quantity <= 0:
            logging.warning(f"Cannot enter position with non-positive quantity: {quantity}")
            return False
        
        cost = quantity * entry_price
        if cost > self.cash:
            logging.warning(f"Insufficient cash. Cost: {cost}, Available: {self.cash}")
            return False
        
        self.positions[symbol] = {
            'quantity': quantity,
            'entry_price': entry_price,
            'entry_time': timestamp or datetime.now(timezone.utc),
            'entry_value': cost
        }
        self.cash -= cost
        
        logging.info(f"Entered {symbol}: {quantity} units at {entry_price}, cash remaining: {self.cash}")
        return True

    def exit_position(self, symbol: str, exit_price: float, timestamp: Optional[datetime] = None) -> Optional[Dict]:
        """
        Exits a position and records the trade.
        Returns trade details or None if position doesn't exist.
        """
        if symbol not in self.positions:
            logging.warning(f"No position to exit for {symbol}")
            return None
        
        pos = self.positions[symbol]
        quantity = pos['quantity']
        entry_price = pos['entry_price']
        entry_value = pos['entry_value']
        exit_value = quantity * exit_price
        pnl = exit_value - entry_value
        pnl_pct = (pnl / entry_value * 100) if entry_value > 0 else 0
        
        trade = {
            'symbol': symbol,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'quantity': quantity,
            'entry_value': entry_value,
            'exit_value': exit_value,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'entry_time': pos['entry_time'],
            'exit_time': timestamp or datetime.now(timezone.utc),
            'is_winner': pnl > 0
        }
        
        self.trade_history.append(trade)
        self.cash += exit_value
        del self.positions[symbol]
        
        logging.info(f"Exited {symbol}: {quantity} units at {exit_price}, PnL: {pnl:.2f} ({pnl_pct:.2f}%)")
        return trade

    def update_equity(self, current_prices: Dict[str, float], timestamp: Optional[datetime] = None):
        """
        Updates current equity based on mark-to-market prices for open positions.
        """
        unrealized_pnl = 0.0
        
        for symbol, pos in self.positions.items():
            if symbol in current_prices:
                current_value = pos['quantity'] * current_prices[symbol]
                unrealized_pnl += current_value - pos['entry_value']
        
        self.current_equity = self.cash + unrealized_pnl
        
        # Track peak and drawdown
        if self.current_equity > self.peak_equity:
            self.peak_equity = self.current_equity
        
        current_drawdown = self.peak_equity - self.current_equity
        self.max_drawdown_pct = (current_drawdown / self.peak_equity * 100) if self.peak_equity > 0 else 0
        
        # Record equity curve
        self.equity_curve.append(self.current_equity)
        self.equity_timestamps.append(timestamp or datetime.now(timezone.utc))
        
        return self.current_equity

    def get_metrics(self) -> Dict:
        """
        Returns current portfolio metrics.
        """
        total_trades = len(self.trade_history)
        winning_trades = sum(1 for t in self.trade_history if t['is_winner'])
        losing_trades = total_trades - winning_trades
        
        total_pnl = sum(t['pnl'] for t in self.trade_history)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        avg_win = sum(t['pnl'] for t in self.trade_history if t['is_winner']) / winning_trades if winning_trades > 0 else 0
        avg_loss = abs(sum(t['pnl'] for t in self.trade_history if not t['is_winner']) / losing_trades) if losing_trades > 0 else 0
        profit_factor = avg_win / avg_loss if avg_loss > 0 else (2.0 if avg_win > 0 else 1.0)
        
        return {
            'current_equity': self.current_equity,
            'initial_capital': self.initial_capital,
            'total_pnl': total_pnl,
            'total_pnl_pct': (total_pnl / self.initial_capital * 100),
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'max_drawdown_pct': self.max_drawdown_pct,
            'peak_equity': self.peak_equity,
            'open_positions': len(self.positions)
        }

    def get_open_position(self, symbol: str) -> Optional[Dict]:
        """Returns details of open position or None."""
        return self.positions.get(symbol)

    def close_all_positions(self, current_prices: Dict[str, float], timestamp: Optional[datetime] = None):
        """
        Closes all open positions at current prices.
        Used at end of backtest or emergency shutdown.
        """
        closed_trades = []
        for symbol in list(self.positions.keys()):
            if symbol in current_prices:
                trade = self.exit_position(symbol, current_prices[symbol], timestamp)
                if trade:
                    closed_trades.append(trade)
        
        return closed_trades
