#!/usr/bin/env python3
"""
Blessed Dashboard Viewer
Live monitoring dashboard for the strategy optimizer with key metrics and system health
"""
import sys
import os
import json
import time
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from monitoring.blessed_dashboard import BlessedDashboard

def demo_dashboard():
    """Demo the blessed dashboard with sample data"""
    dashboard = BlessedDashboard()
    
    print("\n" * 2)
    dashboard.draw_header()
    
    # Demo iteration
    for iteration in range(1, 4):
        dashboard.print_iteration_banner(iteration)
        
        # Simulate some data
        dashboard.update_state(
            iteration=iteration,
            backtest_trades=50 + (iteration * 15),
            sharpe_ratio=0.85 + (iteration * 0.1),
            current_equity=10000 + (iteration * 500),
            total_pnl=iteration * 500,
            profit_pct=(iteration * 500) / 10000 * 100,
            max_drawdown=5.0 + (iteration * 0.5),
            open_positions=iteration,
            total_trades=iteration * 10,
            regime=['TREND', 'HIGH_VOL', 'RANGE'][iteration % 3],
        )
        
        # Print some signals
        dashboard.print_signal(1, 2.2, 83788.48)
        time.sleep(0.3)
        
        # Print trade execution
        dashboard.print_trade_executed('BUY', 0.067, 83788.48)
        time.sleep(0.3)
        
        # Print portfolio update
        dashboard.print_portfolio_update(
            dashboard.state['current_equity'],
            dashboard.state['total_pnl'],
            dashboard.state['max_drawdown'],
            dashboard.state['open_positions']
        )
        
        print("\n")
        time.sleep(0.5)
    
    # Final dashboard view
    dashboard.render_dashboard()


if __name__ == "__main__":
    demo_dashboard()
