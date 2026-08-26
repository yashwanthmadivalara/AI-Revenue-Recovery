import uuid
import hashlib
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy import select, desc
from app.models.database import AsyncSessionLocal
from app.models.ledger_models import FinancialLedger
from app.schemas.ledger import LedgerEntryCreate, LedgerEntryResponse

logger = logging.getLogger(__name__)
GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


class AuditLedgerService:
    """
    Append-Only Cryptographic Financial Audit Ledger.
    Ensures absolute data integrity and auditability by linking every financial record
    via SHA-256 hash chaining.
    """

    @classmethod
    def calculate_hash(
        cls,
        previous_hash: str,
        entry_id: str,
        case_id: str,
        entry_type: str,
        amount: float,
        net_recovered: float,
        timestamp_str: str
    ) -> str:
        clean_net = 0.0 if abs(net_recovered) < 1e-9 else float(net_recovered)
        clean_amt = 0.0 if abs(amount) < 1e-9 else float(amount)
        payload = f"{previous_hash}|{entry_id}|{case_id}|{entry_type}|{clean_amt:.4f}|{clean_net:.4f}|{timestamp_str}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    async def record_entry(cls, entry: LedgerEntryCreate) -> LedgerEntryResponse:
        entry_id = f"led_{uuid.uuid4().hex[:12]}"
        now = datetime.utcnow()
        timestamp_str = now.strftime("%Y-%m-%d %H:%M:%S")

        # Compute net recovered
        total_costs = entry.gateway_fee + entry.communication_cost + entry.ai_token_cost
        net_recovered = entry.gross_recovered - total_costs if entry.gross_recovered > 0 else -total_costs
        if abs(net_recovered) < 1e-9:
            net_recovered = 0.0

        async with AsyncSessionLocal() as session:
            # 1. Fetch latest previous ledger entry to get hash
            stmt = select(FinancialLedger).order_by(desc(FinancialLedger.sequence_id)).limit(1)
            last_record = (await session.execute(stmt)).scalar_one_or_none()

            previous_hash = last_record.current_hash if last_record else GENESIS_HASH

            # 2. Compute current record SHA-256 hash
            current_hash = cls.calculate_hash(
                previous_hash=previous_hash,
                entry_id=entry_id,
                case_id=entry.case_id,
                entry_type=entry.entry_type.value if hasattr(entry.entry_type, "value") else str(entry.entry_type),
                amount=entry.amount,
                net_recovered=net_recovered,
                timestamp_str=timestamp_str
            )

            # 3. Create ORM instance
            ledger_record = FinancialLedger(
                entry_id=entry_id,
                case_id=entry.case_id,
                entry_type=entry.entry_type,
                amount=entry.amount,
                currency=entry.currency,
                gross_recovered=entry.gross_recovered,
                gateway_fee=entry.gateway_fee,
                communication_cost=entry.communication_cost,
                ai_token_cost=entry.ai_token_cost,
                net_recovered=net_recovered,
                previous_hash=previous_hash,
                current_hash=current_hash,
                metadata_json=entry.metadata,
                timestamp=now
            )

            session.add(ledger_record)
            await session.commit()
            await session.refresh(ledger_record)

            logger.info(f"Recorded Audit Ledger Entry Seq #{ledger_record.sequence_id} (Hash: {current_hash[:12]}...)")

            return LedgerEntryResponse.model_validate(ledger_record)

    @classmethod
    async def verify_chain_integrity(cls) -> Dict[str, Any]:
        """Validates the complete SHA-256 cryptographic chain across all historical ledger records."""
        async with AsyncSessionLocal() as session:
            stmt = select(FinancialLedger).order_by(FinancialLedger.sequence_id.asc())
            records = (await session.execute(stmt)).scalars().all()

            expected_prev_hash = GENESIS_HASH
            for idx, r in enumerate(records):
                if r.previous_hash != expected_prev_hash:
                    return {
                        "is_valid": False,
                        "broken_sequence_id": r.sequence_id,
                        "error": f"Previous hash mismatch at sequence {r.sequence_id}"
                    }

                # Verify current hash recomputation
                timestamp_str = r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else ""
                recalculated = cls.calculate_hash(
                    previous_hash=r.previous_hash,
                    entry_id=r.entry_id,
                    case_id=r.case_id,
                    entry_type=r.entry_type.value if hasattr(r.entry_type, "value") else str(r.entry_type),
                    amount=r.amount,
                    net_recovered=r.net_recovered,
                    timestamp_str=timestamp_str
                )

                if recalculated != r.current_hash:
                    return {
                        "is_valid": False,
                        "tampered_sequence_id": r.sequence_id,
                        "error": f"Data tampering detected at sequence {r.sequence_id}"
                    }

                expected_prev_hash = r.current_hash

            return {
                "is_valid": True,
                "total_records_verified": len(records),
                "last_verified_hash": expected_prev_hash
            }
