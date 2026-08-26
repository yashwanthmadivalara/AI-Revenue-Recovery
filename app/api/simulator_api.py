import uuid
from typing import Dict, Any, List
from fastapi import APIRouter
from app.schemas.events import IngestionEvent
from app.agent.graph import recovery_workflow
from app.agent.state import RecoveryAgentState

router = APIRouter(prefix="/simulator", tags=["Demo & Scenario Simulator"])

SCENARIOS = {
    "soft_decline": {
        "source": "stripe",
        "event_type": "payment_intent.payment_failed",
        "customer_id": "cust_stripe_88",
        "customer_name": "Sarah Jenkins",
        "customer_email": "sarah.j@acmecloud.io",
        "customer_phone": "+14155552671",
        "amount": 450.00,
        "currency": "USD",
        "decline_code": "insufficient_funds",
        "metadata": {"subscription_tier": "Pro Annual", "retry_count": 1}
    },
    "abandoned_checkout": {
        "source": "mixpanel",
        "event_type": "checkout.abandoned",
        "customer_id": "cust_cart_99",
        "customer_name": "Marcus Vance",
        "customer_email": "m.vance@designpro.com",
        "customer_phone": "+14155559812",
        "amount": 1200.00,
        "currency": "USD",
        "metadata": {"cart_items_count": 3, "time_spent_seconds": 180}
    },
    "overdue_b2b_hinglish": {
        "source": "netsuite",
        "event_type": "invoice.aged_60",
        "customer_id": "cust_b2b_india_42",
        "customer_name": "Rajesh Sharma",
        "customer_email": "rajesh@sharmalogistics.in",
        "customer_phone": "+919876543210",
        "amount": 4200.00,
        "currency": "INR",
        "days_overdue": 65,
        "metadata": {"invoice_id": "INV-IN-8891", "terms": "Net 30"}
    },
    "active_dispute_blocked": {
        "source": "stripe",
        "event_type": "payment_intent.payment_failed",
        "customer_id": "cust_dispute_12",
        "customer_name": "Disputed Client",
        "customer_email": "legal@disputed.com",
        "customer_phone": "+14155550000",
        "amount": 1500.00,
        "currency": "USD",
        "decline_code": "insufficient_funds",
        "metadata": {"has_active_dispute": True}
    }
}


@router.get("/scenarios")
async def list_scenarios():
    """Returns available simulation blueprints."""
    return list(SCENARIOS.keys())


@router.post("/run/{scenario_key}")
async def run_scenario(scenario_key: str):
    """Executes a full end-to-end simulated scenario through the LangGraph recovery workflow."""
    if scenario_key not in SCENARIOS:
        return {"error": f"Scenario '{scenario_key}' not found. Choose from {list(SCENARIOS.keys())}"}

    data = SCENARIOS[scenario_key]
    event = IngestionEvent(
        source=data["source"],
        event_type=data["event_type"],
        customer_id=data["customer_id"],
        customer_name=data["customer_name"],
        customer_email=data["customer_email"],
        customer_phone=data.get("customer_phone"),
        amount=data["amount"],
        currency=data["currency"],
        decline_code=data.get("decline_code"),
        days_overdue=data.get("days_overdue"),
        metadata=data.get("metadata", {})
    )

    case_id = f"sim_{scenario_key}_{uuid.uuid4().hex[:6]}"
    is_disputed = data.get("metadata", {}).get("has_active_dispute", False)

    initial_state: RecoveryAgentState = {
        "case_id": case_id,
        "customer_id": event.customer_id,
        "customer_name": event.customer_name or "Valued Client",
        "customer_email": event.customer_email or "client@example.com",
        "customer_phone": event.customer_phone,
        "customer_timezone": "Asia/Kolkata" if "in" in event.currency.lower() else "UTC",
        "customer_language": "hinglish" if "in" in event.currency.lower() else "en",
        "has_active_dispute": is_disputed,
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
        "execution_logs": [f"Starting Scenario [{scenario_key}] with amount {event.amount} {event.currency}"],
        "error_message": None
    }

    final_state = await recovery_workflow.ainvoke(initial_state)

    return {
        "scenario": scenario_key,
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
