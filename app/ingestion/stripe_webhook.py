import logging
from typing import Dict, Any, Optional
from app.schemas.events import IngestionEvent

logger = logging.getLogger(__name__)


class StripeWebhookParser:
    """Parses raw Stripe webhook payloads into standardized IngestionEvent objects."""

    @staticmethod
    def parse_event(payload: Dict[str, Any]) -> Optional[IngestionEvent]:
        try:
            event_type = payload.get("type", "")
            data_obj = payload.get("data", {}).get("object", {})

            if not data_obj:
                return None

            # Handle payment_intent.payment_failed
            if event_type == "payment_intent.payment_failed":
                customer_id = data_obj.get("customer") or data_obj.get("metadata", {}).get("customer_id", "cus_stripe_unknown")
                amount = (data_obj.get("amount", 0)) / 100.0  # Stripe amounts are in cents
                currency = (data_obj.get("currency", "usd")).upper()
                last_payment_error = data_obj.get("last_payment_error", {})
                decline_code = last_payment_error.get("decline_code") or last_payment_error.get("code", "generic_decline")

                customer_email = data_obj.get("receipt_email") or data_obj.get("billing_details", {}).get("email", "customer@example.com")
                customer_name = data_obj.get("billing_details", {}).get("name", "Stripe Customer")

                return IngestionEvent(
                    source="stripe",
                    event_type=event_type,
                    customer_id=customer_id,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    amount=amount,
                    currency=currency,
                    decline_code=decline_code,
                    metadata={
                        "payment_intent_id": data_obj.get("id"),
                        "failure_message": last_payment_error.get("message", "Payment failed"),
                        "payment_method_type": last_payment_error.get("payment_method", {}).get("type", "card")
                    }
                )

            # Handle invoice.payment_failed
            elif event_type == "invoice.payment_failed":
                customer_id = data_obj.get("customer", "cus_stripe_unknown")
                amount = (data_obj.get("amount_due", 0)) / 100.0
                currency = (data_obj.get("currency", "usd")).upper()
                customer_email = data_obj.get("customer_email", "customer@example.com")
                customer_name = data_obj.get("customer_name", "Stripe Subscriber")

                return IngestionEvent(
                    source="stripe",
                    event_type=event_type,
                    customer_id=customer_id,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    amount=amount,
                    currency=currency,
                    decline_code="subscription_invoice_failed",
                    metadata={
                        "invoice_id": data_obj.get("id"),
                        "subscription_id": data_obj.get("subscription"),
                        "attempt_count": data_obj.get("attempt_count", 1),
                        "hosted_invoice_url": data_obj.get("hosted_invoice_url")
                    }
                )

            logger.info(f"Unhandled Stripe event type: {event_type}")
            return None

        except Exception as ex:
            logger.error(f"Error parsing Stripe webhook: {ex}")
            return None
