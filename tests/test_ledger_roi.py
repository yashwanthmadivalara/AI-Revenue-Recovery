import pytest
from app.ledger.audit_ledger import AuditLedgerService
from app.ledger.roi_engine import ROIEngine
from app.schemas.ledger import LedgerEntryCreate
from app.models.ledger_models import LedgerEntryType


@pytest.mark.asyncio
async def test_audit_ledger_entry_and_hash_chain():
    # Record entry 1
    entry1 = await AuditLedgerService.record_entry(
        LedgerEntryCreate(
            case_id="case_led_1",
            entry_type=LedgerEntryType.ACTION_DISPATCHED,
            amount=500.0,
            currency="USD",
            gross_recovered=500.0,
            gateway_fee=10.0,
            communication_cost=0.05,
            ai_token_cost=0.002
        )
    )
    assert entry1.sequence_id > 0
    assert entry1.net_recovered > 480.0
    assert len(entry1.current_hash) == 64

    # Record entry 2
    entry2 = await AuditLedgerService.record_entry(
        LedgerEntryCreate(
            case_id="case_led_2",
            entry_type=LedgerEntryType.ACTION_DISPATCHED,
            amount=1000.0,
            currency="USD",
            gross_recovered=1000.0,
            gateway_fee=20.0,
            communication_cost=0.10,
            ai_token_cost=0.004
        )
    )
    assert entry2.previous_hash == entry1.current_hash

    # Verify SHA-256 integrity of the entire chain
    verification = await AuditLedgerService.verify_chain_integrity()
    assert verification["is_valid"] is True
    assert verification["total_records_verified"] >= 2


@pytest.mark.asyncio
async def test_roi_calculation():
    metrics = await ROIEngine.get_summary_metrics()
    assert metrics.total_recovered_revenue >= 0.0
    assert metrics.net_recovered_revenue >= 0.0
