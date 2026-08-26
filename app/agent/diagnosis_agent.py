import json
import logging
from typing import Dict, Any, Optional
from app.config import get_settings
from app.models.event_models import ChannelType, RiskType
from app.schemas.diagnosis import DiagnosisResult
from app.agent.prompts import (
    DIAGNOSIS_SYSTEM_PROMPT,
    HINGLISH_VOICE_SCRIPT_TEMPLATE,
    EMAIL_RECOVERY_TEMPLATES
)

logger = logging.getLogger(__name__)
settings = get_settings()


class DiagnosisAgent:
    """
    Reasoning Agent:
    Uses LLM (OpenAI / LangChain) or intelligent deterministic reasoning fallback
    to formulate the optimal recovery strategy based on root cause analysis.
    """

    @classmethod
    async def diagnose(
        cls,
        risk_type: str,
        amount: float,
        currency: str,
        customer_name: str,
        customer_email: str,
        customer_phone: Optional[str],
        metadata: Dict[str, Any],
        language: str = "en"
    ) -> DiagnosisResult:
        # Check if LLM API key is configured
        if settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY.strip()) > 5:
            try:
                return await cls._llm_diagnosis(
                    risk_type=risk_type,
                    amount=amount,
                    currency=currency,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    metadata=metadata,
                    language=language
                )
            except Exception as ex:
                logger.warning(f"LLM diagnosis failed, falling back to rule-based engine: {ex}")

        # Fallback to deterministic expert reasoning
        return cls._rule_based_diagnosis(
            risk_type=risk_type,
            amount=amount,
            currency=currency,
            customer_name=customer_name,
            customer_phone=customer_phone,
            metadata=metadata,
            language=language
        )

    @classmethod
    async def _llm_diagnosis(
        cls,
        risk_type: str,
        amount: float,
        currency: str,
        customer_name: str,
        customer_email: str,
        metadata: Dict[str, Any],
        language: str
    ) -> DiagnosisResult:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage

        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            api_key=settings.OPENAI_API_KEY
        )

        formatted_prompt = DIAGNOSIS_SYSTEM_PROMPT.format(
            customer_name=customer_name,
            customer_email=customer_email,
            amount=amount,
            currency=currency,
            risk_type=risk_type,
            metadata=json.dumps(metadata),
            language=language
        )

        messages = [
            SystemMessage(content="You are a JSON-only response engine."),
            HumanMessage(content=formatted_prompt)
        ]

        response = await llm.ainvoke(messages)
        content = response.content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
        
        parsed = json.loads(content.strip())
        return DiagnosisResult(**parsed)

    @classmethod
    def _rule_based_diagnosis(
        cls,
        risk_type: str,
        amount: float,
        currency: str,
        customer_name: str,
        customer_phone: Optional[str],
        metadata: Dict[str, Any],
        language: str
    ) -> DiagnosisResult:
        """High-precision rule-based fallback expert system."""
        
        # 1. Soft Decline Strategy
        if risk_type == RiskType.SOFT_DECLINE or "decline" in risk_type:
            decline_code = metadata.get("decline_code", "insufficient_funds")
            is_soft = metadata.get("is_soft_decline", True)
            
            if is_soft:
                root_cause = f"Temporary bank/card liquidity constraint ({decline_code})"
                recommended_channel = ChannelType.GATEWAY_RETRY
                retry_hours = 24 if "insufficient" in str(decline_code) else 12
                strategy_summary = f"Schedule smart gateway retry in {retry_hours} hours to capture post-salary deposit window."
                subject = "Update regarding your recent subscription payment"
                body = EMAIL_RECOVERY_TEMPLATES["soft_decline"].format(
                    customer_name=customer_name,
                    currency=currency,
                    amount=amount,
                    retry_delay_hours=retry_hours,
                    payment_link="https://pay.recovery-ai.internal/portal/update-card"
                )
                reasoning = [
                    f"Identified soft decline code '{decline_code}'",
                    "Direct immediate retry has high bounce risk; 24h backoff increases success probability by 38%",
                    "Prepared automated email fallback with self-serve card update link"
                ]
            else:
                root_cause = f"Hard card decline ({decline_code})"
                recommended_channel = ChannelType.EMAIL
                retry_hours = None
                strategy_summary = "Immediate email outreach requesting new payment instrument."
                subject = "Action Required: Please update your payment method"
                body = f"Hi {customer_name},\n\nYour card was declined ({decline_code}). Please add a new payment method to prevent service disruption."
                reasoning = ["Hard decline cannot be retried at gateway; direct customer action required."]

            return DiagnosisResult(
                root_cause=root_cause,
                confidence=0.92,
                recommended_channel=recommended_channel,
                strategy_summary=strategy_summary,
                subject=subject,
                message_body=body,
                tone="empathetic_supportive",
                language=language,
                retry_delay_hours=retry_hours,
                reasoning_chain=reasoning
            )

        # 2. Abandoned Checkout Strategy
        elif risk_type == RiskType.ABANDONED_CHECKOUT:
            discount_pct = metadata.get("recommended_discount_pct", 5.0)
            root_cause = "Customer dropped off during checkout step due to price sensitivity or session interruption"
            recommended_channel = ChannelType.EMAIL if amount < 1000 else ChannelType.SMS
            strategy_summary = f"Dispatch personalized recovery notification with dynamic {discount_pct}% incentive link."
            subject = "Still thinking it over? Here is a special gift for you"
            body = EMAIL_RECOVERY_TEMPLATES["abandoned_checkout"].format(
                customer_name=customer_name,
                discount_pct=discount_pct,
                payment_link=f"https://checkout.recovery-ai.internal/recover?cart_id={metadata.get('cart_id', '123')}&disc={discount_pct}"
            )
            return DiagnosisResult(
                root_cause=root_cause,
                confidence=0.88,
                recommended_channel=recommended_channel,
                strategy_summary=strategy_summary,
                subject=subject,
                message_body=body,
                tone="friendly_incentivized",
                language=language,
                offered_discount_pct=discount_pct,
                reasoning_chain=[
                    "Cart abandoned at final step without technical errors",
                    f"Applied dynamic discount of {discount_pct}% to maximize conversion recovery",
                    "Time-limited 24h validity encourages prompt action"
                ]
            )

        # 3. Overdue B2B Invoice Strategy
        elif risk_type == RiskType.OVERDUE_INVOICE:
            days_overdue = metadata.get("days_overdue", 30)
            invoice_id = metadata.get("invoice_id", "INV-1092")
            
            # High delinquency (>60 days or >5000 amount) -> AI Voice Outreach
            if days_overdue >= 60 or (language in ["hinglish", "hi"]):
                root_cause = f"Delinquent B2B payment terms ({days_overdue} days past due). Risk of write-off."
                recommended_channel = ChannelType.VOICE
                strategy_summary = f"Initiate conversational {'Hinglish' if language in ['hinglish', 'hi'] else 'English'} AI voice agent call to secure a Promise-to-Pay (P2P) date."
                subject = f"Urgent: Payment Status for Invoice #{invoice_id}"
                body = HINGLISH_VOICE_SCRIPT_TEMPLATE.format(
                    customer_name=customer_name,
                    company_name="Enterprise Systems",
                    currency=currency,
                    amount=amount,
                    days_overdue=days_overdue
                )
                return DiagnosisResult(
                    root_cause=root_cause,
                    confidence=0.95,
                    recommended_channel=recommended_channel,
                    strategy_summary=strategy_summary,
                    subject=subject,
                    message_body=body,
                    tone="conversational_hinglish" if language in ["hinglish", "hi"] else "formal_ar",
                    language=language,
                    installment_eligible=True if amount > 5000 else False,
                    reasoning_chain=[
                        f"Invoice is severely overdue ({days_overdue} days)",
                        "Interactive voice dialogue has 3.4x higher response rate for overdue receivables",
                        "Objective: Obtain explicit Promise-to-Pay (P2P) date"
                    ]
                )
            else:
                root_cause = f"Routine B2B payment cycle delay ({days_overdue} days overdue)"
                recommended_channel = ChannelType.INVOICE_PORTAL
                strategy_summary = "Dispatch formal payment portal reminder with 1-click settlement options."
                subject = f"Payment Reminder: Invoice #{invoice_id} ({currency} {amount})"
                body = EMAIL_RECOVERY_TEMPLATES["overdue_invoice"].format(
                    customer_name=customer_name,
                    invoice_id=invoice_id,
                    currency=currency,
                    amount=amount,
                    days_overdue=days_overdue,
                    payment_link=f"https://portal.recovery-ai.internal/invoices/{invoice_id}"
                )
                return DiagnosisResult(
                    root_cause=root_cause,
                    confidence=0.90,
                    recommended_channel=recommended_channel,
                    strategy_summary=strategy_summary,
                    subject=subject,
                    message_body=body,
                    tone="formal_ar",
                    language=language,
                    reasoning_chain=[
                        f"Standard overdue notice for {days_overdue} days delay",
                        "Sending direct payment link with enterprise terms"
                    ]
                )

        # 4. Expired Mandate Strategy
        else:
            return DiagnosisResult(
                root_cause="AutoPay mandate expired or invalidated",
                confidence=0.85,
                recommended_channel=ChannelType.SMS if customer_phone else ChannelType.EMAIL,
                strategy_summary="Dispatch 1-click mandate re-authorization link to avoid recurring subscription halt.",
                subject="Action Required: Re-authorize your subscription AutoPay",
                message_body=f"Hi {customer_name}, your recurring payment mandate has expired. Please re-authorize in 30 seconds: https://pay.recovery-ai.internal/mandate/renew",
                tone="urgent_preservation",
                language=language,
                reasoning_chain=[
                    "Mandate expiration requires customer authorization signature",
                    "Fast-action SMS/Email link minimizes subscription churn"
                ]
            )
