from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
class BaseModelWithEq(BaseModel):
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BaseModel):
            return False
        try:
            return self.model_dump() == other.model_dump()
        except Exception:
            return False


class Candle(BaseModelWithEq):
    """Represents a single OHLCV candle."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class CausalChainRef(BaseModelWithEq):
    """Reference to a piece of evidence in the causal chain."""
    type: str
    id: str

class OptimizerProposal(BaseModelWithEq):
    """Schema for a parameter proposal from the optimizer."""
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    proposal_version: int
    source: str
    proposed_parameters: Dict[str, Any]
    context: Dict[str, Any]
    causal_chain_refs: List[CausalChainRef]

class TieredFinding(BaseModelWithEq):
    """A single finding from the audit layer, categorized by tier."""
    tier: str
    code: str
    explanation: str
    impact: Optional[str] = None
    remediation: Optional[str] = None

class AuditAction(BaseModelWithEq):
    """The action to be taken based on the audit verdict."""
    type: str
    restrictions: Optional[Dict[str, Any]] = None

class AuditVerdict(BaseModelWithEq):
    """Schema for an audit verdict on an optimizer proposal."""
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: Optional[str] = ''
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tiered_findings: List[TieredFinding] = Field(default_factory=list)
    action: AuditAction = Field(default_factory=lambda: AuditAction(type='ALLOW'))
    artifact_refs: List[str] = Field(default_factory=list)
    checksum: Optional[str] = ''

class BacktestResult(BaseModelWithEq):
    """Schema for the results of a backtest per spec section 3.2."""
    start_date: datetime
    end_date: datetime
    profit_factor: float
    max_drawdown_pct: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    sortino_ratio: float
    equity_curve: List[float]
    trades: List[Dict[str, Any]] = Field(default_factory=list)  # Trade-by-trade details
    drawdowns: List[Dict[str, Any]] = Field(default_factory=list)  # Drawdown events with credit assignment
    per_regime_metrics: Dict[str, Any] = Field(default_factory=dict)  # Metrics broken down by regime (spec 3.2)
    parameter_hash: Optional[str] = None  # Hash of parameters used for this backtest
    total_return_pct: float = 0.0  # Total return percentage
    avg_r_multiple: float = 0.0  # Average R-multiple (profit per unit of risk)
