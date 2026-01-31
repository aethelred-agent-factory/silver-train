# Architecture: Self-Auditing Strategy Optimizer

This document serves as the architectural blueprint for the Self-Auditing Strategy Optimizer, outlining its modular design, key components, and interactions. It formalizes the concepts detailed in the project's `SPECIFICATIONS.txt` into a concrete file and module structure.

---

## **File Architecture**

```
strategy-optimizer/
│
├── README.md
├── requirements.txt
├── setup.py
├── .env.example
├── docker-compose.yml
│
├── config/
│   ├── __init__.py
│   ├── system_config.yaml           # System-wide settings (data sources, paths, thresholds)
│   ├── audit_rules.yaml              # T1/T2/T3 rule definitions
│   ├── regime_config.yaml            # Regime classification thresholds
│   ├── parameter_bounds.yaml         # Min/max for all strategy parameters
│   └── safe_baseline.yaml            # Fallback parameters for emergency mode
│
├── data/
│   ├── market/                       # Raw market data (OHLCV candles)
│   │   └── .gitkeep
│   ├── artifacts/                    # Immutable audit artifacts (JSON + checksums)
│   │   └── .gitkeep
│   └── state/                        # SQLite WAL database
│       └── optimizer_state.db
│
├── logs/
│   ├── system.log
│   ├── audit.log
│   ├── execution.log
│   └── emergency.log
│
├── src/
│   │
│   ├── __init__.py
│   │
│   ├── main.py                       # Orchestrator - coordinates all components
│   │
│   ├── data_bus/
│   │   ├── __init__.py
│   │   ├── market_data_bus.py        # Canonical OHLCV ingestion & storage
│   │   ├── event_bus.py              # Event stream for optimizer→audit communication
│   │   └── schemas.py                # Pydantic models for all data structures
│   │
│   ├── processors/
│   │   ├── __init__.py
│   │   ├── indicator_engine.py       # Compute RSI, ATR, ADX, percentiles (causal)
│   │   ├── regime_classifier.py      # TREND/HIGH_VOL/RANGE classification
│   │   ├── data_validator.py         # Missing data detection & imputation
│   │   └── causal_validator.py       # Ensure all computations are timestamp-causal
│   │
│   ├── optimizer/
│   │   ├── __init__.py
│   │   ├── strategy_optimizer.py     # Main optimizer logic (parameter proposals)
│   │   ├── signal_generator.py       # Scoring system & trade signals
│   │   ├── llm_interface.py          # DeepSeek API integration
│   │   ├── fallback_mode.py          # Deterministic gradient estimation
│   │   └── parameter_memory.py       # Track tested parameter combinations
│   │
│   ├── backtesting/
│   │   ├── __init__.py
│   │   ├── backtest_engine.py        # Core backtesting logic
│   │   ├── position_manager.py       # Position sizing, SL/TP placement
│   │   ├── performance_metrics.py    # Profit, drawdown, win rate, Sharpe, etc.
│   │   └── walk_forward.py           # Walk-forward validation implementation
│   │
│   ├── audit/
│   │   ├── __init__.py
│   │   ├── audit_layer.py            # Main audit coordinator
│   │   ├── t1_checks.py              # Tier 1: Structural integrity checks
│   │   ├── t2_checks.py              # Tier 2: Reasoning flaw detection
│   │   ├── t3_checks.py              # Tier 3: Informational gap detection
│   │   ├── causal_chain_validator.py # Verify provenance & causality
│   │   └── artifact_store.py         # Immutable audit artifact storage
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── execution_engine.py       # Safe interface to exchange API
│   │   ├── order_manager.py          # Order placement & fill tracking
│   │   └── exchange_adapter.py       # CCXT wrapper with rate limiting
│   │
│   ├── governance/
│   │   ├── __init__.py
│   │   ├── emergency_manager.py      # Emergency protocol execution
│   │   ├── approval_workflow.py      # Human-in-the-loop approval system
│   │   ├── restriction_enforcer.py   # Apply T2-based restrictions
│   │   └── incident_tracker.py       # Track T1 incidents & resolutions
│   │
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── dashboard_server.py       # Flask/FastAPI dashboard
│   │   ├── alerting.py               # Email/Telegram alerts
│   │   ├── metrics_collector.py      # Prometheus-style metrics
│   │   └── health_checker.py         # System health monitoring
│   │
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── state_manager.py          # SQLite WAL interface
│   │   ├── artifact_manager.py       # Object storage (S3/local) with checksums
│   │   └── replay_engine.py          # Reproduce decisions from artifacts
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logging_config.py         # Structured logging setup
│       ├── crypto_utils.py           # Checksums, hashing
│       ├── time_utils.py             # Timezone-aware datetime handling
│       └── statistical_tests.py      # Bootstrap CI, hypothesis tests
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_data_bus/
│   ├── test_processors/
│   ├── test_optimizer/
│   ├── test_backtesting/
│   ├── test_audit/
│   ├── test_execution/
│   └── test_integration/
│
├── scripts/
│   ├── initialize_db.py              # Create SQLite schema
│   ├── load_historical_data.py       # Bootstrap market data
│   ├── run_audit_only.py             # Audit existing proposals without execution
│   ├── emergency_shutdown.py         # Manual emergency stop
│   └── generate_reports.py           # Export audit reports, backtest results
│
└── docs/
    ├── architecture.md               # This document
    ├── api_reference.md              # Component APIs
    ├── deployment_guide.md           # Production deployment steps
    └── troubleshooting.md            # Common issues & solutions
```

---

## **File Descriptions & Relationships**

### **Root Level**

| File | Purpose | Relations |
|------|---------|-----------|
| `README.md` | Project overview, quick start | References all docs/ |
| `requirements.txt` | Python dependencies | Used by setup.py, Docker |
| `setup.py` | Package installation config | Uses requirements.txt |
| `.env.example` | Environment variable template | Copied to .env for secrets |
| `docker-compose.yml` | Container orchestration | Mounts config/, data/, logs/ |

---

### **config/** - Configuration Layer

All YAML files are loaded by `src/main.py` at startup and passed to relevant components.

| File | Purpose | Used By |
|------|---------|---------|
| `system_config.yaml` | Paths, API keys, thresholds | All components |
| `audit_rules.yaml` | T1/T2/T3 rule definitions | `audit/` modules |
| `regime_config.yaml` | ADX/ATR thresholds for regimes | `processors/regime_classifier.py` |
| `parameter_bounds.yaml` | Min/max for all params | `optimizer/strategy_optimizer.py`, `audit/t1_checks.py` |
| `safe_baseline.yaml` | Emergency fallback params | `optimizer/fallback_mode.py`, `governance/emergency_manager.py` |

---

### **data/** - Persistent Storage

| Directory | Purpose | Managed By | Format |
|-----------|---------|------------|--------|
| `market/` | Raw OHLCV candles | `data_bus/market_data_bus.py` | Parquet files (symbol/YYYY-MM-DD.parquet) |
| `artifacts/` | Audit artifacts | `audit/artifact_store.py` | JSON with CRC32 checksums |
| `state/` | Optimizer state | `storage/state_manager.py` | SQLite WAL database |

---

### **src/main.py** - The Orchestrator

**Purpose:** Coordinates all components in the optimization loop.

**Orchestration Flow:**
```python
1. Load configs (config/*.yaml)
2. Initialize components:
   - MarketDataBus (data_bus/market_data_bus.py)
   - IndicatorEngine (processors/indicator_engine.py)
   - RegimeClassifier (processors/regime_classifier.py)
   - StrategyOptimizer (optimizer/strategy_optimizer.py)
   - AuditLayer (audit/audit_layer.py)
   - ExecutionEngine (execution/execution_engine.py)
   - EmergencyManager (governance/emergency_manager.py)
   
3. Main loop:
   a. Fetch market data → MarketDataBus
   b. Compute indicators → IndicatorEngine
   c. Classify regime → RegimeClassifier
   d. Generate proposal → StrategyOptimizer
   e. Audit proposal → AuditLayer
   f. If ALLOW → ExecutionEngine
   g. If T1 → EmergencyManager
   h. Log everything → monitoring/metrics_collector.py
```

**Relations:** Imports and coordinates ALL components.

---

### **src/data_bus/** - Data Infrastructure

#### `market_data_bus.py`
- **Purpose:** Canonical, immutable OHLCV storage
- **Key Functions:**
  - `ingest_candles(symbol, start, end)` - Fetch from exchange via CCXT
  - `get_candles(symbol, start, end)` - Retrieve for backtesting
  - `mark_missing(symbol, timestamp)` - Track data gaps
- **Relations:**
  - **Reads from:** Exchange API (via `execution/exchange_adapter.py`)
  - **Writes to:** `data/market/` (Parquet files)
  - **Used by:** `processors/indicator_engine.py`, `backtesting/backtest_engine.py`

#### `event_bus.py`
- **Purpose:** Optimizer→Audit communication stream
- **Key Functions:**
  - `publish_proposal(proposal_dict)` - Optimizer publishes
  - `subscribe_audit()` - Audit layer consumes
- **Relations:**
  - **Publishers:** `optimizer/strategy_optimizer.py`
  - **Subscribers:** `audit/audit_layer.py`
  - **Stores events in:** `storage/state_manager.py` (SQLite)

#### `schemas.py`
- **Purpose:** Pydantic models for all data structures
- **Models:**
  - `OptimizerProposal`, `AuditVerdict`, `Candle`, `BacktestResult`, etc.
- **Relations:** Imported by **EVERY** module for type safety

---

### **src/processors/** - Data Processing

#### `indicator_engine.py`
- **Purpose:** Compute RSI, ATR, ADX, percentiles (causal)
- **Key Functions:**
  - `compute_rsi(candles, period=14)` - Uses only past data
  - `compute_atr_percentile(candles, window=90)` - Rolling percentile
- **Relations:**
  - **Reads from:** `data_bus/market_data_bus.py`
  - **Validated by:** `processors/causal_validator.py`
  - **Used by:** `optimizer/signal_generator.py`, `processors/regime_classifier.py`

#### `regime_classifier.py`
- **Purpose:** TREND/HIGH_VOL/RANGE classification
- **Key Functions:**
  - `classify_regime(indicators)` - Returns regime label + confidence
- **Relations:**
  - **Reads:** Indicators from `indicator_engine.py`
  - **Config:** `config/regime_config.yaml`
  - **Used by:** `optimizer/strategy_optimizer.py`, `audit/t2_checks.py`

#### `data_validator.py`
- **Purpose:** Detect missing candles, apply imputation
- **Key Functions:**
  - `detect_gaps(candles)` - Find missing timestamps
  - `impute_missing(candles)` - Forward-fill + log
- **Relations:**
  - **Reads from:** `data_bus/market_data_bus.py`
  - **Logs to:** `audit/artifact_store.py` (imputation events)
  - **Triggers:** T1 if >10% missing (via `audit/t1_checks.py`)

#### `causal_validator.py`
- **Purpose:** Ensure all computations use only past data
- **Key Functions:**
  - `validate_timestamp_causality(computation, candle_timestamp)`
- **Relations:**
  - **Called by:** `indicator_engine.py`, `audit/causal_chain_validator.py`
  - **Flags:** T1_CausalViolation if future data detected

---

### **src/optimizer/** - Strategy Optimization

#### `strategy_optimizer.py`
- **Purpose:** Main optimization logic, parameter proposals
- **Key Functions:**
  - `propose_parameters(current_metrics, regime, history)` - Returns JSON proposal
  - `apply_frozen_epoch()` - Enforce minimum iterations before change
- **Relations:**
  - **Calls:** `llm_interface.py` (DeepSeek) or `fallback_mode.py`
  - **Reads:** `parameter_memory.py` (avoid repeating failures)
  - **Config:** `config/parameter_bounds.yaml`
  - **Publishes to:** `data_bus/event_bus.py`

#### `signal_generator.py`
- **Purpose:** Scoring system & trade signal generation
- **Key Functions:**
  - `calculate_signal_score(indicators, params)` - Base + Bonus scoring
- **Relations:**
  - **Reads:** Indicators from `processors/indicator_engine.py`
  - **Used by:** `backtesting/backtest_engine.py`

#### `llm_interface.py`
- **Purpose:** DeepSeek API integration
- **Key Functions:**
  - `query_llm(prompt, context)` - Send proposal request
  - `parse_json_response(response)` - Extract params
- **Relations:**
  - **Called by:** `strategy_optimizer.py`
  - **Fallback to:** `fallback_mode.py` on API failure
  - **Config:** API keys from `.env`

#### `fallback_mode.py`
- **Purpose:** Deterministic gradient estimation when LLM fails
- **Key Functions:**
  - `perturb_parameters(current_params)` - ±5% delta variants
  - `score_variant(variant)` - profit - 2*drawdown
- **Relations:**
  - **Called by:** `strategy_optimizer.py` (on LLM failure)
  - **Uses:** `backtesting/backtest_engine.py` for rapid simulation
  - **Safe baseline from:** `config/safe_baseline.yaml`

#### `parameter_memory.py`
- **Purpose:** Track tested combinations, prevent repetition
- **Key Functions:**
  - `log_tested(params, regime, result)` - Store in SQLite
  - `has_been_tested(params, regime)` - Check before proposing
- **Relations:**
  - **Storage:** `storage/state_manager.py` (SQLite)
  - **Used by:** `strategy_optimizer.py`

---

### **src/backtesting/** - Backtesting Engine

#### `backtest_engine.py`
- **Purpose:** Core backtesting simulation
- **Key Functions:**
  - `run_backtest(params, start, end)` - Full simulation
  - `rapid_backtest(params, window=7_days)` - Quick validation
- **Relations:**
  - **Reads:** Candles from `data_bus/market_data_bus.py`
  - **Uses:** `signal_generator.py` for entries, `position_manager.py` for execution
  - **Returns:** `BacktestResult` to `optimizer/strategy_optimizer.py`

#### `position_manager.py`
- **Purpose:** Position sizing, SL/TP placement
- **Key Functions:**
  - `calculate_position_size(capital, risk_pct, atr, stop_mult)`
  - `place_stop_loss(entry, atr, multiplier)`
- **Relations:**
  - **Used by:** `backtest_engine.py`
  - **Config:** Bounds from `config/parameter_bounds.yaml`

#### `performance_metrics.py`
- **Purpose:** Calculate profit, drawdown, win rate, Sharpe, Sortino
- **Key Functions:**
  - `calculate_metrics(equity_curve)` - All performance stats
  - `bootstrap_confidence_interval(metric, samples=2000)` - Statistical CI
- **Relations:**
  - **Used by:** `backtest_engine.py`, `audit/t2_checks.py`
  - **Statistical tests from:** `utils/statistical_tests.py`

#### `walk_forward.py`
- **Purpose:** Walk-forward validation implementation
- **Key Functions:**
  - `split_datasets(data, cal_pct=60, val_pct=20, test_pct=20)`
  - `rolling_walk_forward(data, window, step)`
- **Relations:**
  - **Uses:** `backtest_engine.py` for each window
  - **Verified by:** `audit/t2_checks.py` (non-overlapping check)

---

### **src/audit/** - Audit Layer

#### `audit_layer.py`
- **Purpose:** Main audit coordinator
- **Key Functions:**
  - `audit_proposal(proposal)` - Run all T1/T2/T3 checks
  - `generate_verdict(findings)` - ALLOW / RESTRICT / BLOCK
- **Relations:**
  - **Subscribes to:** `data_bus/event_bus.py`
  - **Calls:** `t1_checks.py`, `t2_checks.py`, `t3_checks.py`, `causal_chain_validator.py`
  - **Stores results in:** `artifact_store.py`
  - **Notifies:** `governance/restriction_enforcer.py` on T2, `governance/emergency_manager.py` on T1

#### `t1_checks.py`
- **Purpose:** Structural integrity (critical failures)
- **Checks:**
  - `check_contradiction()` - Regime vs ATR_percentile
  - `check_bounds()` - Parameters within limits
  - `check_circularity()` - No same-cycle data references
- **Relations:**
  - **Config:** `config/audit_rules.yaml`
  - **Triggers:** `governance/emergency_manager.py` on failure

#### `t2_checks.py`
- **Purpose:** Reasoning flaws (confidence degradation)
- **Checks:**
  - `check_insufficient_sample()` - N_trades >= N_min
  - `check_fuzzy_boundary()` - ADX near threshold
  - `check_causal_gap()` - Missing causal chain
- **Relations:**
  - **Uses:** `utils/statistical_tests.py` for sample size validation
  - **Triggers:** `governance/restriction_enforcer.py`

#### `t3_checks.py`
- **Purpose:** Informational gaps (remediation requests)
- **Checks:**
  - `check_config_gaps()` - Missing required config keys
  - `check_ambiguous_logs()` - NLP check for vague terms
- **Relations:**
  - **Reads:** `config/system_config.yaml`
  - **Logs:** Remediation requests to `logs/audit.log`

#### `causal_chain_validator.py`
- **Purpose:** Verify provenance & timestamp causality
- **Key Functions:**
  - `validate_causal_chain(chain, proposal_timestamp)` - All nodes causal
- **Relations:**
  - **Used by:** `audit_layer.py`
  - **Validates against:** `processors/causal_validator.py` rules

#### `artifact_store.py`
- **Purpose:** Immutable audit artifact storage
- **Key Functions:**
  - `store_artifact(audit_verdict)` - Write JSON + checksum
  - `retrieve_artifact(audit_id)` - Read with verification
- **Relations:**
  - **Writes to:** `data/artifacts/` (object storage)
  - **Checksums via:** `utils/crypto_utils.py`
  - **Used by:** `storage/replay_engine.py` for reproduction

---

### **src/execution/** - Trade Execution

#### `execution_engine.py`
- **Purpose:** Safe interface to exchange API
- **Key Functions:**
  - `execute_trade(signal, params)` - Place orders with validation
  - `check_execution_safety(proposal, audit_verdict)` - Pre-execution check
- **Relations:**
  - **Calls:** `order_manager.py` → `exchange_adapter.py`
  - **Blocks if:** `audit_layer.py` returns BLOCK verdict
  - **Logs to:** `logs/execution.log`

#### `order_manager.py`
- **Purpose:** Order placement & fill tracking
- **Key Functions:**
  - `place_order(symbol, side, size, sl, tp)` - Send to exchange
  - `track_fill(order_id)` - Monitor order status
- **Relations:**
  - **Uses:** `exchange_adapter.py` (CCXT wrapper)
  - **Updates:** `storage/state_manager.py` (order state)

#### `exchange_adapter.py`
- **Purpose:** CCXT wrapper with rate limiting
- **Key Functions:**
  - `fetch_ohlcv(symbol, timeframe)` - Rate-limited data fetch
  - `create_order(symbol, type, side, amount)` - Rate-limited order placement
- **Relations:**
  - **Used by:** `data_bus/market_data_bus.py`, `order_manager.py`
  - **Config:** API keys from `.env`, rate limits from `config/system_config.yaml`

---

### **src/governance/** - Human Oversight

#### `emergency_manager.py`
- **Purpose:** Emergency protocol execution
- **Key Functions:**
  - `trigger_emergency(incident)` - Halt system, create ticket
  - `revert_to_safe_baseline()` - Load fallback params
- **Relations:**
  - **Triggered by:** `audit/t1_checks.py`
  - **Loads:** `config/safe_baseline.yaml`
  - **Creates:** Incident in `incident_tracker.py`
  - **Alerts:** `monitoring/alerting.py` (urgent notifications)

#### `approval_workflow.py`
- **Purpose:** Human-in-the-loop approval system
- **Key Functions:**
  - `request_approval(emergency_ticket)` - Send to approvers
  - `check_approval_status(ticket_id)` - Wait for 2 signatures
- **Relations:**
  - **Called by:** `emergency_manager.py`
  - **Stores tickets in:** `storage/state_manager.py`
  - **Timeout → revert via:** `emergency_manager.py`

#### `restriction_enforcer.py`
- **Purpose:** Apply T2-based restrictions
- **Key Functions:**
  - `apply_restrictions(verdict)` - Reduce position size, etc.
  - `lift_restrictions(verdict)` - Remove when cleared
- **Relations:**
  - **Triggered by:** `audit/t2_checks.py`
  - **Modifies:** Execution parameters in `execution_engine.py`

#### `incident_tracker.py`
- **Purpose:** Track T1 incidents & resolutions
- **Key Functions:**
  - `log_incident(type, details, timestamp)` - Store in DB
  - `mark_resolved(incident_id, resolution)` - Close incident
- **Relations:**
  - **Storage:** `storage/state_manager.py` (SQLite incidents table)
  - **Displayed in:** `monitoring/dashboard_server.py`

---

### **src/monitoring/** - Observability

#### `dashboard_server.py`
- **Purpose:** Flask/FastAPI web dashboard
- **Endpoints:**
  - `/metrics` - Current equity, drawdown, flags
  - `/incidents` - T1/T2/T3 event history
  - `/artifacts` - Browse audit artifacts
- **Relations:**
  - **Reads from:** `storage/state_manager.py`, `data/artifacts/`
  - **Port:** 5000 (configurable in `config/system_config.yaml`)

#### `alerting.py`
- **Purpose:** Email/Telegram alerts
- **Key Functions:**
  - `send_urgent_alert(message)` - T1 events
  - `send_daily_summary()` - T2/T3 trends
- **Relations:**
  - **Triggered by:** `emergency_manager.py`, scheduled cron
  - **Config:** Alert channels in `.env`

#### `metrics_collector.py`
- **Purpose:** Prometheus-style metrics collection
- **Metrics:**
  - `optimizer_proposals_total`, `audit_t1_failures_total`, `equity_current`, etc.
- **Relations:**
  - **Called by:** ALL components (increment counters)
  - **Scraped by:** Prometheus (optional) or logged locally

#### `health_checker.py`
- **Purpose:** System health monitoring
- **Checks:**
  - Database connectivity, API availability, disk space, latency
- **Relations:**
  - **Runs:** Every 60s (configurable)
  - **Alerts via:** `alerting.py` on failures

---

### **src/storage/** - Persistence Layer

#### `state_manager.py`
- **Purpose:** SQLite WAL database interface
- **Tables:**
  - `optimizer_state`, `audit_verdicts`, `incidents`, `parameter_history`, `order_log`
- **Key Functions:**
  - `save_state(state)`, `load_state()`, `query(sql)`
- **Relations:**
  - **Used by:** ALL components for persistent state
  - **File:** `data/state/optimizer_state.db`

#### `artifact_manager.py`
- **Purpose:** Object storage (S3/local) with checksums
- **Key Functions:**
  - `upload_artifact(data, artifact_id)` - Write JSON + CRC32
  - `download_artifact(artifact_id)` - Verify checksum on read
- **Relations:**
  - **Used by:** `audit/artifact_store.py`
  - **Storage:** `data/artifacts/` or S3 (config-dependent)
  - **Crypto via:** `utils/crypto_utils.py`

#### `replay_engine.py`
- **Purpose:** Reproduce decisions from immutable artifacts
- **Key Functions:**
  - `replay_decision(proposal_id)` - Re-run optimizer with same inputs
  - `verify_reproducibility(original, replayed)` - Hash comparison
- **Relations:**
  - **Reads:** `data/artifacts/` via `artifact_manager.py`
  - **Re-runs:** `optimizer/strategy_optimizer.py` with archived context
  - **Used for:** Forensic debugging, compliance audits

---

### **src/utils/** - Shared Utilities

#### `logging_config.py`
- **Purpose:** Structured logging setup
- **Formats:** JSON logs with timestamp, level, component, trace_id
- **Relations:** Imported by `main.py`, used by ALL components

#### `crypto_utils.py`
- **Purpose:** Checksums, hashing
- **Key Functions:**
  - `crc32_checksum(data)`, `sha256_hash(file)`
- **Relations:** Used by `storage/artifact_manager.py`, `audit/artifact_store.py`

#### `time_utils.py`
- **Purpose:** Timezone-aware datetime handling
- **Key Functions:**
  - `now_utc()`, `parse_iso8601(str)`, `ensure_causal(timestamp, reference)`
- **Relations:** Used by ALL components for timestamp consistency

#### `statistical_tests.py`
- **Purpose:** Bootstrap CI, hypothesis tests
- **Key Functions:**
  - `bootstrap_ci(data, metric_func, iterations=2000)` - Non-parametric CI
  - `permutation_test(data_a, data_b)` - Significance test
- **Relations:** Used by `backtesting/performance_metrics.py`, `audit/t2_checks.py`

---

### **tests/** - Test Suite

Each `test_*/` directory mirrors the structure of `src/` and tests the corresponding component in isolation.

**Key files:**
- `conftest.py` - Shared fixtures (mock data, test configs)
- `test_integration/` - End-to-end tests (full optimization cycle)

**Relations:** All tests import from `src/` and use fixtures from `conftest.py`

---

### **scripts/** - Operational Scripts

| Script | Purpose | Uses |
|--------|---------|------|
| `initialize_db.py` | Create SQLite schema | `storage/state_manager.py` |
| `load_historical_data.py` | Bootstrap market data | `data_bus/market_data_bus.py` |
| `run_audit_only.py` | Audit existing proposals without execution
| `emergency_shutdown.py` | Manual emergency stop | `governance/emergency_manager.py` |
| `generate_reports.py` | Export audit reports, backtest results | `storage/`, `backtesting/` |

---

## **Component Interaction Map**

```
main.py (Orchestrator)
    ↓
    ├─→ data_bus/market_data_bus.py ──→ data/market/
    │                                     ↓
    ├─→ processors/indicator_engine.py ←─┘
    │           ↓
    ├─→ processors/regime_classifier.py
    │           ↓
    ├─→ optimizer/strategy_optimizer.py ──→ data_bus/event_bus.py
    │           ↓                                      ↓
    │   optimizer/llm_interface.py          audit/audit_layer.py
    │      (or fallback_mode.py)                      ↓
    │                                      ├─→ audit/t1_checks.py → governance/emergency_manager.py
    │                                      ├─→ audit/t2_checks.py → governance/restriction_enforcer.py
    │                                      └─→ audit/t3_checks.py → logs/audit.log
    │                                                  ↓
    └─→ execution/execution_engine.py ←────────────────┘
                ↓
        execution/order_manager.py
                ↓
        execution/exchange_adapter.py
                ↓
            [EXCHANGE API]

    ALL components log to:
        - logs/*.log (via utils/logging_config.py)
        - monitoring/metrics_collector.py
        - storage/state_manager.py (SQLite)
```

---

## **Key Design Principles**

1. **Immutability:** Market data, audit artifacts are append-only
2. **Causality:** All timestamps verified by `processors/causal_validator.py`
3. **Separation:** Optimizer and Audit run independently, communicate via event bus
4. **Traceability:** Every decision has a causal chain stored in artifacts
5. **Safety:** T1 failures trigger immediate halt via `governance/emergency_manager.py`
6. **Reproducibility:** `storage/replay_engine.py` can re-run any decision from artifacts
