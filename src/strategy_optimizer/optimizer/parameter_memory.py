import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional


class ParameterMemory:
    """
    Tracks tested parameter combinations and learning memory per spec 3.3.1.

    Features:
    - Hashes of tested parameter sets
    - Rolling performance statistics per regime
    - Blacklisted parameter sets that caused drawdown > 40%

    Uses state_manager (SQLite) for persistence.
    """

    def __init__(self, state_manager=None):
        self.state_manager = state_manager
        self.in_memory_cache = {}  # Cache for fast lookups
        self.blacklist_set = (
            set()
        )  # Set of blacklisted parameter hashes (renamed to avoid conflict with method name)

        if state_manager:
            self._initialize_tables()

        logging.info("Initialized ParameterMemory with learning memory tracking.")

    def _initialize_tables(self):
        """Create necessary database tables for parameter memory."""
        try:
            self.state_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS parameter_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    params_hash TEXT NOT NULL,
                    params_json TEXT NOT NULL,
                    regime TEXT NOT NULL,
                    profit_pct REAL,
                    max_drawdown_pct REAL,
                    win_rate REAL,
                    total_trades INTEGER,
                    result TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(params_hash, regime)
                );
            """
            )

            self.state_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    params_hash TEXT NOT NULL UNIQUE,
                    params_json TEXT,
                    reason TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            self.state_manager.execute_query(
                """
                CREATE TABLE IF NOT EXISTS best_parameters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    regime TEXT NOT NULL UNIQUE,
                    params_json TEXT NOT NULL,
                    profit_pct REAL,
                    max_drawdown_pct REAL,
                    iteration INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                );
            """
            )

            # Load blacklist on startup
            self._load_blacklist()

            logging.info("Parameter memory tables initialized.")
        except Exception as e:
            logging.warning(f"Could not initialize parameter tables: {e}")

    def log_tested(
        self, params: dict, regime: str, metrics: Dict = None, result: str = "TESTED"
    ):
        """
        Log a tested parameter combination with performance metrics.

        Args:
            params: Parameter dictionary
            regime: Market regime (TREND, RANGE, HIGH_VOL)
            metrics: Performance metrics {profit_pct, max_drawdown_pct, win_rate, total_trades}
            result: Test result (TESTED, UPDATE, HOLD, ROLLBACK)
        """
        params_hash = self._hash_params(params)
        params_json = json.dumps(params, sort_keys=True, default=str)

        if not metrics:
            metrics = {}

        profit_pct = metrics.get("profit", metrics.get("profit_pct", 0))
        max_drawdown_pct = metrics.get("max_drawdown_pct", 0)
        win_rate = metrics.get("win_rate", 0)
        total_trades = metrics.get("total_trades", 0)

        logging.info(
            f"Logging tested params {params_hash} for {regime}: "
            f"profit={profit_pct:.2f}%, dd={max_drawdown_pct:.2f}%"
        )

        if self.state_manager:
            try:
                query = """
                    INSERT OR REPLACE INTO parameter_history 
                    (params_hash, params_json, regime, profit_pct, max_drawdown_pct, win_rate, total_trades, result)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """
                self.state_manager.execute_query(
                    query,
                    (
                        params_hash,
                        params_json,
                        regime,
                        profit_pct,
                        max_drawdown_pct,
                        win_rate,
                        total_trades,
                        result,
                    ),
                )
            except Exception as e:
                logging.debug(f"Could not log to DB: {e}")

        # Cache in memory
        cache_key = f"{params_hash}:{regime}"
        self.in_memory_cache[cache_key] = {
            "params": params,
            "profit_pct": profit_pct,
            "max_drawdown_pct": max_drawdown_pct,
            "win_rate": win_rate,
            "total_trades": total_trades,
        }

    def has_been_tested(self, params: dict, regime: str) -> bool:
        """
        Check if parameter combination has been tested in a given regime.
        """
        params_hash = self._hash_params(params)
        cache_key = f"{params_hash}:{regime}"

        # Check in-memory cache first
        if cache_key in self.in_memory_cache:
            return True

        if not self.state_manager:
            return False

        try:
            query = "SELECT 1 FROM parameter_history WHERE params_hash = ? AND regime = ? LIMIT 1"
            result = self.state_manager.execute_query(
                query, (params_hash, regime), fetch="one"
            )
            return result is not None
        except Exception as e:
            logging.debug(f"Could not query DB: {e}")
            return False

    def get_best_params(self, regime: str) -> Dict:
        """
        Get best-performing parameters for a given regime.
        Returns empty dict if no params found.
        """
        if not self.state_manager:
            return {}

        try:
            query = """
                SELECT params_json FROM best_parameters 
                WHERE regime = ? 
                ORDER BY profit_pct DESC, max_drawdown_pct ASC 
                LIMIT 1
            """
            result = self.state_manager.execute_query(query, (regime,), fetch="one")

            if result:
                return json.loads(result[0])
            return {}
        except Exception as e:
            logging.debug(f"Could not get best params: {e}")
            return {}

    def record_best_params(
        self, regime: str, params: Dict, metrics: Dict, iteration: int
    ) -> None:
        """
        Record the best-performing parameters for a regime.
        Updates if new params have better profit or lower drawdown.
        """
        if not self.state_manager:
            return

        params_json = json.dumps(params, sort_keys=True, default=str)
        profit_pct = metrics.get("profit", 0)
        max_drawdown_pct = metrics.get("max_drawdown_pct", 0)

        logging.info(
            f"Recording best params for {regime}: profit={profit_pct:.2f}%, dd={max_drawdown_pct:.2f}%"
        )

        try:
            query = """
                INSERT OR REPLACE INTO best_parameters 
                (regime, params_json, profit_pct, max_drawdown_pct, iteration)
                VALUES (?, ?, ?, ?, ?)
            """
            self.state_manager.execute_query(
                query, (regime, params_json, profit_pct, max_drawdown_pct, iteration)
            )
        except Exception as e:
            logging.debug(f"Could not record best params: {e}")

    def blacklist(
        self, params_hash: str, params: Dict = None, reason: str = ""
    ) -> None:
        """
        Spec 3.3.1: Blacklist a parameter set that caused excessive drawdown.
        Prevents reuse of bad parameter combinations.
        """
        self.blacklist_set.add(params_hash)

        if not self.state_manager:
            return

        params_json = (
            json.dumps(params, sort_keys=True, default=str) if params else None
        )

        logging.warning(f"Blacklisting params {params_hash}: {reason}")

        try:
            query = """
                INSERT OR IGNORE INTO blacklist (params_hash, params_json, reason)
                VALUES (?, ?, ?)
            """
            self.state_manager.execute_query(query, (params_hash, params_json, reason))
        except Exception as e:
            logging.debug(f"Could not blacklist params: {e}")

    def is_blacklisted(self, params: Dict) -> bool:
        """
        Check if a parameter set is blacklisted.
        """
        params_hash = self._hash_params(params)
        return params_hash in self.blacklist_set

    def _load_blacklist(self) -> None:
        """Load blacklist from database on startup."""
        if not self.state_manager:
            return

        try:
            query = "SELECT params_hash FROM blacklist"
            results = self.state_manager.execute_query(query, fetch="all")

            for row in results:
                self.blacklist_set.add(row[0])

            logging.info(f"Loaded {len(self.blacklist_set)} blacklisted parameter sets")
        except Exception as e:
            logging.debug(f"Could not load blacklist: {e}")

    def get_per_regime_stats(self, regime: str) -> Dict:
        """
        Get rolling performance statistics for a regime.
        """
        if not self.state_manager:
            return {}

        try:
            query = """
                SELECT 
                    COUNT(*) as total_tested,
                    AVG(profit_pct) as avg_profit,
                    AVG(max_drawdown_pct) as avg_drawdown,
                    AVG(win_rate) as avg_win_rate,
                    MAX(profit_pct) as best_profit,
                    MIN(max_drawdown_pct) as best_drawdown
                FROM parameter_history
                WHERE regime = ?
            """
            result = self.state_manager.execute_query(query, (regime,), fetch="one")

            if result:
                return {
                    "total_tested": result[0] or 0,
                    "avg_profit": result[1] or 0,
                    "avg_drawdown": result[2] or 0,
                    "avg_win_rate": result[3] or 0,
                    "best_profit": result[4] or 0,
                    "best_drawdown": result[5] or 0,
                }
            return {}
        except Exception as e:
            logging.debug(f"Could not get regime stats: {e}")
            return {}

    def _hash_params(self, params: dict) -> str:
        """
        Creates a deterministic hash of the parameters dictionary.
        Uses MD5 for consistency with other modules.
        """
        params_str = json.dumps(params, sort_keys=True, default=str)
        return hashlib.md5(params_str.encode()).hexdigest()[:8]
