import enum
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    Enum as SAEnum,
    JSON,
    Boolean,
    Integer,
    ForeignKey,
    Text
)
from sqlalchemy.orm import relationship
from app.models.database import Base


class RiskType(str, enum.Enum):
    SOFT_DECLINE = "soft_decline"
    ABANDONED_CHECKOUT = "abandoned_checkout"
    OVERDUE_INVOICE = "overdue_invoice"
    EXPIRED_MANDATE = "expired_mandate"
    UNKNOWN = "unknown"


class RiskSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CaseStatus(str, enum.Enum):
    OPEN = "open"
    DIAGNOSING = "diagnosing"
    GUARDRAIL_BLOCKED = "guardrail_blocked"
    PENDING_APPROVAL = "pending_approval"
    EXECUTING = "executing"
    RESOLVED = "resolved"
    FAILED = "failed"
    PAUSED_DISPUTE = "paused_dispute"
    PAUSED_PROMISE_TO_PAY = "paused_promise_to_pay"


class ChannelType(str, enum.Enum):
    GATEWAY_RETRY = "gateway_retry"
    EMAIL = "email"
    SMS = "sms"
    VOICE = "voice"
    INVOICE_PORTAL = "invoice_portal"
    MANUAL_ESCALATION = "manual_escalation"


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    company_name = Column(String(255), nullable=True)
    language_preference = Column(String(20), default="en")
    timezone = Column(String(50), default="UTC")
    has_active_dispute = Column(Boolean, default=False)
    opted_out = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recovery_cases = relationship("RecoveryCase", back_populates="customer")
    contact_logs = relationship("ContactLog", back_populates="customer")


class RiskEvent(Base):
    __tablename__ = "risk_events"

    id = Column(String(64), primary_key=True, index=True)
    source = Column(String(50), nullable=False)  # stripe, razorpay, chargebee, netsuite, mixpanel
    event_type = Column(String(100), nullable=False)
    risk_type = Column(SAEnum(RiskType), nullable=False, default=RiskType.UNKNOWN)
    severity = Column(SAEnum(RiskSeverity), nullable=False, default=RiskSeverity.MEDIUM)
    amount = Column(Float, nullable=False, default=0.0)
    currency = Column(String(10), default="USD")
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False)
    raw_payload = Column(JSON, default=dict)
    detected_at = Column(DateTime, default=datetime.utcnow, index=True)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="risk_event", uselist=False)


class RecoveryCase(Base):
    __tablename__ = "recovery_cases"

    id = Column(String(64), primary_key=True, index=True)
    risk_event_id = Column(String(64), ForeignKey("risk_events.id"), nullable=False)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False)
    status = Column(SAEnum(CaseStatus), default=CaseStatus.OPEN, index=True)
    
    # Financial metrics
    original_loss_amount = Column(Float, nullable=False, default=0.0)
    recovered_amount = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")

    # Diagnosis details
    root_cause = Column(String(255), nullable=True)
    strategy_summary = Column(Text, nullable=True)
    recommended_channel = Column(SAEnum(ChannelType), nullable=True)
    diagnosis_metadata = Column(JSON, default=dict)

    # Guardrails details
    is_compliant = Column(Boolean, default=True)
    guardrail_reasons = Column(JSON, default=list)

    # Execution tracking
    requires_human_approval = Column(Boolean, default=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    execution_attempts = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    # Relationships
    customer = relationship("Customer", back_populates="recovery_cases")
    risk_event = relationship("RiskEvent", back_populates="recovery_case")
    actions = relationship("ActionRecord", back_populates="recovery_case")
    promise_to_pays = relationship("PromiseToPay", back_populates="recovery_case")


class ActionRecord(Base):
    __tablename__ = "action_records"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False)
    channel = Column(SAEnum(ChannelType), nullable=False)
    idempotency_key = Column(String(128), unique=True, index=True)
    status = Column(String(50), default="pending")  # pending, dispatched, delivered, failed
    payload = Column(JSON, default=dict)
    response_data = Column(JSON, default=dict)
    cost_usd = Column(Float, default=0.0)
    dispatched_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    recovery_case = relationship("RecoveryCase", back_populates="actions")


class ContactLog(Base):
    __tablename__ = "contact_logs"

    id = Column(String(64), primary_key=True, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id"), nullable=False)
    channel = Column(SAEnum(ChannelType), nullable=False)
    contacted_at = Column(DateTime, default=datetime.utcnow, index=True)

    customer = relationship("Customer", back_populates="contact_logs")


class PromiseToPay(Base):
    __tablename__ = "promise_to_pays"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("recovery_cases.id"), nullable=False)
    promised_date = Column(DateTime, nullable=False)
    promised_amount = Column(Float, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow)
    is_honored = Column(Boolean, default=False)
    notes = Column(Text, nullable=True)

    recovery_case = relationship("RecoveryCase", back_populates="promise_to_pays")
