from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models.event_models import ChannelType


class ActionDispatchPayload(BaseModel):
    case_id: str
    channel: ChannelType
    recipient_email: Optional[str] = None
    recipient_phone: Optional[str] = None
    subject: Optional[str] = None
    content: Optional[str] = None
    amount: float
    currency: str = "USD"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ActionDispatchResult(BaseModel):
    action_id: str
    case_id: str
    channel: ChannelType
    status: str  # success, simulated, failed, rejected
    idempotency_key: str
    external_reference_id: Optional[str] = None
    cost_usd: float = 0.0
    dispatched_at: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)


class PromiseToPayRequest(BaseModel):
    case_id: str
    promised_date: datetime
    promised_amount: float
    notes: Optional[str] = None
