# Silvertrain System

A trading/strategy optimizer that supports backtesting and live (paper) trading.

## Development Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    source .venv/bin/activate
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run sanity checks:**
    ```bash
    pytest
    python -m strategy_optimizer.main --help
    ```
