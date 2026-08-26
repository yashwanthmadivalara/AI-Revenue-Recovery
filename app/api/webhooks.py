import uuid
import logging
from typing import Dict, Any
from fastapi import APIRouter, Request, HTTPException, status
from app.ingestion.stripe_webhook import StripeWebhookParser
from app.ingestion.razorpay_webhook import RazorpayWebhookParser
from app.ingestion.chargebee_webhook import ChargebeeWebhookParser
from app.ingestion.erp_invoice_feed import ERPInvoiceFeedParser
from app.agent.graph import recovery_workflow
from app.agent.state import RecoveryAgentState

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks", tags=["Webhooks Ingestion"])


async def process_and_run_agent(ingestion_event) -> Dict[str, Any]:
    """Helper to initialize state and run the LangGraph workflow."""
    case_id = f"case_{uuid.uuid4().hex[:10]}"
    
    initial_state: RecoveryAgentState = {
        "case_id": case_id,
        "customer_id": ingestion_event.customer_id,
        "customer_name": ingestion_event.customer_name or "Valued Customer",
        "customer_email": ingestion_event.customer_email or "user@example.com",
        "customer_phone": ingestion_event.customer_phone,
        "customer_timezone": "UTC",
        "customer_language": "en" if "in" not in ingestion_event.currency.lower() else "hinglish",
        "has_active_dispute": False,
        "has_opted_out": False,
        "ingestion_event": ingestion_event.model_dump(),
        "risk_result": {},
        "risk_type": "",
        "severity": "",
        "amount": ingestion_event.amount,
        "currency": ingestion_event.currency,
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
        "execution_logs": [f"Webhook received from source '{ingestion_event.source}' for {ingestion_event.amount} {ingestion_event.currency}"],
        "error_message": None
    }

    final_state = await recovery_workflow.ainvoke(initial_state)
    return {
        "case_id": case_id,
        "status": final_state.get("case_status"),
        "risk_type": final_state.get("risk_type"),
        "channel": final_state.get("diagnosis", {}).get("recommended_channel") if final_state.get("diagnosis") else None,
        "recovered_amount": final_state.get("recovered_amount", 0.0),
        "audit_sequence_id": final_state.get("audit_sequence_id")
    }


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """Ingests raw Stripe Webhook events."""
    payload = await request.json()
    event = StripeWebhookParser.parse_event(payload)
    if not event:
        return {"received": True, "action": "ignored"}
    
    result = await process_and_run_agent(event)
    return {"received": True, "recovery_pipeline": result}


@router.post("/razorpay")
async def razorpay_webhook(request: Request):
    """Ingests raw Razorpay Webhook events."""
    payload = await request.json()
    event = RazorpayWebhookParser.parse_event(payload)
    if not event:
        return {"received": True, "action": "ignored"}
    
    result = await process_and_run_agent(event)
    return {"received": True, "recovery_pipeline": result}


@router.post("/chargebee")
async def chargebee_webhook(request: Request):
    """Ingests raw Chargebee Webhook events."""
    payload = await request.json()
    event = ChargebeeWebhookParser.parse_event(payload)
    if not event:
        return {"received": True, "action": "ignored"}
    
    result = await process_and_run_agent(event)
    return {"received": True, "recovery_pipeline": result}


@router.post("/erp")
async def erp_invoice_feed(request: Request):
    """Ingests ERP / NetSuite / QuickBooks overdue invoice feeds."""
    payload = await request.json()
    records = payload if isinstance(payload, list) else [payload]
    events = ERPInvoiceFeedParser.parse_batch_feed(records)
    
    results = []
    for ev in events:
        res = await process_and_run_agent(ev)
        results.append(res)

    return {"processed_count": len(results), "cases": results}
