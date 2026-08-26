import pytest
from app.agent.diagnosis_agent import DiagnosisAgent
from app.agent.graph import recovery_workflow
from app.agent.state import RecoveryAgentState
from app.models.event_models import ChannelType, RiskType


@pytest.mark.asyncio
async def test_diagnosis_agent_rule_fallback():
    diag = await DiagnosisAgent.diagnose(
        risk_type="soft_decline",
        amount=400.0,
        currency="USD",
        customer_name="John Doe",
        customer_email="john@example.com",
        customer_phone=None,
        metadata={"decline_code": "insufficient_funds", "is_soft_decline": True}
    )
    assert diag.recommended_channel == ChannelType.GATEWAY_RETRY
    assert diag.retry_delay_hours == 24
    assert diag.confidence > 0.8


@pytest.mark.asyncio
async def test_langgraph_full_workflow_execution():
    initial_state: RecoveryAgentState = {
        "case_id": "test_case_graph_1",
        "customer_id": "cust_graph_1",
        "customer_name": "Tech Corp",
        "customer_email": "billing@techcorp.io",
        "customer_phone": "+14155550199",
        "customer_timezone": "UTC",
        "customer_language": "en",
        "has_active_dispute": False,
        "has_opted_out": False,
        "ingestion_event": {
            "source": "stripe",
            "event_type": "payment_intent.payment_failed",
            "customer_id": "cust_graph_1",
            "amount": 500.0,
            "currency": "USD",
            "decline_code": "insufficient_funds"
        },
        "risk_result": {},
        "risk_type": "",
        "severity": "",
        "amount": 500.0,
        "currency": "USD",
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
        "execution_logs": [],
        "error_message": None
    }

    final_state = await recovery_workflow.ainvoke(initial_state)

    assert final_state.get("risk_type") == "soft_decline"
    assert final_state.get("is_compliant") is True
    assert final_state.get("action_result") is not None
    assert final_state.get("audit_sequence_id") is not None
    assert len(final_state.get("execution_logs", [])) >= 4
