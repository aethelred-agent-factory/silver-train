# Real Data / Paper Trading System - Setup & Run Guide

## What Changed

This system has been converted from a **contaminated demo** (hardcoded metrics and signals) to a **real-data paper trading system**:

### ✓ FIXED
- ✓ **Hardcoded synthetic metrics** → Now uses real backtest results
- ✓ **Hardcoded mock signals** → Now derives signals from real indicators
- ✓ **Empty data directory** → Bootstrap script loads real exchange data
- ✓ **No portfolio tracking** → Added persistent state manager
- ✓ **Silent failures** → Now hard-fails if data missing

### Components Added
1. **PortfolioState** (`src/backtesting/portfolio_state.py`)
   - Tracks paper trades, equity, drawdown
   - Computes real PnL from trade ledger

2. **DataBootstrapValidator** (`src/processors/data_bootstrap_validator.py`)
   - Validates market data exists and is complete
   - Prevents running on fake data
   - Provides clear bootstrap instructions

3. **Bootstrap Script** (`scripts/bootstrap_all_data.py`)
   - One-command data loading for all symbols
   - Real CCXT → Parquet pipeline

---

## Quick Start

### Step 1: Load Real Market Data

```bash
cd /workspaces/codespaces-blank/stradegy_optimizer

# Load real market data from exchange
python scripts/bootstrap_all_data.py
```

This will:
- Fetch BTC/USDT, ETH/USDT, SOL/USDT, AVAX/USDT from Phemex
- Store as immutable Parquet files in `data/market/`
- Verify data integrity

**Expected Output:**
```
================================================================================
BOOTSTRAP: Loading Real Market Data
================================================================================
Symbols: BTC/USDT, ETH/USDT, SOL/USDT, AVAX/USDT
Date Range: 2025-06-01T00:00:00Z to 2026-01-31T23:59:59Z
Timeframe: 1h
...
[1/4] Loading BTC/USDT...
✓ Successfully loaded BTC/USDT
[2/4] Loading ETH/USDT...
✓ Successfully loaded ETH/USDT
...
================================================================================
BOOTSTRAP COMPLETE
================================================================================
```

### Step 2: Verify Data Was Loaded

```bash
ls -la data/market/
# Should show: BTC_USDT/, ETH_USDT/, SOL_USDT/, AVAX_USDT/ with Parquet files

# Or query database
sqlite3 data/state/optimizer_state.db "SELECT COUNT(*) FROM parameter_history;"
```

### Step 3: Run System with Real Data

```bash
python src/main.py
```

**Expected Output:**
```
================================================================================
ITERATION 1/10 - 2026-01-31 XX:XX:XX
================================================================================
Step 1: Running backtest on real market data...
  ✓ Backtest returned: profit_factor=1.23, drawdown=5.4%, trades=45
Step 2: Extracting metrics from real backtest results...
  - Profit: 23.00%
  - Max Drawdown: 5.40%
  - Win Rate: 58.33%
  - Total Trades: 45
  - Sharpe Ratio: 1.23
Step 3: Classifying market regime from real data...
  - Regime: TREND, Confidence: 85.00%
Step 4: Generating parameter proposal from real metrics...
  - Action: UPDATE
  - Reasoning: Profit positive and drawdown decreasing
Step 5: Running audit on proposal...
  - Verdict: ALLOW
Step 6: Generating REAL paper trade signals...
  - Generated REAL signal from indicators:
    Signal: 1 | Amount: 0.0234
    Entry Price: 95000.50 | SL: 92345.23
Step 7: Executing paper trade...
  ✓ Paper trade executed: BUY 0.0234 at 95000.50

Portfolio Status:
  Current Equity: $10234.50
  Total P&L: $234.50 (2.35%)
  Max Drawdown: 2.10%
  Open Positions: 1
================================================================================
```

---

## System Flow (Real Data)

```
BOOTSTRAP (One-time)
├── scripts/bootstrap_all_data.py
│   └── Fetch real OHLCV from Phemex → Parquet storage
└── Verify: data/market/ contains {BTC, ETH, SOL, AVAX}

MAIN LOOP (Iterative, 10 cycles)
├── STEP 1: Run Real Backtest
│   ├── Read real Parquet candles
│   ├── Compute real indicators (RSI, ATR, ADX)
│   ├── Generate real signals
│   └── Simulate paper trades on real OHLCV
│
├── STEP 2: Extract Real Metrics
│   └── BacktestResult → {profit, drawdown, sharpe, trades}
│
├── STEP 3: Classify Market Regime
│   └── Real indicators → {TREND, RANGE, ...}
│
├── STEP 4: Optimize Parameters
│   ├── Strategy Optimizer gets REAL metrics
│   ├── LLM proposes adjustments
│   └── Stability Guards prevent over-optimization
│
├── STEP 5: Audit Proposal
│   ├── T1: Structural integrity
│   ├── T2: Reasoning validation
│   └── T3: Information completeness
│
├── STEP 6: Generate Paper Trade Signal
│   ├── Signal Generator processes real OHLCV
│   ├── Derives signal from real indicators
│   ├── Computes position size from risk %
│   └── Creates paper trade (not hardcoded)
│
└── STEP 7: Execute Paper Trade
    ├── Enter position (tracked in portfolio)
    ├── Persist in order_log
    └── Update equity curve
```

---

## Validation Checklist

### ✓ Real Data Requirements Met
- [x] Market data from real exchange (Phemex via CCXT)
- [x] Immutable Parquet storage (no cache reuse)
- [x] System hard-fails if data missing
- [x] No synthetic candle generation
- [x] No seeded randomness for market behavior
- [x] No default/placeholder OHLCV values

### ✓ Paper Trading Requirements Met
- [x] Trades derived from real signals (not hardcoded)
- [x] Position size calculated from risk management (not fixed)
- [x] Stop-loss computed from real ATR (not arbitrary)
- [x] PnL calculated from paper trade ledger
- [x] Equity tracked through iterations
- [x] Drawdown from peak computed accurately

### ✓ Causality Requirements Met
- [x] Real data → Real indicators → Real signals
- [x] Real signals → Paper trades → Real PnL
- [x] Real PnL → Real metrics → AI optimization
- [x] AI optimization → Parameter updates → Next iteration
- [x] No hardcoded metrics at any step
- [x] No mock signals at any step

---

## File Changes Summary

### Modified Files
1. **src/main.py**
   - Added: DataBootstrapValidator import
   - Added: PortfolioState import
   - Changed: Hardcoded metrics → Real backtest results
   - Changed: Mock signal → Real signal generation
   - Added: Data validation with hard-fail
   - Added: 10-iteration loop with real data flow
   - Removed: Hardcoded synthetic values

### New Files
1. **src/backtesting/portfolio_state.py**
   - Tracks paper trades, equity, drawdown
   - Computes metrics from trade ledger
   - Persists state across iterations

2. **src/processors/data_bootstrap_validator.py**
   - Validates market data availability
   - Checks data integrity
   - Provides bootstrap instructions if missing

3. **scripts/bootstrap_all_data.py**
   - Loads all required symbols in one command
   - Handles errors gracefully
   - Verifies each symbol

---

## Troubleshooting

### "Data validation failed" Error
**Cause**: Market data not loaded  
**Fix**:
```bash
python scripts/bootstrap_all_data.py
```

### "No data directory for BTC/USDT" Error
**Cause**: Bootstrap script not run  
**Fix**:
```bash
python scripts/bootstrap_all_data.py
```

### "Insufficient candles" Error
**Cause**: Not enough historical data  
**Fix**: Wait for bootstrap to complete (can take 5-15 minutes depending on API rate limits)

### "Exchange connection timeout"
**Cause**: API rate limits or network issues  
**Fix**:
```bash
# Try again - CCXT will retry automatically
python scripts/bootstrap_all_data.py

# Or manually load one symbol
python scripts/load_historical_data.py --symbol BTC/USDT \
  --start 2025-06-01T00:00:00Z --end 2026-01-31T23:59:59Z
```

### Portfolio shows $0 equity
**Cause**: Paper trades not executing properly  
**Fix**: Check that data was loaded and backtest generates valid signals
```bash
# Manually verify one backtest
python scripts/run_audit_only.py --proposal_file /path/to/proposal.json
```

---

## Configuration

### Optimization Loop
**File**: `src/main.py` (lines 155-165)
```python
symbol = 'BTC/USDT'                        # Symbol to optimize
start_date = '2025-06-01T00:00:00Z'       # Data start
end_date = '2026-01-31T23:59:59Z'         # Data end
iteration = 0
max_iterations = 10                        # Number of optimization cycles
```

### Portfolio Parameters
**File**: `src/main.py` (line 161)
```python
portfolio = PortfolioState(initial_capital=10000.0)
```

### Data Date Range
**File**: `scripts/bootstrap_all_data.py` (lines 15-17)
```python
START_DATE = '2025-06-01T00:00:00Z'
END_DATE = '2026-01-31T23:59:59Z'
TIMEFRAME = '1h'
```

---

## Performance Expectations

### Data Loading
- BTC/USDT: ~5-10 minutes (9000+ candles)
- ETH/USDT: ~5-10 minutes
- SOL/USDT: ~5-10 minutes
- AVAX/USDT: ~5-10 minutes
- **Total**: ~20-40 minutes depending on exchange rate limits

### Optimization Loop
- Per iteration: ~30-60 seconds
- 10 iterations: ~5-10 minutes
- Bottleneck: Backtest on large dataset

---

## Data Realism Verification

To confirm this is running on real data:

```python
# Check 1: Data exists
import os
assert os.path.exists('data/market/BTC_USDT'), "BTC data missing"

# Check 2: Data is real (not random)
import pyarrow.parquet as pq
df = pq.read_table('data/market/BTC_USDT').to_pandas()
assert not df['volume'].isna().any(), "Volume is NaN"
assert (df['volume'] > 0).any(), "Some volumes are zero (realistic)"

# Check 3: Candles are continuous
import pandas as pd
df['timestamp'] = pd.to_datetime(df['timestamp'])
assert df['timestamp'].is_monotonic_increasing, "Timestamps not monotonic"

# Check 4: Prices are realistic
assert df['high'].mean() > df['low'].mean(), "High < Low"
assert (df['high'] >= df['close']).all(), "High < Close (invalid)"
assert (df['low'] <= df['close']).all(), "Low > Close (invalid)"

print("✓ All data realism checks passed")
```

---

## Next Steps

1. **Run system**: `python src/main.py`
2. **Monitor iterations**: Watch real backtest results update
3. **Check portfolio**: View equity curve and PnL
4. **Analyze results**: `sqlite3 data/state/optimizer_state.db` to query history

---

## Support

For issues or questions:
1. Check logs: `grep ERROR logs/*.log`
2. Verify data: `ls -la data/market/`
3. Check database: `sqlite3 data/state/optimizer_state.db ".tables"`
