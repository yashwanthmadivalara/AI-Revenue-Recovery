import pytest
from app.execution.dispatcher import ActionDispatcher
from app.execution.dynamic_links import DynamicPaymentLinkGenerator
from app.schemas.actions import ActionDispatchPayload
from app.models.event_models import ChannelType


@pytest.mark.asyncio
async def test_email_action_dispatch():
    payload = ActionDispatchPayload(
        case_id="case_exec_test_1",
        channel=ChannelType.EMAIL,
        recipient_email="test@company.com",
        subject="Payment Update Required",
        content="Please update payment details {payment_link}",
        amount=250.0,
        currency="USD"
    )
    result = await ActionDispatcher.dispatch(payload)
    assert result.status == "delivered"
    assert result.idempotency_key is not None
    assert result.external_reference_id is not None
    assert result.cost_usd > 0.0


def test_dynamic_payment_link_generation():
    link_info = DynamicPaymentLinkGenerator.generate_link(
        case_id="case_cart_123",
        amount=1000.0,
        discount_pct=10.0,
        currency="USD"
    )
    assert link_info["final_payable_amount"] == 900.0
    assert "https://pay.recovery-ai.internal/checkout/" in link_info["url"]
    assert "sig=" in link_info["url"]
