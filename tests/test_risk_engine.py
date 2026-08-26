import pytest
from app.schemas.events import IngestionEvent
from app.risk_engine.detector import RiskDetector
from app.models.event_models import RiskType, RiskSeverity


def test_soft_decline_detection():
    event = IngestionEvent(
        source="stripe",
        event_type="payment_intent.payment_failed",
        customer_id="cust_1",
        amount=350.0,
        currency="USD",
        decline_code="insufficient_funds"
    )
    result = RiskDetector.evaluate_event(event)
    assert result.risk_type == RiskType.SOFT_DECLINE
    assert result.severity == RiskSeverity.MEDIUM
    assert result.raw_payload.get("is_soft_decline") is True


def test_abandoned_checkout_detection():
    event = IngestionEvent(
        source="mixpanel",
        event_type="checkout.abandoned",
        customer_id="cust_cart_1",
        amount=1500.0,
        currency="USD",
        metadata={"cart_items_count": 2, "time_spent_seconds": 90}
    )
    result = RiskDetector.evaluate_event(event)
    assert result.risk_type == RiskType.ABANDONED_CHECKOUT
    assert result.severity == RiskSeverity.HIGH
    assert result.raw_payload.get("recommended_discount_pct") == 5.0


def test_overdue_invoice_aging_detection():
    event = IngestionEvent(
        source="netsuite",
        event_type="invoice.aged_60",
        customer_id="cust_b2b_1",
        amount=12000.0,
        currency="USD",
        days_overdue=75
    )
    result = RiskDetector.evaluate_event(event)
    assert result.risk_type == RiskType.OVERDUE_INVOICE
    assert result.severity == RiskSeverity.CRITICAL
    assert result.raw_payload.get("requires_voice") is True
