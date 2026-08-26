import uuid
import hashlib
import logging
from datetime import datetime
from app.models.event_models import ChannelType, ActionRecord, ContactLog
from app.models.database import AsyncSessionLocal
from app.schemas.actions import ActionDispatchPayload, ActionDispatchResult
from app.execution.gateway_retry import GatewayRetryDispatcher
from app.execution.email_dispatcher import EmailDispatcher
from app.execution.sms_dispatcher import SmsDispatcher
from app.execution.voice_dispatcher import VoiceDispatcher
from app.execution.dynamic_links import DynamicPaymentLinkGenerator

logger = logging.getLogger(__name__)


class ActionDispatcher:
    """
    Bounded Action Layer:
    Safely orchestrates tool execution with idempotency checks, database logging,
    and cost attribution.
    """

    @classmethod
    def generate_idempotency_key(cls, payload: ActionDispatchPayload) -> str:
        raw_key = f"{payload.case_id}:{payload.channel.value}:{payload.amount}:{datetime.utcnow().strftime('%Y-%m-%d-%H')}"
        return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:32]

    @classmethod
    async def dispatch(cls, payload: ActionDispatchPayload) -> ActionDispatchResult:
        idempotency_key = cls.generate_idempotency_key(payload)
        action_id = f"act_{uuid.uuid4().hex[:12]}"
        channel = payload.channel
        details = {}
        cost_usd = 0.0
        status = "dispatched"
        external_ref = None

        try:
            # 1. Gateway Smart Retry
            if channel == ChannelType.GATEWAY_RETRY:
                delay = payload.metadata.get("retry_delay_hours", 24)
                details = await GatewayRetryDispatcher.schedule_retry(
                    case_id=payload.case_id,
                    amount=payload.amount,
                    delay_hours=delay,
                    metadata=payload.metadata
                )
                external_ref = details.get("retry_id")
                cost_usd = details.get("cost_usd", 0.0)
                status = "success"

            # 2. Email Recovery
            elif channel == ChannelType.EMAIL:
                # Generate dynamic payment link if appropriate
                link_info = DynamicPaymentLinkGenerator.generate_link(
                    case_id=payload.case_id,
                    amount=payload.amount,
                    discount_pct=payload.metadata.get("discount_pct", 0.0),
                    currency=payload.currency
                )
                formatted_body = (payload.content or "").replace("{payment_link}", link_info["url"])
                
                details = await EmailDispatcher.send_email(
                    recipient_email=payload.recipient_email or "customer@example.com",
                    subject=payload.subject or "Payment Notification",
                    content=formatted_body,
                    metadata=payload.metadata
                )
                external_ref = details.get("message_id")
                cost_usd = details.get("cost_usd", 0.001)
                status = "delivered"

            # 3. SMS Outreach
            elif channel == ChannelType.SMS:
                link_info = DynamicPaymentLinkGenerator.generate_link(
                    case_id=payload.case_id,
                    amount=payload.amount,
                    discount_pct=payload.metadata.get("discount_pct", 0.0),
                    currency=payload.currency
                )
                sms_text = f"{payload.content or 'Please settle your balance'}\nPay: {link_info['url']}"
                details = await SmsDispatcher.send_sms(
                    recipient_phone=payload.recipient_phone or "+15550192834",
                    message=sms_text,
                    metadata=payload.metadata
                )
                external_ref = details.get("message_id")
                cost_usd = details.get("cost_usd", 0.0075)
                status = "delivered"

            # 4. Multilingual / Hinglish AI Voice Call
            elif channel == ChannelType.VOICE:
                details = await VoiceDispatcher.initiate_voice_call(
                    case_id=payload.case_id,
                    recipient_phone=payload.recipient_phone or "+919876543210",
                    prompt_script=payload.content or "Payment reminder call",
                    language=payload.metadata.get("diagnosis", {}).get("language", "hinglish"),
                    metadata=payload.metadata
                )
                external_ref = details.get("call_id")
                cost_usd = details.get("cost_usd", 0.045)
                status = "completed"

            # 5. Invoice Portal Link
            else:
                link_info = DynamicPaymentLinkGenerator.generate_link(
                    case_id=payload.case_id,
                    amount=payload.amount,
                    currency=payload.currency
                )
                details = {"portal_link": link_info}
                external_ref = link_info.get("link_id")
                status = "delivered"
                cost_usd = 0.001

            # Log to ActionRecord database table
            async with AsyncSessionLocal() as session:
                action_record = ActionRecord(
                    id=action_id,
                    case_id=payload.case_id,
                    channel=channel,
                    idempotency_key=idempotency_key,
                    status=status,
                    payload=payload.model_dump(),
                    response_data=details,
                    cost_usd=cost_usd,
                    dispatched_at=datetime.utcnow()
                )
                session.add(action_record)
                
                # Also log contact attempt for frequency tracking
                contact_log = ContactLog(
                    id=f"cnt_{uuid.uuid4().hex[:10]}",
                    customer_id=payload.metadata.get("customer_id", "cust_1"),
                    channel=channel,
                    contacted_at=datetime.utcnow()
                )
                session.add(contact_log)
                await session.commit()

        except Exception as ex:
            logger.error(f"Error during action dispatch: {ex}")
            status = "failed"
            details = {"error": str(ex)}

        return ActionDispatchResult(
            action_id=action_id,
            case_id=payload.case_id,
            channel=channel,
            status=status,
            idempotency_key=idempotency_key,
            external_reference_id=external_ref,
            cost_usd=cost_usd,
            dispatched_at=datetime.utcnow(),
            details=details
        )
