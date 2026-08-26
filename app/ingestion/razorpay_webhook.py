import logging
from typing import Dict, Any, Optional
from app.schemas.events import IngestionEvent

logger = logging.getLogger(__name__)


class RazorpayWebhookParser:
    """Parses raw Razorpay webhook payloads into standardized IngestionEvent objects."""

    @staticmethod
    def parse_event(payload: Dict[str, Any]) -> Optional[IngestionEvent]:
        try:
            event_name = payload.get("event", "")
            payload_data = payload.get("payload", {})

            # Handle subscription.charged failure / payment.failed
            if event_name in ["payment.failed", "subscription.halted", "subscription.pending"]:
                payment_entity = payload_data.get("payment", {}).get("entity", {})
                subscription_entity = payload_data.get("subscription", {}).get("entity", {})

                # Razorpay amounts in paise (INR) -> divide by 100
                amount = (payment_entity.get("amount") or subscription_entity.get("paid_count", 0) * 100) / 100.0
                currency = (payment_entity.get("currency") or "INR").upper()
                customer_id = payment_entity.get("customer_id") or payment_entity.get("email") or "cust_rzp_unknown"
                customer_email = payment_entity.get("email", "customer@example.in")
                customer_phone = payment_entity.get("contact", "+919876543210")
                error_code = payment_entity.get("error_code") or payment_entity.get("error_reason", "gateway_error")

                return IngestionEvent(
                    source="razorpay",
                    event_type=event_name,
                    customer_id=customer_id,
                    customer_name=payment_entity.get("notes", {}).get("name", "Razorpay Customer"),
                    customer_email=customer_email,
                    customer_phone=customer_phone,
                    amount=amount,
                    currency=currency,
                    decline_code=error_code,
                    metadata={
                        "payment_id": payment_entity.get("id"),
                        "subscription_id": subscription_entity.get("id"),
                        "error_description": payment_entity.get("error_description"),
                        "method": payment_entity.get("method", "upi"),
                        "bank": payment_entity.get("bank")
                    }
                )

            logger.info(f"Unhandled Razorpay event: {event_name}")
            return None

        except Exception as ex:
            logger.error(f"Error parsing Razorpay webhook: {ex}")
            return None
