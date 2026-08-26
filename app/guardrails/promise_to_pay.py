import logging
from datetime import datetime, timedelta
from sqlalchemy import select
from app.models.database import AsyncSessionLocal
from app.models.event_models import PromiseToPay, RecoveryCase
from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PromiseToPayManager:
    """
    Manages Promise-to-Pay (P2P) agreements:
    When a customer commits to pay by a specific date, autonomous recovery outreach is frozen
    until that date + grace period expires.
    """

    @staticmethod
    async def has_active_promise(customer_id: str) -> bool:
        grace_delta = timedelta(days=settings.PROMISE_TO_PAY_GRACE_DAYS)
        now = datetime.utcnow()

        async with AsyncSessionLocal() as session:
            # Join with recovery cases for customer
            stmt = select(PromiseToPay).join(RecoveryCase).where(
                RecoveryCase.customer_id == customer_id,
                PromiseToPay.is_honored == False
            )
            result = await session.execute(stmt)
            promises = result.scalars().all()

            for p in promises:
                # Active if promised date + grace period has not yet passed
                if p.promised_date + grace_delta >= now:
                    logger.info(f"Customer {customer_id} has active Promise-to-Pay until {p.promised_date}")
                    return True

            return False
