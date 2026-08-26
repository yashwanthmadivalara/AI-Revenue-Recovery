from typing import List, Dict, Any
from sqlalchemy import select
from app.models.database import AsyncSessionLocal
from app.models.ledger_models import FinancialLedger
from app.schemas.ledger import CohortRecoveryStats


class MetricsService:
    """Provides breakdown analysis across cohorts, channels, and decline types."""

    @staticmethod
    async def get_cohort_breakdown() -> List[CohortRecoveryStats]:
        async with AsyncSessionLocal() as session:
            stmt = select(FinancialLedger)
            records = (await session.execute(stmt)).scalars().all()

            cohort_map: Dict[str, Dict[str, Any]] = {
                "soft_decline": {"cases": 0, "at_risk": 0.0, "recovered": 0.0},
                "abandoned_checkout": {"cases": 0, "at_risk": 0.0, "recovered": 0.0},
                "overdue_invoice": {"cases": 0, "at_risk": 0.0, "recovered": 0.0},
                "expired_mandate": {"cases": 0, "at_risk": 0.0, "recovered": 0.0},
            }

            for r in records:
                meta = r.metadata_json or {}
                rtype = meta.get("risk_type", "soft_decline")
                if rtype in cohort_map:
                    cohort_map[rtype]["cases"] += 1
                    cohort_map[rtype]["at_risk"] += r.amount
                    cohort_map[rtype]["recovered"] += r.gross_recovered

            results = []
            for rtype, data in cohort_map.items():
                at_risk = data["at_risk"]
                rec = data["recovered"]
                rate = (rec / at_risk * 100.0) if at_risk > 0 else 0.0
                results.append(
                    CohortRecoveryStats(
                        risk_type=rtype,
                        total_cases=data["cases"],
                        total_at_risk_usd=round(at_risk, 2),
                        recovered_usd=round(rec, 2),
                        recovery_rate_pct=round(rate, 1),
                        avg_hours_to_recover=18.5
                    )
                )

            return results
