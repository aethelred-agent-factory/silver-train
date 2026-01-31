High-Level Purpose:
- Goal: Build a production-grade, self-auditing strategy optimizer that proposes parameter updates (LLM-assisted), backtests them on real market data, audits proposals (T1/T2/T3), and executes controlled paper trades with human-in-the-loop governance.

Top-Level Structure:
- src/: core modules (orchestrator, data bus, processors, optimizer, backtesting, audit, execution, governance, monitoring, storage, utils)
- config/: system and domain rules (system_config.yaml, stability_guards.yaml, audit_rules.yaml, etc.)
- data/: market candles, immutable artifacts (JSON + checksums), state DB
- scripts/: operational helpers (init DB, load data, run audits, emergency shutdown)
- tests/: unit & integration tests

Runtime / Orchestration (core flow):
- Loads configs and logging, validates real data availability (hard fail if missing).
- Initializes services: StateManager, EventBus, MarketDataBus, IndicatorEngine, RegimeClassifier, BacktestEngine, LLMInterface, StrategyOptimizer, AuditLayer, ExecutionEngine, Governance modules.
- Main iterative loop (example up to max_iterations):
  1) Run backtest on real data using current params.
  2) Extract metrics (profit, drawdown, win-rate, sharpe, trades).
  3) Classify market regime.
  4) Generate parameter proposal via StrategyOptimizer (LLM + fallback heuristics).
  5) Publish proposal and run AuditLayer (T1/T2/T3 + causal validation).
  6) If allowed, generate signals and simulate paper execution (position sizing, SL) and call ExecutionEngine.
  7) Update params (UPDATE/ROLLBACK/HOLD), portfolio state, and repeat.
- AuditLayer runs a background listener and stores immutable artifacts with checksums.

Key Components & Responsibilities:
- StrategyOptimizer: proposes parameter updates, combines LLM and deterministic fallback.
- LLMInterface: DeepSeek integration (configured in system_config.yaml), with deterministic fallback.
- AuditLayer (T1/T2/T3): independent checks that can block or restrict proposals; uses artifact store and causal chain validator.
- BacktestEngine / PositionManager / PerformanceMetrics: evaluate proposals on real market data.
- SignalGenerator / IndicatorEngine / RegimeClassifier: create signals and determine regime.
- ExecutionEngine / OrderManager: perform (paper) executions via exchange adapters.
- Governance: incident tracking, approval workflows, restriction enforcer, emergency manager.

Important Configs:
- config/system_config.yaml: exchange/timeframe settings, DeepSeek/ccxt API settings, monitoring, optimization flags.
- config/stability_guards.yaml: freeze, rollback, fallback, blacklist, and per-regime targets.
- audit_rules.yaml, parameter_bounds.yaml, safe_baseline.yaml, optimization_config.yaml: audit rules, search bounds, safe defaults, optimizer options.

Safety & Governance:
- Real-data enforcement (no synthetic data allowed).
- Tiered audit with causal artifact validation.
- Stability guards implement freeze/rollback/blacklist policies.
- Human-in-the-loop approval workflows and emergency shutdown options.

How to run (concise):
- Create venv and install deps:
  python3 -m venv venv
  source venv/bin/activate
  pip install -r requirements.txt
- Configure .env from .env.example with API keys.
- Initialize DB: python scripts/initialize_db.py
- (Optional) Load data: python scripts/load_historical_data.py --symbol BTC/USDT --start ... --end ... --timeframe 1h
- Run optimizer: python src/main.py

Next recommended checks:
- Verify .env and API credentials for DeepSeek & exchange.
- Run tests: pytest
- Confirm sufficient history in data/market (>= minimum_trade_history_days in system_config.yaml)
- Review config/audit_rules.yaml to understand blocking vs restriction behavior.
