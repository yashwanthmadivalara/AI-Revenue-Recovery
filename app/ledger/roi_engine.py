from typing import Dict, Any
from sqlalchemy import select, func
from app.models.database import AsyncSessionLocal
from app.models.ledger_models import FinancialLedger
from app.schemas.ledger import FinancialMetricsResponse


class ROIEngine:
    """
    Attribution & Financial ROI Calculation Engine:
    Measures baseline at-risk revenue, recovered amounts, gross margins,
    AI/Comms operational costs, and net ROI multiplier.
    """

    @staticmethod
    async def get_summary_metrics() -> FinancialMetricsResponse:
        async with AsyncSessionLocal() as session:
            # Sum at-risk amounts
            stmt_risk = select(func.sum(FinancialLedger.amount)).select_from(FinancialLedger)
            total_at_risk = (await session.execute(stmt_risk)).scalar_one_or_none() or 0.0

            # Sum gross recovered
            stmt_rec = select(func.sum(FinancialLedger.gross_recovered)).select_from(FinancialLedger)
            total_gross_recovered = (await session.execute(stmt_rec)).scalar_one_or_none() or 0.0

            # Sum costs
            stmt_fee = select(func.sum(FinancialLedger.gateway_fee)).select_from(FinancialLedger)
            gateway_fees = (await session.execute(stmt_fee)).scalar_one_or_none() or 0.0

            stmt_comm = select(func.sum(FinancialLedger.communication_cost)).select_from(FinancialLedger)
            comm_costs = (await session.execute(stmt_comm)).scalar_one_or_none() or 0.0

            stmt_ai = select(func.sum(FinancialLedger.ai_token_cost)).select_from(FinancialLedger)
            ai_costs = (await session.execute(stmt_ai)).scalar_one_or_none() or 0.0

            total_costs = gateway_fees + comm_costs + ai_costs
            net_recovered = total_gross_recovered - total_costs

            # Total cases
            stmt_cases = select(func.count(func.distinct(FinancialLedger.case_id))).select_from(FinancialLedger)
            total_cases = (await session.execute(stmt_cases)).scalar_one_or_none() or 0

            recovery_rate = (total_gross_recovered / total_at_risk * 100.0) if total_at_risk > 0 else 0.0
            roi_multiple = (net_recovered / total_costs) if total_costs > 0 else 0.0

            return FinancialMetricsResponse(
                total_revenue_at_risk=round(total_at_risk, 2),
                total_recovered_revenue=round(total_gross_recovered, 2),
                total_recovery_costs=round(total_costs, 2),
                net_recovered_revenue=round(net_recovered, 2),
                overall_recovery_rate_pct=round(recovery_rate, 1),
                net_roi_multiple=round(roi_multiple, 2),
                total_cases_processed=total_cases,
                resolved_cases_count=total_cases,
                active_cases_count=0,
                guardrail_blocked_count=0
            )
