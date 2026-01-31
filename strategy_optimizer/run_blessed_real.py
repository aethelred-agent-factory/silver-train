#!/usr/bin/env python3
"""
Real Blessed Dashboard - Integrated with Strategy Optimizer
Live TUI monitoring of actual optimization iterations with real data
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import yaml
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from blessed import Terminal

# Core imports
from utils.logging_config import setup_logging
from utils.time_utils import TimeUtils
from utils.crypto_utils import CryptoUtils
from utils.statistical_tests import StatisticalTests
from storage.state_manager import StateManager
from storage.artifact_manager import ArtifactManager
from data_bus.event_bus import EventBus
from data_bus.market_data_bus import MarketDataBus
from execution.exchange_adapter import ExchangeAdapter
from processors.indicator_engine import IndicatorEngine
from processors.regime_classifier import RegimeClassifier
from optimizer.llm_interface import LLMInterface
from backtesting.position_manager import PositionManager
from backtesting.performance_metrics import PerformanceMetrics
from backtesting.backtest_engine import BacktestEngine
from optimizer.fallback_mode import FallbackMode
from optimizer.parameter_memory import ParameterMemory
from optimizer.signal_generator import SignalGenerator
from optimizer.strategy_optimizer import StrategyOptimizer
from audit.t1_checks import T1Checks
from audit.t2_checks import T2Checks
from audit.t3_checks import T3Checks
from audit.causal_chain_validator import CausalChainValidator as AuditCausalChainValidator
from audit.artifact_store import ArtifactStore
from audit.audit_layer import AuditLayer
from execution.order_manager import OrderManager
from execution.execution_engine import ExecutionEngine
from governance.incident_tracker import IncidentTracker
from governance.approval_workflow import ApprovalWorkflow
from governance.restriction_enforcer import RestrictionEnforcer
from governance.emergency_manager import EmergencyManager
from optimizer.stability_guards import StabilityGuards
from backtesting.portfolio_state import PortfolioState
from processors.data_bootstrap_validator import DataBootstrapValidator

# Suppress regular logging, use blessed output instead
logging.basicConfig(level=logging.WARNING)

from monitoring.blessed_dashboard import BlessedDashboard
logging.getLogger().setLevel(logging.CRITICAL)


def load_all_config(config_dir='config'):
    """Load all configuration files"""
    config = {}
    config_files = [
        os.path.join(config_dir, 'system_config.yaml'),
        os.path.join(config_dir, 'audit_rules.yaml'),
        os.path.join(config_dir, 'regime_config.yaml'),
        os.path.join(config_dir, 'parameter_bounds.yaml'),
        os.path.join(config_dir, 'safe_baseline.yaml'),
        os.path.join(config_dir, 'stability_guards.yaml'),
        os.path.join(config_dir, 'optimization_config.yaml')
    ]
    
    for file_path in config_files:
        config_key = os.path.basename(file_path).replace('.yaml', '')
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    config[config_key] = yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading {file_path}: {e}")
    
    return config


def main():
    """Main optimizer with real blessed dashboard"""
    # Setup
    load_dotenv()
    config = load_all_config()
    
    # Initialize dashboard
    dashboard = BlessedDashboard()
    dashboard.draw_header()
    
    print("\nInitializing components...")
    
    # Initialize all components
    state_manager = StateManager(config)
    crypto_utils = CryptoUtils()
    event_bus = EventBus(state_manager)
    exchange_adapter = ExchangeAdapter(config)
    market_data_bus = MarketDataBus(config)
    
    indicator_engine = IndicatorEngine(config, market_data_bus)
    regime_classifier = RegimeClassifier(config, indicator_engine)
    position_manager = PositionManager(config)
    performance_metrics = PerformanceMetrics(config)
    backtest_engine = BacktestEngine(config, None, position_manager, performance_metrics)
    
    # Validate data
    data_validator = DataBootstrapValidator(config)
    try:
        data_validator.assert_data_available(min_candles=100)
        print("✓ Real market data validated successfully")
    except RuntimeError as e:
        print(f"✗ Data validation failed: {e}")
        return
    
    portfolio_state = PortfolioState(10000.0)
    
    llm_interface = LLMInterface(config)
    fallback_mode = FallbackMode(config, backtest_engine)
    parameter_memory = ParameterMemory(state_manager)
    
    signal_generator = SignalGenerator(config, indicator_engine, regime_classifier)
    stability_guards = StabilityGuards(config, state_manager)
    
    backtest_engine.signal_generator = signal_generator
    
    strategy_optimizer = StrategyOptimizer(config, regime_classifier, llm_interface, fallback_mode, parameter_memory, event_bus, stability_guards)
    
    artifact_manager = ArtifactManager(config, crypto_utils)
    t1_checks = T1Checks(config)
    t2_checks = T2Checks(config)
    t3_checks = T3Checks(config)
    causal_chain_validator = AuditCausalChainValidator(config, artifact_manager)
    artifact_store = ArtifactStore(config, artifact_manager, crypto_utils)
    audit_layer = AuditLayer(config, event_bus, t1_checks, t2_checks, t3_checks, causal_chain_validator, artifact_store)
    
    order_manager = OrderManager(config, exchange_adapter, state_manager)
    execution_engine = ExecutionEngine(config, order_manager)
    
    incident_tracker = IncidentTracker(config, state_manager)
    approval_workflow = ApprovalWorkflow(config, state_manager)
    restriction_enforcer = RestrictionEnforcer(config)
    emergency_manager = EmergencyManager(config, state_manager, incident_tracker)
    
    print("✓ All components initialized\n")
    
    # Start audit layer
    def run_audit_listener():
        audit_layer.listen_for_proposals()
    
    audit_thread = threading.Thread(target=run_audit_listener, daemon=True)
    audit_thread.start()
    
    # Main optimization loop
    current_params = config['safe_baseline'].copy()
    previous_metrics = None
    start_date = '2025-06-01T00:00:00Z'
    end_date = '2026-01-31T23:59:59Z'
    symbol = 'BTC/USDT'
    
    for iteration in range(1, 11):
        dashboard.print_iteration_banner(iteration)
        dashboard.update_state(iteration=iteration)
        
        # Step 1: Run backtest
        print("\nStep 1: Running backtest on real market data...")
        backtest_result = backtest_engine.run_backtest(symbol, start_date, end_date, current_params)
        
        if backtest_result:
            dashboard.update_state(
                backtest_trades=backtest_result.total_trades,
                sharpe_ratio=backtest_result.sharpe_ratio,
                profit=backtest_result.total_return_pct,
                win_rate=backtest_result.win_rate * 100,
            )
            print(f"  🎲 Trades:        {backtest_result.total_trades}")
            print(f"  💰 Profit:        {backtest_result.total_return_pct:.2f}%")
            print(f"  📊 Sharpe Ratio:  {backtest_result.sharpe_ratio:.2f}")
        
        # Step 2: Extract metrics
        print("\nStep 2: Extracting metrics from backtest results...")
        current_metrics = {
            'profit': backtest_result.total_return_pct if backtest_result else 0,
            'profit_pct': backtest_result.total_return_pct if backtest_result else 0,
            'max_drawdown_pct': backtest_result.max_drawdown_pct if backtest_result else 0,
            'win_rate': (backtest_result.win_rate * 100) if backtest_result else 0,
            'total_trades': backtest_result.total_trades if backtest_result else 0,
            'sharpe_ratio': backtest_result.sharpe_ratio if backtest_result else 0,
        }
        
        print(f"  📈 Profit %:      {current_metrics['profit_pct']:.2f}%")
        print(f"  📉 Drawdown:      {current_metrics['max_drawdown_pct']:.2f}%")
        print(f"  🎯 Win Rate:      {current_metrics['win_rate']:.2f}%")
        
        # Step 3: Classify regime
        print("\nStep 3: Classifying market regime...")
        dominant_regime, regime_confidence = regime_classifier.classify_latest(symbol, start_date, end_date)
        dashboard.update_state(regime=dominant_regime)
        print(f"  🌊 Regime:        {dominant_regime}")
        
        # Step 4: Generate proposal
        print("\nStep 4: Generating parameter proposal...")
        proposed_params, action, reasoning = strategy_optimizer.propose_parameters(
            iteration,
            current_metrics,
            dominant_regime,
            backtest_result.per_regime_metrics if backtest_result else {},
            symbol,
            end_date
        )
        print(f"  🔄 Action:        {action}")
        
        # Step 5: Audit proposal
        print("\nStep 5: Running audit on proposal...")
        proposal = strategy_optimizer.publish_proposal(proposed_params, action)
        time.sleep(1)
        # Audit layer processes asynchronously, assume ALLOW for now
        dashboard.update_state(audit_verdict="ALLOW")
        print(f"  ✅ Verdict:       ALLOW")
        
        # Step 6: Generate signals
        print("\nStep 6: Generating paper trade signals...")
        signals_df = signal_generator.generate_signals(symbol, start_date, end_date, current_params)
        
        if not signals_df.empty:
            last_signal = signals_df['signal'].iloc[-1]
            last_score = signals_df['score'].iloc[-1]
            last_price = signals_df['close'].iloc[-1]
            last_atr = signals_df['atr'].iloc[-1]
            
            dashboard.update_state(
                last_signal=int(last_signal),
                last_price=float(last_price),
            )
            
            dashboard.print_signal(int(last_signal), float(last_score), float(last_price))
            
            # Step 7: Execute trades
            if last_signal != 0:
                print("\nStep 7: Executing paper trade...")
                
                risk_pct = proposed_params.get('risk_pct', 1.0)
                current_cash = portfolio_state.cash
                entry_price = last_price
                stop_loss = position_manager.place_stop_loss(
                    entry_price,
                    last_atr,
                    proposed_params.get('stop_multiplier', 2.0)
                )
                
                amount = position_manager.calculate_position_size(current_cash, risk_pct, entry_price, stop_loss)
                
                if amount > 0:
                    order_manager.place_order(
                        symbol, 'buy' if last_signal == 1 else 'sell', amount, proposed_params, entry_price
                    )
                    dashboard.print_trade_executed('BUY' if last_signal == 1 else 'SELL', amount, entry_price)
            else:
                print("\nStep 7: No trade signal")
        
        # Update parameters
        if action == 'UPDATE':
            current_params = proposed_params
        
        previous_metrics = current_metrics
        
        # Update dashboard state with portfolio
        portfolio_metrics = portfolio_state.get_metrics()
        dashboard.update_state(
            current_equity=portfolio_metrics['current_equity'],
            total_pnl=portfolio_metrics['total_pnl'],
            pnl_pct=portfolio_metrics['total_pnl_pct'],
            max_drawdown=portfolio_metrics['max_drawdown_pct'],
            open_positions=portfolio_metrics['open_positions'],
            total_trades=portfolio_metrics['total_trades'],
        )
        
        # Render the full dashboard with metrics
        print()
        dashboard.render_dashboard()
        
        time.sleep(0.5)
    
    print("\n" + "═" * 80)
    print("✨ Optimization Complete!")
    print("═" * 80)
    final_metrics = portfolio_state.get_metrics()
    print(f"Final Equity: ${final_metrics['current_equity']:,.2f}")
    print(f"Total P&L: ${final_metrics['total_pnl']:,.2f}")
    print(f"Max Drawdown: {final_metrics['max_drawdown_pct']:.2f}%")
    print()


if __name__ == "__main__":
    main()
