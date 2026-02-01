# Silvertrain System Architecture

This document provides a high-level overview of the Silvertrain System's architecture.

## Directory Structure

The project is organized into the following main directories:

```
silvertrain-system/
│
├── README.md
├── requirements.txt
├── config/
├── data/
├── logs/
├── src/
├── tests/
├── scripts/
└── docs/
```

## Core Modules

The `src` directory contains the core modules of the Silvertrain System:

*   **`main.py`**: The central orchestrator of the system.
*   **`data_bus`**: Handles data ingestion, event communication, and schemas.
*   **`processors`**: Contains modules for data processing, including indicators, regime classification, and validation.
*   **`optimizer`**: Implements the strategy optimization logic.
*   **`backtesting`**: Includes the backtesting engine, position management, and performance metrics.
*   **`audit`**: The independent audit layer for verifying optimizer decisions.
*   **`execution`**: Manages trade execution.
*   **`governance`**: Implements human oversight and emergency protocols.
*   **`monitoring`**: Provides observability features like dashboards, alerting, and metrics.
*   **`storage`**: The persistence layer for state management and artifact storage.
*   **`utils`**: Contains shared utility functions.
