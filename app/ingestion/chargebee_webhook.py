import logging
from typing import Dict, Any, Optional
from app.schemas.events import IngestionEvent

logger = logging.getLogger(__name__)


class ChargebeeWebhookParser:
    """Parses raw Chargebee webhook payloads into standardized IngestionEvent objects."""

    @staticmethod
    def parse_event(payload: Dict[str, Any]) -> Optional[IngestionEvent]:
        try:
            event_type = payload.get("event_type", "")
            content = payload.get("content", {})
            invoice = content.get("invoice", {})
            customer = content.get("customer", {})
            transaction = content.get("transaction", {})

            if "payment_failed" in event_type or "dunning" in event_type or "subscription_cancelled" in event_type:
                amount = (invoice.get("amount_due", 0) or transaction.get("amount", 0)) / 100.0
                currency = (invoice.get("currency_code") or "USD").upper()
                customer_id = customer.get("id") or invoice.get("customer_id", "cb_customer_unknown")

                return IngestionEvent(
                    source="chargebee",
                    event_type=event_type,
                    customer_id=customer_id,
                    customer_name=f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Chargebee Client",
                    customer_email=customer.get("email", "client@chargebee.com"),
                    customer_phone=customer.get("phone"),
                    amount=amount,
                    currency=currency,
                    decline_code=transaction.get("error_code", "chargebee_decline"),
                    metadata={
                        "invoice_id": invoice.get("id"),
                        "subscription_id": invoice.get("subscription_id"),
                        "dunning_status": invoice.get("dunning_status"),
                        "error_text": transaction.get("error_text")
                    }
                )

            return None
        except Exception as ex:
            logger.error(f"Error parsing Chargebee webhook: {ex}")
            return None
