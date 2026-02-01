# Silvertrain System

A trading/strategy optimizer that supports backtesting and live (paper) trading.

## Architecture Status

### Current Implementation (v0.1 - Local Development)
- **Database**: SQLite (`data/state/optimizer_state.db`)
- **Artifacts**: Local JSON files (`data/artifacts/`)
- **Deployment**: Single-machine development
- **Limitations**: No real-time features, no multi-agent coordination

### Planned Architecture (v1.0 - Production)
- **Database**: Supabase Postgres (with TimescaleDB for time-series)
- **Artifacts**: Supabase Storage (with checksums and versioning)
- **Real-time**: Supabase Realtime for event streaming
- **Multi-agent**: Distributed agent coordination
- **Deployment**: Cloud-native, horizontally scalable

### Migration Roadmap

**Phase 1: Storage Abstraction** (Current Sprint)
- [ ] Create `StorageInterface` abstract class
- [ ] Implement `SqliteStorage` (current backend)
- [ ] Implement `SupabaseStorage` (future backend)
- [ ] Add environment-based backend selection

**Phase 2: Supabase Setup** (Next Sprint)
- [ ] Create Supabase project and configure authentication
- [ ] Define database schema with migrations
- [ ] Setup Storage buckets with RLS policies
- [ ] Create Edge Functions for real-time processing

**Phase 3: Dual-Mode Operation** (Testing Phase)
- [ ] Run SQLite locally, Supabase in staging
- [ ] Data migration scripts (SQLite → Supabase)
- [ ] Integration tests for both backends
- [ ] Performance benchmarking

**Phase 4: Production Migration** (Deployment)
- [ ] Migrate historical data to Supabase
- [ ] Enable Realtime subscriptions
- [ ] Deploy multi-agent coordination
- [ ] Deprecate SQLite backend

For development, use SQLite (default). For production deployment, set `DATABASE_BACKEND=supabase` in your `.env` file.

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
