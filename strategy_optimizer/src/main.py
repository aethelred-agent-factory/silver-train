import yaml
import logging
import threading
import time
import os
import json
import argparse
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Component Imports
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logging_config import setup_logging
from utils.time_utils import TimeUtils
from utils.crypto_utils import CryptoUtils
from utils.statistical_tests import StatisticalTests
from storage.state_manager import StateManager
from storage.artifact_manager import ArtifactManager
from storage.replay_engine import ReplayEngine
from data_bus.event_bus import EventBus
from data_bus.market_data_bus import MarketDataBus
from execution.exchange_adapter import ExchangeAdapter
from execution.paper_adapter import PaperAdapter
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
from governance.kill_switch import KillSwitch
from optimizer.stability_guards import StabilityGuards
from monitoring.dashboard_server import DashboardServer
from monitoring.metrics_collector import MetricsCollector
from backtesting.portfolio_state import PortfolioState
from processors.data_bootstrap_validator import DataBootstrapValidator

# --- Constants ---
MAX_ORDER_SIZE = 10000  # Max order size in USD

def load_all_config(config_dir='strategy_optimizer/config'):
    """
    Loads all YAML configuration files.
    Files are optional - missing files won't crash the system.
    """
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
                logging.info(f"Loaded configuration: {config_key}")
            else:
                logging.warning(f"Configuration file not found: {file_path}")
        except Exception as e:
            logging.error(f"Error loading {file_path}: {e}")
    
    return config

def audit_log(order, simulated_balance):
    """
    Logs order and balance information to a durable audit log.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "order": order,
        "simulated_balance": simulated_balance
    }
    with open("audit_log.jsonl", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def main():
    """
    Initializes all components and starts the main orchestration loops for
    the strategy optimizer and the audit layer.
    """
    # 1. Setup & Configuration
    parser = argparse.ArgumentParser(description="Strategy Optimizer")
    parser.add_argument('--mode', type=str, default='paper', choices=['live', 'paper'],
                        help='Trading mode: live or paper')
    args = parser.parse_args()
    
    setup_logging()
    load_dotenv(dotenv_path='strategy_optimizer/.env')
    config = load_all_config()
    logging.info("Starting the Self-Auditing Strategy Optimizer...")
    logging.info(f"Selected trading mode: {args.mode.upper()}")

    # 2. Initialize all components with correct dependencies
    logging.info("Initializing components...")
    
    # Core Utilities
    state_manager = StateManager(config)
    crypto_utils = CryptoUtils()
    
    # Governance
    kill_switch = KillSwitch(state_manager)
    incident_tracker = IncidentTracker(config, state_manager)
    approval_workflow = ApprovalWorkflow(config, state_manager)
    restriction_enforcer = RestrictionEnforcer(config)
    emergency_manager = EmergencyManager(config, incident_tracker, approval_workflow)
    
    # Data & Execution Layer
    event_bus = EventBus(state_manager)
    if args.mode == 'paper':
        adapter = PaperAdapter(initial_balance=config.get('system_config', {}).get('initial_capital', 100000.0))
        logging.info("Initialized Paper Trading Adapter.")
    else:
        adapter = ExchangeAdapter(config)
        logging.info("Initialized Live Exchange Adapter.")
    
    market_data_bus = MarketDataBus(config)
    
    # Processors
    indicator_engine = IndicatorEngine(config, market_data_bus)
    regime_classifier = RegimeClassifier(config, indicator_engine)
    
    # Backtesting & Performance
    position_manager = PositionManager(config)
    performance_metrics = PerformanceMetrics(config)
    backtest_engine = BacktestEngine(config, None, position_manager, performance_metrics) # SignalGenerator injected later
    
    # Data Validation - ENFORCE REAL DATA
    data_validator = DataBootstrapValidator(config)
    try:
        data_validator.assert_data_available(min_candles=100)
        logging.info("✓ Real market data validated and available")
    except RuntimeError as e:
        logging.critical(str(e))
        raise  # Hard fail - no fake data allowed
    
    # Portfolio State - Track paper trades
    portfolio = PortfolioState(initial_capital=10000.0)
    
    # Optimizer Components
    llm_interface = LLMInterface(config)
    fallback_mode = FallbackMode(config, backtest_engine)
    parameter_memory = ParameterMemory(state_manager)
    signal_generator = SignalGenerator(config, indicator_engine, regime_classifier)
    backtest_engine.signal_generator = signal_generator # Resolve circular dependency
    
    # Stability Guards
    stability_guards = StabilityGuards(config)
    
    strategy_optimizer = StrategyOptimizer(config, regime_classifier, llm_interface, fallback_mode, parameter_memory, event_bus, stability_guards)

    # Audit Layer
    artifact_manager = ArtifactManager(config, crypto_utils)
    t1_checks = T1Checks(config)
    t2_checks = T2Checks(config)
    t3_checks = T3Checks(config)
    audit_causal_validator = AuditCausalChainValidator(config, artifact_manager)
    artifact_store = ArtifactStore(config, artifact_manager, crypto_utils)
    audit_layer = AuditLayer(config, event_bus, t1_checks, t2_checks, t3_checks, audit_causal_validator, artifact_store)
    
    # Monitoring
    metrics_collector = MetricsCollector(state_manager, performance_metrics)
    dashboard_server = DashboardServer(config, state_manager, artifact_manager, incident_tracker, metrics_collector)

    # Execution & Governance
    order_manager = OrderManager(config, adapter, state_manager)
    execution_engine = ExecutionEngine(config, order_manager, state_manager, portfolio)
    
    logging.info("All components initialized.")

    # 3. Start background services in separate threads
    
    # Start AuditLayer listener in a background thread
    audit_thread = threading.Thread(target=audit_layer.listen_for_proposals, daemon=True)
    audit_thread.start()
    logging.info("Audit layer started in a background thread.")
    
    # Start DashboardServer in a background thread
    dashboard_thread = threading.Thread(target=dashboard_server.start, daemon=True)
    dashboard_thread.start()
    logging.info("Dashboard server started in a background thread.")

    # 4. Main orchestration loop (MVTP - Live Trading Flow)
    symbol = 'BTC/USDT'
    current_params = config.get('safe_baseline', {})
    iteration = 0
    
    logging.info(f"\n{'='*80}")
    logging.info(f"STARTING MINIMAL VIABLE TRADING PATH (MVTP)")
    logging.info(f"MODE: {args.mode.upper()} TRADING")
    logging.info(f"{'='*80}\n")
    
    try:
        while True:
            iteration += 1
            logging.info(f"\nITERATION {iteration} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # 0. Global Kill Switch Check
            if kill_switch.is_active():
                logging.critical("System HALTED by Global Kill Switch. Exiting main loop.")
                break

            # 1. Ingest Live Market Data
            logging.info("Step 1: Ingesting live market data...")
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=1)
                candles = market_data_bus.get_candles(symbol, start_date.isoformat(), end_date.isoformat())
            except Exception as e:
                logging.error(f"Data ingestion failed: {e}")
                time.sleep(10)
                continue

            # 2. Generate Signals
            logging.info("Step 2: Generating signals from indicators...")
            signals = signal_generator.generate_signals(symbol, None, None, current_params)
            if signals.empty:
                logging.warning("No signal data produced.")
                time.sleep(10)
                continue

            latest_signal = signals.iloc[-1].to_dict()
            logging.info(f"  - Latest Price: {latest_signal.get('close')}")
            logging.info(f"  - Signal: {latest_signal.get('signal')} (Score: {latest_signal.get('score', 0):.2f})")

            # 3. Size Position
            amount = 0.01  # Placeholder for position manager sizing
            order_size = amount * latest_signal.get('close', 0)
            if order_size > MAX_ORDER_SIZE:
                logging.warning(f"Order size ({order_size}) exceeds MAX_ORDER_SIZE ({MAX_ORDER_SIZE}). Skipping trade.")
                continue

            signal_dict = {
                'symbol': symbol,
                'signal': latest_signal.get('signal'),
                'amount': amount,
                'price': latest_signal.get('close')
            }

            if latest_signal.get('signal') == 1:
                logging.info("✓ BUY SIGNAL DETECTED")

                # 4. Audit & Governance
                proposal = strategy_optimizer.publish_proposal(current_params, 'HOLD')
                
                # Store the proposal artifact so the next audit can find it
                artifact_manager.upload_artifact(
                    artifact_id=proposal.proposal_id,
                    data=proposal.json()
                )

                # Wait for the audit to complete
                verdict = None
                for _ in range(10):
                    verdict = event_bus.subscribe_verdict(proposal.proposal_id)
                    if verdict:
                        break
                    time.sleep(1)

                if not verdict:
                    logging.error(f"Timeout waiting for audit verdict for proposal {proposal.proposal_id}")
                    continue

                logging.info(f"  - Audit Verdict: {verdict.action.type}")

                # 5. Place Trade via Hardened Boundary
                logging.info("Step 5: Routing through hardened execution boundary...")
                success = execution_engine.execute_trade(signal_dict, proposal, verdict)
                if success:
                    logging.info("✓ Trade successfully routed to OrderManager")
                    # Audit Log
                    audit_log(signal_dict, adapter.get_balance())
                else:
                    logging.warning("× Trade blocked by safety gates")
            else:
                logging.info("No signal detected. System monitoring...")

            time.sleep(60)
    
    except RuntimeError as e:
        logging.critical(f"Fatal error: {str(e)}")
        raise
    except KeyboardInterrupt:
        logging.info("\nShutting down Strategy Optimizer (user interrupted)...")
    finally:
        logging.info("Cleaning up resources...")
        logging.info("Strategy Optimizer has been shut down.")

if __name__ == "__main__":
    main()
