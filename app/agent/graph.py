import logging
import uuid
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, END
from app.agent.state import RecoveryAgentState
from app.agent.diagnosis_agent import DiagnosisAgent
from app.risk_engine.detector import RiskDetector
from app.schemas.events import IngestionEvent
from app.models.event_models import CaseStatus, ChannelType

logger = logging.getLogger(__name__)


async def node_detect_risk(state: RecoveryAgentState) -> Dict[str, Any]:
    """Node 1: Evaluates raw ingestion event and produces risk classification."""
    logs = list(state.get("execution_logs", []))
    logs.append("Executing Node: detect_risk")

    ingestion_dict = state.get("ingestion_event", {})
    event = IngestionEvent(**ingestion_dict)
    
    risk_result = RiskDetector.evaluate_event(event)
    
    logs.append(f"Risk Classified: [{risk_result.risk_type}] Severity [{risk_result.severity}]")

    return {
        "risk_result": risk_result.model_dump(),
        "risk_type": risk_result.risk_type.value,
        "severity": risk_result.severity.value,
        "amount": risk_result.amount,
        "currency": risk_result.currency,
        "execution_logs": logs
    }


async def node_diagnose(state: RecoveryAgentState) -> Dict[str, Any]:
    """Node 2: Reasoning & strategy selection via LLM or rule-based engine."""
    logs = list(state.get("execution_logs", []))
    logs.append("Executing Node: diagnose_root_cause")

    risk_result = state.get("risk_result", {})
    raw_payload = risk_result.get("raw_payload", {})

    diagnosis = await DiagnosisAgent.diagnose(
        risk_type=state.get("risk_type", "soft_decline"),
        amount=state.get("amount", 0.0),
        currency=state.get("currency", "USD"),
        customer_name=state.get("customer_name", "Customer"),
        customer_email=state.get("customer_email", "user@example.com"),
        customer_phone=state.get("customer_phone"),
        metadata=raw_payload,
        language=state.get("customer_language", "en")
    )

    logs.append(f"Strategy Formulated: Channel [{diagnosis.recommended_channel.value}] | Root Cause: {diagnosis.root_cause}")

    return {
        "diagnosis": diagnosis.model_dump(),
        "execution_logs": logs
    }


async def node_evaluate_guardrails(state: RecoveryAgentState) -> Dict[str, Any]:
    """Node 3: Enforces compliance, contact caps, quiet hours, and active dispute kill-switch."""
    from app.guardrails.compliance import ComplianceGuardrails
    
    logs = list(state.get("execution_logs", []))
    logs.append("Executing Node: evaluate_guardrails")

    diagnosis = state.get("diagnosis", {})
    channel = diagnosis.get("recommended_channel", "email")

    evaluation = await ComplianceGuardrails.evaluate(
        customer_id=state.get("customer_id", "cust_1"),
        customer_timezone=state.get("customer_timezone", "UTC"),
        channel=channel,
        amount=state.get("amount", 0.0),
        has_active_dispute=state.get("has_active_dispute", False),
        has_opted_out=state.get("has_opted_out", False)
    )

    if evaluation.is_compliant:
        logs.append("Guardrails Passed: Full compliance verified.")
    else:
        violations_str = ", ".join([v.message for v in evaluation.violations])
        logs.append(f"Guardrails BLOCKED: {violations_str}")

    return {
        "guardrail_result": evaluation.model_dump(),
        "is_compliant": evaluation.is_compliant,
        "requires_human_approval": evaluation.requires_human_approval,
        "execution_logs": logs
    }


async def node_execute_action(state: RecoveryAgentState) -> Dict[str, Any]:
    """Node 4: Bounded tool dispatch across Gateway, Email, SMS, Voice, or Payment Links."""
    from app.execution.dispatcher import ActionDispatcher
    from app.schemas.actions import ActionDispatchPayload

    logs = list(state.get("execution_logs", []))
    logs.append("Executing Node: execute_action")

    diagnosis = state.get("diagnosis", {})
    channel = diagnosis.get("recommended_channel", ChannelType.EMAIL.value)

    payload = ActionDispatchPayload(
        case_id=state.get("case_id", f"case_{uuid.uuid4().hex[:8]}"),
        channel=ChannelType(channel),
        recipient_email=state.get("customer_email"),
        recipient_phone=state.get("customer_phone"),
        subject=diagnosis.get("subject"),
        content=diagnosis.get("message_body"),
        amount=state.get("amount", 0.0),
        currency=state.get("currency", "USD"),
        metadata={
            "diagnosis": diagnosis,
            "retry_delay_hours": diagnosis.get("retry_delay_hours"),
            "discount_pct": diagnosis.get("offered_discount_pct", 0.0)
        }
    )

    result = await ActionDispatcher.dispatch(payload)
    logs.append(f"Action Dispatched [{channel}]: Status [{result.status}] Ref [{result.external_reference_id}] Cost [${result.cost_usd:.4f}]")

    # Simulate realistic recovery probability based on channel & status
    simulated_recovered_amount = 0.0
    if result.status in ["success", "simulated", "delivered"]:
        # Gateway retries and prompt responses recover the full amount in successful simulations
        simulated_recovered_amount = state.get("amount", 0.0)

    return {
        "action_result": result.model_dump(),
        "cost_usd": result.cost_usd,
        "recovered_amount": simulated_recovered_amount,
        "case_status": CaseStatus.RESOLVED.value if simulated_recovered_amount > 0 else CaseStatus.EXECUTING.value,
        "execution_logs": logs
    }


async def node_record_ledger(state: RecoveryAgentState) -> Dict[str, Any]:
    """Node 5: Cryptographic append-only audit trail logging & ROI ledger entry."""
    from app.ledger.audit_ledger import AuditLedgerService
    from app.schemas.ledger import LedgerEntryCreate
    from app.models.ledger_models import LedgerEntryType

    logs = list(state.get("execution_logs", []))
    logs.append("Executing Node: record_ledger")

    case_id = state.get("case_id", "case_default")
    recovered = state.get("recovered_amount", 0.0)
    cost = state.get("cost_usd", 0.0)
    ai_cost = 0.002  # estimated AI inference cost

    # 1. Record Action & Cost Ledger Entry
    entry = await AuditLedgerService.record_entry(
        LedgerEntryCreate(
            case_id=case_id,
            entry_type=LedgerEntryType.ACTION_DISPATCHED,
            amount=state.get("amount", 0.0),
            currency=state.get("currency", "USD"),
            gross_recovered=recovered,
            gateway_fee=recovered * 0.02 if recovered > 0 else 0.0,
            communication_cost=cost,
            ai_token_cost=ai_cost,
            metadata={
                "risk_type": state.get("risk_type"),
                "channel": state.get("diagnosis", {}).get("recommended_channel"),
                "status": state.get("case_status")
            }
        )
    )

    logs.append(f"Financial Ledger Updated: Seq #{entry.sequence_id} Hash [{entry.current_hash[:12]}...] Net Recovered [${entry.net_recovered:.2f}]")

    return {
        "audit_sequence_id": entry.sequence_id,
        "execution_logs": logs
    }


async def node_block_and_log(state: RecoveryAgentState) -> Dict[str, Any]:
    """Node for handling non-compliant or guardrail-blocked cases."""
    from app.ledger.audit_ledger import AuditLedgerService
    from app.schemas.ledger import LedgerEntryCreate
    from app.models.ledger_models import LedgerEntryType

    logs = list(state.get("execution_logs", []))
    logs.append("Case Blocked by Policy Guardrails. Halting outreach.")

    case_id = state.get("case_id", "case_default")
    guardrail = state.get("guardrail_result", {})

    status = CaseStatus.PAUSED_DISPUTE.value if state.get("has_active_dispute") else CaseStatus.GUARDRAIL_BLOCKED.value

    entry = await AuditLedgerService.record_entry(
        LedgerEntryCreate(
            case_id=case_id,
            entry_type=LedgerEntryType.CASE_CLOSED,
            amount=state.get("amount", 0.0),
            currency=state.get("currency", "USD"),
            metadata={
                "blocked_reason": guardrail.get("violations", []),
                "status": status
            }
        )
    )

    return {
        "case_status": status,
        "audit_sequence_id": entry.sequence_id,
        "execution_logs": logs
    }


def route_guardrails(state: RecoveryAgentState) -> Literal["execute_action", "block_and_log"]:
    """Conditional Edge: Routes to execution if compliant, or block handler if violated."""
    if state.get("is_compliant", True):
        return "execute_action"
    return "block_and_log"


def create_recovery_graph() -> StateGraph:
    """Builds and compiles the complete LangGraph state machine."""
    workflow = StateGraph(RecoveryAgentState)

    # Add Nodes
    workflow.add_node("detect_risk", node_detect_risk)
    workflow.add_node("diagnose_root_cause", node_diagnose)
    workflow.add_node("evaluate_guardrails", node_evaluate_guardrails)
    workflow.add_node("execute_action", node_execute_action)
    workflow.add_node("record_ledger", node_record_ledger)
    workflow.add_node("block_and_log", node_block_and_log)

    # Set Entry Point
    workflow.set_entry_point("detect_risk")

    # Add Edges
    workflow.add_edge("detect_risk", "diagnose_root_cause")
    workflow.add_edge("diagnose_root_cause", "evaluate_guardrails")
    
    # Conditional edge from guardrail check
    workflow.add_conditional_edges(
        "evaluate_guardrails",
        route_guardrails,
        {
            "execute_action": "execute_action",
            "block_and_log": "block_and_log"
        }
    )

    workflow.add_edge("execute_action", "record_ledger")
    workflow.add_edge("record_ledger", END)
    workflow.add_edge("block_and_log", END)

    return workflow.compile()


# Compiled singleton instance
recovery_workflow = create_recovery_graph()
