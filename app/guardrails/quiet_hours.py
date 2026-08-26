import logging
from datetime import datetime
import zoneinfo
from app.config import get_settings
from app.models.event_models import ChannelType

logger = logging.getLogger(__name__)
settings = get_settings()


class QuietHoursEnforcer:
    """
    Enforces TCPA (US) & TRAI (India) compliance:
    Outbound Voice calls and SMS messages must NOT be dispatched during nighttime quiet hours
    (e.g., 9:00 PM to 8:00 AM in customer's local timezone).
    """

    @staticmethod
    def is_within_quiet_hours(timezone_str: str = "UTC", channel: str = "email") -> bool:
        if not settings.ENABLE_QUIET_HOURS:
            return False

        # Email and automated backend retries can run anytime
        if channel in [ChannelType.EMAIL.value, ChannelType.GATEWAY_RETRY.value, ChannelType.INVOICE_PORTAL.value]:
            return False

        try:
            tz = zoneinfo.ZoneInfo(timezone_str)
            local_time = datetime.now(tz)
            local_hour = local_time.hour

            # Quiet hours: 21:00 (9 PM) to 08:00 (8 AM)
            if local_hour >= 21 or local_hour < 8:
                logger.info(f"Channel {channel} blocked during quiet hours in tz {timezone_str} (Local hour: {local_hour})")
                return True
            return False

        except Exception as ex:
            # If invalid timezone, fallback to UTC check against settings
            utc_hour = datetime.utcnow().hour
            if utc_hour >= settings.QUIET_HOURS_START_UTC or utc_hour < settings.QUIET_HOURS_END_UTC:
                return True
            return False
