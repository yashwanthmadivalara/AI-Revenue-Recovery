import pytest
from app.guardrails.compliance import ComplianceGuardrails
from app.guardrails.quiet_hours import QuietHoursEnforcer


@pytest.mark.asyncio
async def test_guardrail_dispute_killswitch():
    result = await ComplianceGuardrails.evaluate(
        customer_id="cust_dispute_test",
        customer_timezone="UTC",
        channel="email",
        amount=1000.0,
        has_active_dispute=True
    )
    assert result.is_compliant is False
    assert any(v.rule_name == "DISPUTE_KILLSWITCH" for v in result.violations)


@pytest.mark.asyncio
async def test_guardrail_high_value_gate():
    result = await ComplianceGuardrails.evaluate(
        customer_id="cust_high_val",
        customer_timezone="UTC",
        channel="email",
        amount=8500.0,
        has_active_dispute=False
    )
    assert result.is_compliant is True
    assert result.requires_human_approval is True
    assert any(v.rule_name == "HIGH_VALUE_GATE" for v in result.violations)


def test_quiet_hours_enforcement():
    # Email should never trigger quiet hours
    assert QuietHoursEnforcer.is_within_quiet_hours(timezone_str="America/New_York", channel="email") is False
