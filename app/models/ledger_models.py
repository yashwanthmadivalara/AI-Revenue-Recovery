import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    Enum as SAEnum,
    JSON,
    Integer,
    Text
)
from app.models.database import Base


class LedgerEntryType(str, enum.Enum):
    RISK_DETECTED = "risk_detected"
    ACTION_DISPATCHED = "action_dispatched"
    COST_INCURRED = "cost_incurred"
    PAYMENT_RECOVERED = "payment_recovered"
    PROMISE_REGISTERED = "promise_registered"
    CASE_CLOSED = "case_closed"


class FinancialLedger(Base):
    """
    Cryptographically chained, append-only financial audit ledger
    for all revenue recovery actions, costs, and recoveries.
    """
    __tablename__ = "financial_ledger"

    sequence_id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(64), unique=True, index=True, nullable=False)
    case_id = Column(String(64), index=True, nullable=False)
    entry_type = Column(SAEnum(LedgerEntryType), nullable=False)
    
    # Financial fields
    amount = Column(Float, default=0.0)
    currency = Column(String(10), default="USD")
    
    # Attribution / Cost Breakdowns
    gross_recovered = Column(Float, default=0.0)
    gateway_fee = Column(Float, default=0.0)
    communication_cost = Column(Float, default=0.0)
    ai_token_cost = Column(Float, default=0.0)
    net_recovered = Column(Float, default=0.0)

    # Immutability & Audit Hash Chain
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, unique=True)
    
    # Metadata
    metadata_json = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
