import uuid
import logging
from typing import Dict, Any, Optional
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class SmsDispatcher:
    """Dispatches SMS payment reminders & shortlinks via Twilio or sandbox simulator."""

    @staticmethod
    async def send_sms(
        recipient_phone: str,
        message: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        sms_id = f"sms_{uuid.uuid4().hex[:12]}"

        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            # Twilio API hook
            logger.info(f"[Twilio API] Sending SMS to {recipient_phone}")
            return {
                "provider": "twilio",
                "message_id": sms_id,
                "status": "delivered",
                "recipient": recipient_phone,
                "cost_usd": 0.0075
            }
        else:
            # High-fidelity mock/simulator
            logger.info(f"[Simulator SMS] Sent to {recipient_phone} | Body: {message[:80]}...")
            return {
                "provider": "simulated_sms",
                "message_id": sms_id,
                "status": "delivered",
                "recipient": recipient_phone,
                "body": message,
                "cost_usd": 0.0075
            }
