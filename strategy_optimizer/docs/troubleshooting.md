# Troubleshooting Guide

This document provides solutions to common issues and problems encountered while setting up, running, or developing the Self-Auditing Strategy Optimizer.

---

## **1. General Issues**

### **"ModuleNotFoundError: No module named 'src.something'"**

-   **Problem:** Python cannot find one of the modules in the `src` directory.
-   **Solution:**
    1.  Ensure you are running your script from the project root directory (`strategy-optimizer/`).
    2.  Check that your Python path is correctly configured. When running scripts directly, you might need to manually add the `src` directory to `PYTHONPATH` or use the `python -m` command.
    3.  If running from the project root, ensure you have activated your virtual environment and installed all dependencies (`pip install -r requirements.txt`).

### **"Permission Denied" Errors**

-   **Problem:** The application or a script is trying to write to a file or directory without the necessary permissions.
-   **Solution:**
    -   Check the permissions of the `data/`, `logs/`, and `config/` directories. Ensure the user running the application has read/write access.
    -   If using Docker, ensure the mounted volumes have correct permissions.

### **Configuration Loading Errors (YAML/Environment Variables)**

-   **Problem:** The application fails to load configuration from YAML files or environment variables (`.env`).
-   **Solution:**
    -   Verify that all `.yaml` files in the `config/` directory are valid YAML syntax. Use an online YAML validator if unsure.
    -   Ensure your `.env` file exists in the project root and is correctly formatted (key=value pairs).
    -   Check that all required environment variables are set, as indicated in `.env.example`.

---

## **2. Database Issues**

### **"OperationalError: unable to open database file"**

-   **Problem:** SQLite database file cannot be accessed.
-   **Solution:**
    -   Verify that the `data/state/` directory exists and has write permissions.
    -   Ensure no other process is holding an exclusive lock on the `optimizer_state.db` file.

### **"sqlite3.OperationalError: no such table: some_table"**

-   **Problem:** A required database table does not exist.
-   **Solution:**
    -   Run the database initialization script: `python scripts/initialize_db.py`.
    -   If running in Docker, ensure this script is run as part of your `docker-compose up` or before starting the main application.

---

## **3. Exchange/API Connectivity Issues**

### **"ccxt.base.errors.AuthenticationError"**

-   **Problem:** Invalid API key or secret for the cryptocurrency exchange.
-   **Solution:**
    -   Double-check your `EXCHANGE_API_KEY` and `EXCHANGE_SECRET_KEY` in your `.env` file.
    -   Ensure your API keys have the necessary permissions (e.g., read data, place orders) on the exchange.

### **"ccxt.base.errors.NetworkError" / "requests.exceptions.ConnectionError"**

-   **Problem:** Inability to connect to the exchange API or DeepSeek API.
-   **Solution:**
    -   Check your internet connection.
    -   Verify the exchange API endpoint is correct and accessible.
    -   Check for any firewalls or network restrictions that might be blocking outbound connections.
    -   The exchange or DeepSeek API might be experiencing downtime. Check their status pages.

### **DeepSeek API Errors**

-   **Problem:** Issues with the DeepSeek LLM API.
-   **Solution:**
    -   Verify your `DEEPSEEK_API_KEY` in `.env`.
    -   Check the DeepSeek API status page.
    -   Review the logs for specific error messages from the `llm_interface.py` module.

---

## **4. Audit Layer Issues**

### **"T1_Contradiction" or other T1 Flags**

-   **Problem:** Critical structural integrity violation detected.
-   **Solution:**
    -   **Immediate Action:** The system will halt or revert to a safe baseline. Investigate the `audit.log` and the specific `AuditVerdict` artifact for details.
    -   **Root Cause Analysis:** Examine the `OptimizerProposal` that triggered the flag, checking the `proposed_parameters` and `context` for anomalies (e.g., unexpected regime classification, out-of-bounds parameters).
    -   Review the `config/audit_rules.yaml` to understand the exact conditions for the triggered rule.

### **"T2_InsufficientSample" or other T2 Flags**

-   **Problem:** Reasoning flaw or confidence degradation detected.
-   **Solution:**
    -   The system will apply restrictions (e.g., reduced position size). Review `audit.log` for more information.
    -   **Root Cause Analysis:** The `explanation` field in the `TieredFinding` will provide details. For `T2_InsufficientSample`, this might mean your backtest window was too short or market conditions were too quiet.
    -   Consider adjusting strategy parameters or increasing data window size for backtesting.

### **"T3_ConfigGap" or other T3 Flags**

-   **Problem:** Informational gap or missing configuration.
-   **Solution:**
    -   This typically results in remediation requests logged to `audit.log`.
    -   Review the `config/` files and ensure all necessary parameters for the current strategy are defined.
    -   Consult the `API_Reference.md` for expected configuration keys.

---

## **5. Monitoring & Dashboard Issues**

### **Dashboard Not Accessible**

-   **Problem:** Cannot open the FastAPI dashboard in your browser.
-   **Solution:**
    -   Ensure the `DashboardServer` is running. If using `docker-compose`, check `docker-compose ps`.
    -   Verify the port in `config/system_config.yaml` (`monitoring.dashboard_port`) matches the port you are trying to access. Default is `5000`.
    -   Check for any firewall rules blocking the port.

### **Metrics Not Updating**

-   **Problem:** Prometheus-style metrics (e.g., equity, trade counts) are not updating.
-   **Solution:**
    -   Ensure `MetricsCollector` is correctly initialized and its `increment` and `update` methods are being called at relevant points in the code.
    -   Check logs for any errors related to metrics collection.

---

*(This document is a placeholder. More specific troubleshooting steps, common error codes, and FAQs will be added as the project evolves.)*
