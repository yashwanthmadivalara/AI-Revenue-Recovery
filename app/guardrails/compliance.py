import logging
from datetime import datetime
from typing import Optional, List
from app.schemas.guardrails import GuardrailEvaluationResult, GuardrailViolation
from app.guardrails.frequency_limiter import FrequencyLimiter
from app.guardrails.dispute_checker import DisputeChecker
from app.guardrails.promise_to_pay import PromiseToPayManager
from app.guardrails.quiet_hours import QuietHoursEnforcer
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ComplianceGuardrails:
    """
    Unified Policy & Compliance Guardrails Engine:
    Validates every candidate recovery action against legal, ethical, and business rules before dispatch.
    """

    @classmethod
    async def evaluate(
        cls,
        customer_id: str,
        customer_timezone: str = "UTC",
        channel: str = "email",
        amount: float = 0.0,
        has_active_dispute: bool = False,
        has_opted_out: bool = False
    ) -> GuardrailEvaluationResult:
        violations: List[GuardrailViolation] = []
        requires_human_approval = False

        # 1. Check Opt-out / Do Not Contact
        if has_opted_out:
            violations.append(GuardrailViolation(
                rule_name="OPT_OUT_BLOCK",
                severity="block",
                message="Customer has opted out of automated communications."
            ))

        # 2. Check Active Dispute / Chargeback Kill-Switch
        active_dispute = await DisputeChecker.has_active_dispute(
            customer_id=customer_id,
            customer_override_flag=has_active_dispute
        )
        if active_dispute:
            violations.append(GuardrailViolation(
                rule_name="DISPUTE_KILLSWITCH",
                severity="block",
                message="Active payment dispute or chargeback detected. Outreach halted immediately."
            ))

        # 3. Check Promise-to-Pay Cooldown
        active_promise = await PromiseToPayManager.has_active_promise(customer_id=customer_id)
        if active_promise:
            violations.append(GuardrailViolation(
                rule_name="PROMISE_TO_PAY_COOLDOWN",
                severity="block",
                message="Customer has an active, unexpired Promise-to-Pay commitment. Outreach paused."
            ))

        # 4. Check Frequency Cap (Max attempts per week)
        recent_contacts = await FrequencyLimiter.get_recent_contact_count(customer_id)
        frequency_ok = await FrequencyLimiter.check_compliance(customer_id, channel)
        if not frequency_ok:
            violations.append(GuardrailViolation(
                rule_name="FREQUENCY_LIMIT_EXCEEDED",
                severity="block",
                message=f"Contact cap reached ({recent_contacts}/{settings.MAX_CONTACT_ATTEMPTS_PER_WEEK} attempts in last 7 days)."
            ))

        # 5. Check Quiet Hours (Voice & SMS)
        in_quiet_hours = QuietHoursEnforcer.is_within_quiet_hours(
            timezone_str=customer_timezone,
            channel=channel
        )
        if in_quiet_hours:
            violations.append(GuardrailViolation(
                rule_name="QUIET_HOURS_RESTRICTION",
                severity="block",
                message=f"Outreach blocked during local quiet hours for timezone '{customer_timezone}'."
            ))

        # 6. High-Value Human-In-The-Loop Check
        if amount >= settings.HIGH_VALUE_THRESHOLD_USD:
            requires_human_approval = True
            violations.append(GuardrailViolation(
                rule_name="HIGH_VALUE_GATE",
                severity="warning",
                message=f"High-value recovery (${amount:.2f} >= ${settings.HIGH_VALUE_THRESHOLD_USD:.2f}). Flagged for human review."
            ))

        is_compliant = not any(v.severity == "block" for v in violations)

        return GuardrailEvaluationResult(
            is_compliant=is_compliant,
            requires_human_approval=requires_human_approval,
            violations=violations,
            evaluated_at=datetime.utcnow(),
            contact_count_last_7_days=recent_contacts,
            has_active_dispute=active_dispute,
            active_promise_to_pay=active_promise,
            is_quiet_hours=in_quiet_hours
        )
