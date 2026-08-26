import logging
from sqlalchemy import select
from app.models.database import AsyncSessionLocal
from app.models.event_models import Customer
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class DisputeChecker:
    """
    Emergency Kill-Switch:
    If a customer has an active chargeback, payment dispute, or legal notice,
    all autonomous recovery communications must IMMEDIATELY halt to comply with regulations.
    """

    @staticmethod
    async def has_active_dispute(customer_id: str, customer_override_flag: bool = False) -> bool:
        if customer_override_flag:
            return True

        if not settings.ENABLE_DISPUTE_KILLSWITCH:
            return False

        async with AsyncSessionLocal() as session:
            stmt = select(Customer.has_active_dispute).where(Customer.id == customer_id)
            result = await session.execute(stmt)
            dispute_flag = result.scalar_one_or_none()
            return bool(dispute_flag)
