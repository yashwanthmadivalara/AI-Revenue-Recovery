import uuid
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import select, desc
from app.models.database import AsyncSessionLocal
from app.models.event_models import ActionRecord
from app.models.ledger_models import FinancialLedger
from app.schemas.events import IngestionEvent
from app.agent.graph import recovery_workflow
from app.agent.state import RecoveryAgentState

router = APIRouter(prefix="/recovery", tags=["Recovery Operations"])


@router.post("/trigger")
async def trigger_recovery_pipeline(event: IngestionEvent):
    """
    Manually triggers the end-to-end AI Revenue Recovery workflow
    (Ingestion -> Risk Detection -> Diagnosis -> Guardrails -> Action -> Ledger).
    """
    case_id = f"case_{uuid.uuid4().hex[:10]}"

    initial_state: RecoveryAgentState = {
        "case_id": case_id,
        "customer_id": event.customer_id,
        "customer_name": event.customer_name or "Client",
        "customer_email": event.customer_email or "client@example.com",
        "customer_phone": event.customer_phone,
        "customer_timezone": "UTC",
        "customer_language": "hinglish" if "in" in event.currency.lower() else "en",
        "has_active_dispute": False,
        "has_opted_out": False,
        "ingestion_event": event.model_dump(),
        "risk_result": {},
        "risk_type": "",
        "severity": "",
        "amount": event.amount,
        "currency": event.currency,
        "diagnosis": None,
        "guardrail_result": None,
        "is_compliant": True,
        "requires_human_approval": False,
        "is_approved": False,
        "action_result": None,
        "case_status": "open",
        "cost_usd": 0.0,
        "recovered_amount": 0.0,
        "audit_sequence_id": None,
        "execution_logs": [f"Pipeline triggered manually for {event.amount} {event.currency}"],
        "error_message": None
    }

    final_state = await recovery_workflow.ainvoke(initial_state)

    return {
        "case_id": case_id,
        "status": final_state.get("case_status"),
        "risk_type": final_state.get("risk_type"),
        "severity": final_state.get("severity"),
        "amount": final_state.get("amount"),
        "currency": final_state.get("currency"),
        "diagnosis": final_state.get("diagnosis"),
        "guardrail_result": final_state.get("guardrail_result"),
        "action_result": final_state.get("action_result"),
        "recovered_amount": final_state.get("recovered_amount", 0.0),
        "audit_sequence_id": final_state.get("audit_sequence_id"),
        "execution_logs": final_state.get("execution_logs", [])
    }


@router.get("/actions")
async def list_action_records(limit: int = 50):
    """Retrieves recent bounded execution tool dispatch logs."""
    async with AsyncSessionLocal() as session:
        stmt = select(ActionRecord).order_by(desc(ActionRecord.dispatched_at)).limit(limit)
        records = (await session.execute(stmt)).scalars().all()
        return [
            {
                "id": r.id,
                "case_id": r.case_id,
                "channel": r.channel.value if hasattr(r.channel, "value") else str(r.channel),
                "status": r.status,
                "cost_usd": r.cost_usd,
                "dispatched_at": r.dispatched_at.isoformat() if r.dispatched_at else None,
                "details": r.response_data
            }
            for r in records
        ]
