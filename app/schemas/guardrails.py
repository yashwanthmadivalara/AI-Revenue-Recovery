from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class GuardrailCheckRequest(BaseModel):
    customer_id: str
    channel: str
    amount: float
    timezone: Optional[str] = "UTC"


class GuardrailViolation(BaseModel):
    rule_name: str
    severity: str = "error"  # warning, error, block
    message: str


class GuardrailEvaluationResult(BaseModel):
    is_compliant: bool
    requires_human_approval: bool = False
    violations: List[GuardrailViolation] = Field(default_factory=list)
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)
    contact_count_last_7_days: int = 0
    has_active_dispute: bool = False
    active_promise_to_pay: bool = False
    is_quiet_hours: bool = False


class PolicyConfig(BaseModel):
    max_contact_attempts_per_week: int = 3
    enable_dispute_killswitch: bool = True
    enable_quiet_hours: bool = True
    quiet_hours_start_utc: int = 22
    quiet_hours_end_utc: int = 7
    high_value_threshold_usd: float = 5000.00
    promise_to_pay_grace_days: int = 3
