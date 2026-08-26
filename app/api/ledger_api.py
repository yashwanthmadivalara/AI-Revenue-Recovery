from typing import List, Dict, Any
from fastapi import APIRouter
from sqlalchemy import select, desc
from app.models.database import AsyncSessionLocal
from app.models.ledger_models import FinancialLedger
from app.schemas.ledger import (
    LedgerEntryResponse,
    FinancialMetricsResponse,
    CohortRecoveryStats
)
from app.ledger.audit_ledger import AuditLedgerService
from app.ledger.roi_engine import ROIEngine
from app.ledger.metrics import MetricsService

router = APIRouter(prefix="/ledger", tags=["Audit & Financial Ledger"])


@router.get("/entries", response_model=List[LedgerEntryResponse])
async def list_ledger_entries(limit: int = 50):
    """Returns the immutable append-only audit trail records."""
    async with AsyncSessionLocal() as session:
        stmt = select(FinancialLedger).order_by(desc(FinancialLedger.sequence_id)).limit(limit)
        records = (await session.execute(stmt)).scalars().all()
        return [LedgerEntryResponse.model_validate(r) for r in records]


@router.get("/metrics", response_model=FinancialMetricsResponse)
async def get_financial_roi_metrics():
    """Calculates aggregate ROI, gross recovered revenue, and net margin."""
    return await ROIEngine.get_summary_metrics()


@router.get("/cohorts", response_model=List[CohortRecoveryStats])
async def get_cohort_analytics():
    """Returns breakdown statistics across failure types and cohorts."""
    return await MetricsService.get_cohort_breakdown()


@router.get("/verify-integrity")
async def verify_cryptographic_chain():
    """
    Verifies the cryptographic SHA-256 hash chain across all historical ledger records
    to prove zero tampering.
    """
    return await AuditLedgerService.verify_chain_integrity()
