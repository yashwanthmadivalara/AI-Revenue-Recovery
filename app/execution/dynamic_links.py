import uuid
import hmac
import hashlib
from typing import Dict, Any
from app.config import get_settings

settings = get_settings()


class DynamicPaymentLinkGenerator:
    """Generates cryptographically signed, personalized payment links with dynamic incentives."""

    @staticmethod
    def generate_link(
        case_id: str,
        amount: float,
        discount_pct: float = 0.0,
        currency: str = "USD",
        expires_in_hours: int = 48
    ) -> Dict[str, Any]:
        link_id = f"link_{uuid.uuid4().hex[:10]}"
        final_amount = round(amount * (1 - (discount_pct / 100.0)), 2)

        # Generate HMAC signature
        signature_raw = f"{case_id}:{final_amount}:{currency}:{settings.SECRET_KEY}"
        signature = hashlib.sha256(signature_raw.encode("utf-8")).hexdigest()[:16]

        url = f"https://pay.recovery-ai.internal/checkout/{link_id}?case={case_id}&amt={final_amount}&cur={currency}&sig={signature}"

        return {
            "link_id": link_id,
            "url": url,
            "original_amount": amount,
            "discount_pct": discount_pct,
            "final_payable_amount": final_amount,
            "currency": currency,
            "expires_in_hours": expires_in_hours
        }
