from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid

class Candle(BaseModel):
    """Represents a single OHLCV candle."""
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

class CausalChainRef(BaseModel):
    """Reference to a piece of evidence in the causal chain."""
    type: str
    id: str

class OptimizerProposal(BaseModel):
    """Schema for a parameter proposal from the optimizer."""
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    proposal_version: int
    source: str
    proposed_parameters: Dict[str, Any]
    context: Dict[str, Any]
    causal_chain_refs: List[CausalChainRef]

class TieredFinding(BaseModel):
    """A single finding from the audit layer, categorized by tier."""
    tier: str
    code: str
    explanation: str
    impact: Optional[str] = None
    remediation: Optional[str] = None

class AuditAction(BaseModel):
    """The action to be taken based on the audit verdict."""
    type: str
    restrictions: Optional[Dict[str, Any]] = None

class AuditVerdict(BaseModel):
    """Schema for an audit verdict on an optimizer proposal."""
    audit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    proposal_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tiered_findings: List[TieredFinding]
    action: AuditAction
    artifact_refs: List[str]
    checksum: str

class BacktestResult(BaseModel):
    """Schema for the results of a backtest."""
    start_date: datetime
    end_date: datetime
    profit_factor: float
    max_drawdown_pct: float
    total_trades: int
    win_rate: float
    sharpe_ratio: float
    sortino_ratio: float
    equity_curve: List[float]
