# Supabase Migration Plan

## Overview
This document outlines the migration from local SQLite development to production Supabase deployment.

## Current State Analysis

### Local Development Stack
- **State Management**: SQLite database
- **Artifact Storage**: Local filesystem (JSON + SHA256)
- **Market Data**: Local CSV/Parquet files
- **Limitations**: 
  - Single machine only
  - No real-time updates
  - No multi-agent coordination
  - Manual scaling

### Target Production Stack
- **State Management**: Supabase Postgres
- **Artifact Storage**: Supabase Storage
- **Market Data**: Supabase with TimescaleDB
- **Benefits**:
  - Distributed architecture
  - Real-time subscriptions
  - Multi-agent support
  - Auto-scaling
  - Built-in auth & RLS

## Storage Abstraction Design

### Interface
```python
# src/strategy_optimizer/storage/interface.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class StorageInterface(ABC):
    """Abstract storage interface for backend-agnostic data access"""
    
    @abstractmethod
    async def save_state(self, key: str, value: Dict) -> bool:
        """Save optimizer state"""
        pass
    
    @abstractmethod
    async def load_state(self, key: str) -> Optional[Dict]:
        """Load optimizer state"""
        pass
    
    @abstractmethod
    async def save_artifact(self, artifact_id: str, content: Dict, checksum: str) -> bool:
        """Save audit artifact with checksum"""
        pass
    
    @abstractmethod
    async def load_artifact(self, artifact_id: str) -> Optional[Dict]:
        """Load audit artifact"""
        pass
    
    @abstractmethod
    async def query_market_data(self, symbol: str, start: str, end: str) -> List[Dict]:
        """Query market data in date range"""
        pass
```

### SQLite Implementation (Current)
- Continue using existing SQLite code
- Wrap in `SqliteStorage` class implementing `StorageInterface`
- No behavior changes, just structural refactor

### Supabase Implementation (Future)
- Implement `SupabaseStorage` class
- Use `supabase-py` client library
- Map methods to Supabase API calls

## Database Schema (Supabase)

### Tables
```sql
-- Optimizer state
CREATE TABLE optimizer_states (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key TEXT UNIQUE NOT NULL,
    value JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit artifacts
CREATE TABLE audit_artifacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    artifact_id TEXT UNIQUE NOT NULL,
    content JSONB NOT NULL,
    checksum TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Market data (with TimescaleDB)
CREATE TABLE market_data (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    open NUMERIC,
    high NUMERIC,
    low NUMERIC,
    close NUMERIC,
    volume NUMERIC,
    PRIMARY KEY (time, symbol)
);

SELECT create_hypertable('market_data', 'time');
```

### Storage Buckets
- `audit-artifacts`: JSON audit files with checksums
- `market-data-archives`: Historical data archives
- `model-checkpoints`: Optimizer model states

## Migration Scripts

### Data Export (SQLite → JSON)
```bash
python scripts/export_sqlite_to_json.py
# Outputs: exports/optimizer_states.json, exports/artifacts.json
```

### Data Import (JSON → Supabase)
```bash
python scripts/import_json_to_supabase.py
# Requires: SUPABASE_URL, SUPABASE_SERVICE_KEY
```

## Environment Configuration

### Development (SQLite)
```bash
DATABASE_BACKEND=sqlite
SQLITE_PATH=data/state/optimizer_state.db
```

### Staging (Supabase Test)
```bash
DATABASE_BACKEND=supabase
SUPABASE_URL=https://staging-project.supabase.co
SUPABASE_KEY=staging-key
```

### Production (Supabase)
```bash
DATABASE_BACKEND=supabase
SUPABASE_URL=https://prod-project.supabase.co
SUPABASE_KEY=prod-key
```

## Testing Strategy

### Unit Tests
- Test both `SqliteStorage` and `SupabaseStorage` with same test suite
- Use interface compliance tests
- Mock Supabase client for offline testing

### Integration Tests
- Run against real Supabase test project
- Verify data integrity after migration
- Performance benchmarks (latency, throughput)

### Validation
- Compare SQLite vs Supabase results on same input
- Verify checksums match
- Audit trail completeness check

## Rollback Plan

If Supabase migration fails:
1. Switch `DATABASE_BACKEND=sqlite` in environment
2. Restore from last SQLite backup
3. Continue development on local stack
4. Debug Supabase issues in staging

## Timeline

- **Week 1**: Storage abstraction implementation
- **Week 2**: Supabase project setup + schema
- **Week 3**: Migration scripts + testing
- **Week 4**: Staged rollout + monitoring

## Success Metrics

- Zero data loss during migration
- <100ms p99 latency for state operations
- 99.9% uptime on Supabase
- Successful multi-agent coordination
- Cost <$50/month for expected workload
