from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.ledger_models import LedgerEntryType


class LedgerEntryCreate(BaseModel):
    case_id: str
    entry_type: LedgerEntryType
    amount: float = 0.0
    currency: str = "USD"
    gross_recovered: float = 0.0
    gateway_fee: float = 0.0
    communication_cost: float = 0.0
    ai_token_cost: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sequence_id: int
    entry_id: str
    case_id: str
    entry_type: LedgerEntryType
    amount: float
    currency: str
    gross_recovered: float
    gateway_fee: float
    communication_cost: float
    ai_token_cost: float
    net_recovered: float
    previous_hash: str
    current_hash: str
    metadata_json: Dict[str, Any]
    timestamp: datetime


class FinancialMetricsResponse(BaseModel):
    total_revenue_at_risk: float
    total_recovered_revenue: float
    total_recovery_costs: float
    net_recovered_revenue: float
    overall_recovery_rate_pct: float
    net_roi_multiple: float
    total_cases_processed: int
    resolved_cases_count: int
    active_cases_count: int
    guardrail_blocked_count: int


class CohortRecoveryStats(BaseModel):
    risk_type: str
    total_cases: int
    total_at_risk_usd: float
    recovered_usd: float
    recovery_rate_pct: float
    avg_hours_to_recover: float
