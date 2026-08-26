from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from app.models.event_models import RiskType, RiskSeverity


class CustomerCreate(BaseModel):
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    company_name: Optional[str] = None
    language_preference: str = "en"
    timezone: str = "UTC"
    has_active_dispute: bool = False
    opted_out: bool = False


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    email: str
    phone: Optional[str] = None
    company_name: Optional[str] = None
    language_preference: str
    timezone: str
    has_active_dispute: bool
    opted_out: bool
    created_at: datetime


class IngestionEvent(BaseModel):
    source: str = Field(..., description="stripe, razorpay, chargebee, netsuite, mixpanel")
    event_type: str = Field(..., description="invoice.payment_failed, checkout.abandoned, etc.")
    customer_id: str
    customer_name: Optional[str] = "Acme Corp"
    customer_email: Optional[str] = "finance@acme.corp"
    customer_phone: Optional[str] = "+15550192834"
    amount: float
    currency: str = "USD"
    decline_code: Optional[str] = None
    days_overdue: Optional[int] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RiskDetectionResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: str
    source: str
    event_type: str
    risk_type: RiskType
    severity: RiskSeverity
    amount: float
    currency: str
    customer_id: str
    detected_at: datetime
    raw_payload: Dict[str, Any] = Field(default_factory=dict)

