from fastapi import APIRouter
from app.config import get_settings
from app.schemas.guardrails import PolicyConfig, GuardrailCheckRequest, GuardrailEvaluationResult
from app.guardrails.compliance import ComplianceGuardrails

router = APIRouter(prefix="/guardrails", tags=["Compliance & Guardrails"])
settings = get_settings()


@router.get("/config", response_model=PolicyConfig)
async def get_policy_config():
    """Returns active compliance guardrail rules and thresholds."""
    return PolicyConfig(
        max_contact_attempts_per_week=settings.MAX_CONTACT_ATTEMPTS_PER_WEEK,
        enable_dispute_killswitch=settings.ENABLE_DISPUTE_KILLSWITCH,
        enable_quiet_hours=settings.ENABLE_QUIET_HOURS,
        quiet_hours_start_utc=settings.QUIET_HOURS_START_UTC,
        quiet_hours_end_utc=settings.QUIET_HOURS_END_UTC,
        high_value_threshold_usd=settings.HIGH_VALUE_THRESHOLD_USD,
        promise_to_pay_grace_days=settings.PROMISE_TO_PAY_GRACE_DAYS
    )


@router.post("/evaluate", response_model=GuardrailEvaluationResult)
async def evaluate_guardrails(req: GuardrailCheckRequest):
    """Direct testing endpoint for evaluating policy compliance for a customer/channel."""
    return await ComplianceGuardrails.evaluate(
        customer_id=req.customer_id,
        customer_timezone=req.timezone or "UTC",
        channel=req.channel,
        amount=req.amount
    )
