from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, func
from app.models.database import AsyncSessionLocal
from app.models.event_models import ContactLog, ChannelType
from app.config import get_settings

settings = get_settings()


class FrequencyLimiter:
    """Enforces contact frequency limits (e.g. max 3 contact attempts per 7 days per customer)."""

    @staticmethod
    async def get_recent_contact_count(customer_id: str, days: int = 7) -> int:
        cutoff = datetime.utcnow() - timedelta(days=days)
        async with AsyncSessionLocal() as session:
            stmt = select(func.count(ContactLog.id)).where(
                ContactLog.customer_id == customer_id,
                ContactLog.contacted_at >= cutoff
            )
            result = await session.execute(stmt)
            count = result.scalar_one_or_none() or 0
            return count

    @classmethod
    async def check_compliance(cls, customer_id: str, channel: str) -> bool:
        # Gateway retries are backend machine-to-machine and don't count towards customer direct message spam
        if channel == ChannelType.GATEWAY_RETRY.value:
            return True

        count = await cls.get_recent_contact_count(customer_id, days=7)
        return count < settings.MAX_CONTACT_ATTEMPTS_PER_WEEK
