# Self-Auditing Strategy Optimizer

This project implements a robust, modular, and self-auditing strategy optimizer designed for production-grade trading systems. It adheres to strict principles of immutability, causality, and separation of concerns to ensure safety, traceability, and reproducibility of all trading decisions.

The system incorporates an independent Audit Layer that continuously validates optimizer proposals against a tiered set of rules (T1 for structural integrity, T2 for reasoning flaws, T3 for informational gaps). Based on audit verdicts, the system can block executions, apply restrictions, or request remediation, ensuring a human-in-the-loop governance model.

---

## **Project Architecture**

The project is structured with a clear separation of concerns, organized into several key modules:

```
strategy-optimizer/
│
├── README.md
├── requirements.txt                 # Python dependencies
├── setup.py                         # Package installation configuration
├── .env.example                     # Environment variable template
├── docker-compose.yml               # Docker Compose for container orchestration
│
├── config/                          # System configuration files (YAML)
│   ├── system_config.yaml           # General settings, paths, API endpoints
│   ├── audit_rules.yaml             # Definitions for T1/T2/T3 audit checks
│   ├── regime_config.yaml           # Thresholds for market regime classification
│   ├── parameter_bounds.yaml        # Min/max ranges for strategy parameters
│   └── safe_baseline.yaml           # Fallback parameters for emergency mode
│
├── data/                            # Persistent data storage
│   ├── market/                      # Raw market data (OHLCV candles)
│   ├── artifacts/                   # Immutable audit artifacts (JSON + checksums)
│   └── state/                       # SQLite WAL database for optimizer state
│
├── logs/                            # Application logs
│   ├── system.log
│   ├── audit.log
│   ├── execution.log
│   └── emergency.log
│
├── src/                             # Core application source code
│   ├── main.py                      # The central orchestrator of the system
│   ├── data_bus/                    # Data ingestion, event communication, and schemas
│   ├── processors/                  # Data processing (indicators, regime classification, validation)
│   ├── optimizer/                   # Strategy optimization logic (parameter proposals, LLM integration, fallback)
│   ├── backtesting/                 # Backtesting engine, position management, performance metrics
│   ├── audit/                       # The independent audit layer (T1/T2/T3 checks, causal validation)
│   ├── execution/                   # Trade execution (exchange interface, order management)
│   ├── governance/                  # Human oversight and emergency protocols
│   ├── monitoring/                  # Observability (dashboard, alerting, metrics, health checks)
│   ├── storage/                     # Persistence layer (state management, artifact storage, replay)
│   └── utils/                       # Shared utility functions (logging, crypto, time, stats)
│
├── tests/                           # Unit and integration tests
│   ├── conftest.py                  # Pytest fixtures
│   ├── test_data_bus/
│   ├── test_processors/
│   ├── ... (mirrors src/ structure)
│   └── test_integration/
│
├── scripts/                         # Operational scripts
│   ├── initialize_db.py             # Database schema creation
│   ├── load_historical_data.py      # Bootstrap market data
│   ├── run_audit_only.py            # Audit existing proposals without execution
│   ├── emergency_shutdown.py        # Manual emergency stop
│   └── generate_reports.py          # Export audit/backtest reports
│
└── docs/                            # Project documentation
    ├── architecture.md              # Detailed architectural overview
    ├── api_reference.md             # Component APIs and data schemas
    ├── deployment_guide.md          # Guide for deploying the system
    └── troubleshooting.md           # Common issues and solutions
```

---

## **Key Features & Principles**

-   **Modular Design:** Clear separation of concerns for maintainability and scalability.
-   **Self-Auditing:** An independent Audit Layer (T1/T2/T3 checks) verifies all optimizer decisions.
-   **Immutability:** Market data and audit artifacts are treated as append-only records.
-   **Causality:** Strict enforcement that all computations and decisions are based only on past data, preventing lookahead bias.
-   **Traceability & Reproducibility:** Every decision is linked to a causal chain and immutable artifacts, allowing for forensic analysis and reconstruction.
-   **Human-in-the-Loop Governance:** Approval workflows, incident tracking, and emergency protocols ensure human oversight for critical events.
-   **LLM Integration:** Utilizes DeepSeek API for intelligent parameter proposals, with a robust deterministic fallback mechanism.
-   **Comprehensive Observability:** Integrated monitoring, alerting, metrics collection, and a web dashboard for real-time insights.

---

## **Getting Started**

### **Prerequisites**

-   Python 3.9+
-   `pip`
-   `git`
-   (Optional for containerization) Docker & Docker Compose

### **Setup Steps**

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-org/strategy-optimizer.git
    cd strategy-optimizer
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file based on `.env.example` and populate it with your API keys and other necessary configurations.
    ```bash
    cp .env.example .env
    # Open .env and add your API keys (e.g., EXCHANGE_API_KEY, DEEPSEEK_API_KEY)
    ```

5.  **Initialize the Database:**
    ```bash
    python scripts/initialize_db.py
    ```

6.  **Load Historical Data (Optional, but recommended for testing):**
    ```bash
    python scripts/load_historical_data.py --symbol BTC/USDT --start 2023-01-01T00:00:00Z --end 2023-12-31T23:59:59Z --timeframe 1h
    ```

7.  **Run Tests:**
    ```bash
    pytest
    ```

---

## **Usage**

To run the main optimizer, ensure all configurations are set up and then execute:

```bash
python src/main.py
```

Refer to the `docs/` directory for detailed guides on deployment, API references, and troubleshooting.

---

## **Contributing**

Contributions are welcome! Please refer to our `CONTRIBUTING.md` (to be created) for guidelines.

---

## **License**

This project is licensed under the MIT License.
