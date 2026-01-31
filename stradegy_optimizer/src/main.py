import yaml
import logging
import threading
import time
import os
import json
from datetime import datetime
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
from monitoring.cli_dashboard import CLIDashboard
from backtesting.portfolio_state import PortfolioState
from processors.data_bootstrap_validator import DataBootstrapValidator

def load_all_config(config_dir='config'):
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

def generate_optimization_summary(llm_interface, optimization_history):
    """
    Generate a summary of the optimization run using DeepSeek API.
    Falls back to automatic summary if LLM fails.
    """
    if not optimization_history:
        logging.warning("No optimization history to summarize")
        return None
    
    logging.info("Generating optimization summary with DeepSeek API...")
    
    # Build summary context from history
    initial_profit = optimization_history[0]["metrics"].get("profit", 0)
    final_profit = optimization_history[-1]["metrics"].get("profit", 0)
    best_metrics = max(optimization_history, key=lambda x: x["metrics"].get("profit", 0))["metrics"]
    best_profit = best_metrics.get("profit", 0)
    improvement_trajectory = [h["metrics"].get("profit", 0) for h in optimization_history]
    
    summary_context = {
        "total_iterations": len(optimization_history),
        "initial_metrics": optimization_history[0]["metrics"],
        "final_metrics": optimization_history[-1]["metrics"],
        "best_metrics": best_metrics,
        "improvement_trajectory": improvement_trajectory,
    }
    
    summary_prompt = f"""
You are analyzing the results of a trading strategy optimization run.

OPTIMIZATION SUMMARY:
- Total Iterations: {len(optimization_history)}
- Initial Profit: {initial_profit:.2f}%
- Final Profit: {final_profit:.2f}%
- Best Profit Achieved: {best_profit:.2f}%
- Initial Drawdown: {optimization_history[0]["metrics"].get('max_drawdown_pct', 0):.2f}%
- Final Drawdown: {optimization_history[-1]["metrics"].get('max_drawdown_pct', 0):.2f}%
- Win Rate Improvement: {optimization_history[-1]["metrics"].get('win_rate', 0) - optimization_history[0]["metrics"].get('win_rate', 0):.2f}%

Profit Trajectory: {improvement_trajectory}

Please provide:
1. A concise summary of the optimization results
2. Key improvements and insights
3. Recommendations for next steps
"""
    
    # Try LLM first
    try:
        summary_response = llm_interface.query_llm(summary_prompt, summary_context)
        if summary_response and summary_response.get("reasoning"):
            summary_text = summary_response.get("reasoning")
            logging.info("✓ Summary generated successfully with LLM")
            return summary_text
    except Exception as e:
        logging.error(f"Error querying LLM for summary: {e}")
    
    # Fallback: Generate automatic summary from metrics
    logging.warning("Failed to generate summary with LLM, using automatic fallback")
    profit_improvement = final_profit - initial_profit
    max_profit_improvement = best_profit - initial_profit
    profit_trajectory_str = " → ".join([f"{p:.2f}%" for p in improvement_trajectory[:10]])
    if len(improvement_trajectory) > 10:
        profit_trajectory_str += f" ... (and {len(improvement_trajectory) - 10} more iterations)"
    
    auto_summary = f"""OPTIMIZATION RESULTS SUMMARY

Completed {len(optimization_history)} iterations of strategy parameter optimization.

Performance Trajectory:
- Initial Profit: {initial_profit:.2f}%
- Final Profit: {final_profit:.2f}%
- Best Profit: {best_profit:.2f}%
- Profit Improvement: {profit_improvement:+.2f}%
- Best Improvement: {max_profit_improvement:+.2f}%

Profit Progression: {profit_trajectory_str}

Final Metrics:
- Win Rate: {optimization_history[-1]["metrics"].get('win_rate', 0):.2f}%
- Max Drawdown: {optimization_history[-1]["metrics"].get('max_drawdown_pct', 0):.2f}%
- Total Trades: {optimization_history[-1]["metrics"].get('total_trades', 0)}
- Sharpe Ratio: {optimization_history[-1]["metrics"].get('sharpe_ratio', 0):.2f}

Best Parameters Found:
{json.dumps(best_metrics.get('parameters', {}), indent=2)}

Recommendations:
- Target profit of 25% is ambitious; current best achieved {best_profit:.2f}%
- Consider extending iterations or adjusting parameter bounds for more exploration
- Stable performance achieved with {optimization_history[-1]["metrics"].get('total_trades', 0)} trades
"""
    
    return auto_summary

def save_optimization_report(optimization_history, summary):
    """
    Save optimization history and summary to a report file.
    """
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"logs/optimization_report_{timestamp}.json"
    
    report = {
        "timestamp": timestamp,
        "total_iterations": len(optimization_history),
        "optimization_history": optimization_history,
        "summary": summary
    }
    
    try:
        os.makedirs("logs", exist_ok=True)
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        logging.info(f"✓ Optimization report saved: {report_path}")
        return report_path
    except Exception as e:
        logging.error(f"Error saving report: {e}")
        return None

def main():
    """
    Initializes all components and starts the main orchestration loops for
    the strategy optimizer and the audit layer.
    """
    # 1. Setup & Configuration
    setup_logging()
    load_dotenv()
    config = load_all_config()
    logging.info("Starting the Self-Auditing Strategy Optimizer...")

    # 2. Initialize all components with correct dependencies
    logging.info("Initializing components...")
    
    # Core Utilities
    state_manager = StateManager(config)
    crypto_utils = CryptoUtils()
    
    # Data & Execution Layer
    event_bus = EventBus(state_manager)
    exchange_adapter = ExchangeAdapter(config)
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
    
    # Execution & Governance
    order_manager = OrderManager(config, exchange_adapter, state_manager)
    execution_engine = ExecutionEngine(config, order_manager)
    incident_tracker = IncidentTracker(config, state_manager)
    approval_workflow = ApprovalWorkflow(config, state_manager)
    restriction_enforcer = RestrictionEnforcer(config)
    emergency_manager = EmergencyManager(config, incident_tracker, approval_workflow)
    
    logging.info("All components initialized.")

    # 3. Start background services in separate threads
    
    # Start AuditLayer listener in a background thread
    audit_thread = threading.Thread(target=audit_layer.listen_for_proposals, daemon=True)
    audit_thread.start()
    logging.info("Audit layer started in a background thread.")
    
    # HealthChecker and Dashboard could also be run in threads if desired
    # health_checker = HealthChecker(...)
    # health_thread = threading.Thread(target=health_checker.start_periodic_checks, daemon=True)
    # health_thread.start()

    # 4. Main orchestration loop with REAL DATA
    symbol = 'BTC/USDT'
    start_date = '2025-06-01T00:00:00Z'
    end_date = '2026-01-31T23:59:59Z'
    
    iteration = 0
    max_iterations = 50  # Run for up to 50 iterations or until conditions are met
    current_params = config.get('safe_baseline', {})
    optimization_history = []  # Track optimization progress
    
    # Optimization stopping conditions
    profit_target = config.get('optimization_config', {}).get('optimization_targets', {}).get('profit_target', 10.0)
    win_rate_target = config.get('optimization_config', {}).get('optimization_targets', {}).get('win_rate_target', 40.0)
    max_drawdown_target = config.get('optimization_config', {}).get('optimization_targets', {}).get('max_drawdown_target', 20.0)
    stability_window = config.get('optimization_config', {}).get('optimization_targets', {}).get('stability_window', 10)
    
    logging.info(f"\n{'='*80}")
    logging.info(f"OPTIMIZATION TARGETS:")
    logging.info(f"  - Profit Target: {profit_target}%")
    logging.info(f"  - Win Rate Target: {win_rate_target}%")
    logging.info(f"  - Max Drawdown Target: {max_drawdown_target}%")
    logging.info(f"  - Stability Window: {stability_window} iterations")
    logging.info(f"  - Max Iterations: {max_iterations}")
    logging.info(f"{'='*80}\n")
    
    try:
        while iteration < max_iterations:
            iteration += 1
            logging.info(f"\n{'='*80}")
            logging.info(f"ITERATION {iteration}/{max_iterations} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"{'='*80}")
            
            # ============================================================
            # STEP 1: RUN REAL BACKTEST ON REAL DATA
            # ============================================================
            logging.info("Step 1: Running backtest on real market data...")
            backtest_result = backtest_engine.run_backtest(symbol, start_date, end_date, current_params)
            
            if backtest_result is None:
                logging.error("Backtest returned None - likely no signals generated from real data")
                logging.error("Checking data availability...")
                try:
                    data_validator.assert_data_available()
                except RuntimeError as e:
                    logging.critical(str(e))
                    raise
                logging.warning("Skipping iteration due to backtest failure")
                time.sleep(5)
                continue
            
            # ============================================================
            # STEP 2: EXTRACT REAL METRICS FROM BACKTEST
            # ============================================================
            logging.info("Step 2: Extracting metrics from real backtest results...")
            current_metrics = {
                'profit': backtest_result.profit_factor * 100 - 100,
                'max_drawdown_pct': backtest_result.max_drawdown_pct,
                'win_rate': backtest_result.win_rate,
                'sharpe_ratio': backtest_result.sharpe_ratio,
                'total_trades': backtest_result.total_trades,
                'profit_factor': backtest_result.profit_factor,
                'parameters': current_params.copy(),
                'regime_confidence': 0.85  # Placeholder - would be from regime classifier
            }
            
            # Store in history for summary
            optimization_history.append({
                'iteration': iteration,
                'timestamp': datetime.now().isoformat(),
                'metrics': current_metrics,
            })
            
            logging.info(f"  - Profit: {current_metrics['profit']:.2f}%")
            logging.info(f"  - Max Drawdown: {current_metrics['max_drawdown_pct']:.2f}%")
            logging.info(f"  - Win Rate: {current_metrics['win_rate']:.2f}%")
            logging.info(f"  - Total Trades: {current_metrics['total_trades']}")
            logging.info(f"  - Sharpe Ratio: {current_metrics['sharpe_ratio']:.2f}")
            
            # ============================================================
            # CHECK STOPPING CONDITIONS
            # ============================================================
            conditions_met = (
                current_metrics['profit'] >= profit_target and
                current_metrics['win_rate'] >= win_rate_target and
                current_metrics['max_drawdown_pct'] <= max_drawdown_target
            )
            
            if conditions_met and len(optimization_history) >= stability_window:
                logging.info("\n" + "="*80)
                logging.info("✓ OPTIMIZATION TARGETS MET!")
                logging.info("="*80)
                logging.info(f"  - Profit: {current_metrics['profit']:.2f}% (target: {profit_target}%)")
                logging.info(f"  - Win Rate: {current_metrics['win_rate']:.2f}% (target: {win_rate_target}%)")
                logging.info(f"  - Max Drawdown: {current_metrics['max_drawdown_pct']:.2f}% (target: {max_drawdown_target}%)")
                logging.info("="*80 + "\n")
                break  # Exit loop - conditions met
            
            # ============================================================
            # STEP 3: CLASSIFY REGIME FROM REAL DATA
            # ============================================================
            logging.info("Step 3: Classifying market regime from real data...")
            regime, confidence = regime_classifier.classify_latest(symbol, start_date, end_date)
            logging.info(f"  - Regime: {regime}, Confidence: {confidence:.2f}%")
            
            # ============================================================
            # STEP 4: GENERATE PROPOSAL FROM REAL BACKTEST METRICS
            # ============================================================
            logging.info("Step 4: Generating parameter proposal from real metrics...")
            proposed_params, action, reasoning = strategy_optimizer.propose_parameters(
                iteration, current_metrics, regime, {}, symbol, end_date
            )
            logging.info(f"  - Action: {action}")
            logging.info(f"  - Reasoning: {reasoning}")
            logging.info(f"  - Proposed Params: {proposed_params}")
            
            # Publish proposal
            proposal = strategy_optimizer.publish_proposal(proposed_params, action)
            
            # ============================================================
            # STEP 5: RUN AUDIT ON PROPOSAL
            # ============================================================
            logging.info("Step 5: Running audit on proposal...")
            verdict = audit_layer.audit_proposal(proposal)
            logging.info(f"  - Verdict: {verdict.action.type}")
            
            if verdict.tiered_findings:
                for finding in verdict.tiered_findings:
                    logging.info(f"    {finding.tier}: {finding.code} - {finding.explanation}")
            
            # ============================================================
            # STEP 6: SKIP TRADE EXECUTION - PURE OPTIMIZATION ONLY
            # ============================================================
            logging.info("Step 6: Skipping trade execution (pure optimization mode)")
            logging.info("  - No paper trades, no position tracking")
            
            # Update parameter for next iteration
            if action == 'UPDATE':
                current_params = proposed_params
                logging.info(f"Updated parameters for next iteration")
            elif action == 'ROLLBACK':
                logging.info(f"Rolling back to previous parameters")
            else:
                logging.info(f"Holding current parameters")
            
            logging.info(f"{'='*80}\n")
            
            time.sleep(5)  # Small delay between iterations
    
    except RuntimeError as e:
        logging.critical(f"Fatal error: {str(e)}")
        raise
    except KeyboardInterrupt:
        logging.info("\nShutting down Strategy Optimizer (user interrupted)...")
    finally:
        # No positions to close - pure optimization mode
        logging.info("Cleaning up resources...")
        
        # ============================================================
        # GENERATE OPTIMIZATION SUMMARY WITH DEEPSEEK API
        # ============================================================
        logging.info("\n" + "="*80)
        logging.info("GENERATING OPTIMIZATION SUMMARY")
        logging.info("="*80)
        
        summary = generate_optimization_summary(llm_interface, optimization_history)
        if summary:
            logging.info("\nOPTIMIZATION SUMMARY:")
            logging.info("-" * 80)
            logging.info(summary)
            logging.info("-" * 80)
        
        # Save report
        report_path = save_optimization_report(optimization_history, summary)
        if report_path:
            logging.info(f"Full optimization report saved to: {report_path}")
        
        logging.info("="*80)
        logging.info("Strategy Optimizer has been shut down.")
        logging.info("="*80)

if __name__ == "__main__":
    main()