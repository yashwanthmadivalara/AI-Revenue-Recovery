from typing import TypedDict, Optional, Dict, Any, List
from app.models.event_models import RiskType, RiskSeverity, CaseStatus, ChannelType
from app.schemas.events import IngestionEvent, RiskDetectionResult
from app.schemas.diagnosis import DiagnosisResult
from app.schemas.guardrails import GuardrailEvaluationResult
from app.schemas.actions import ActionDispatchResult


class RecoveryAgentState(TypedDict):
    """
    Complete state passed across nodes in the LangGraph recovery workflow.
    """
    case_id: str
    customer_id: str
    customer_name: str
    customer_email: str
    customer_phone: Optional[str]
    customer_timezone: str
    customer_language: str
    has_active_dispute: bool
    has_opted_out: bool

    # Event & Risk
    ingestion_event: Dict[str, Any]
    risk_result: Dict[str, Any]
    risk_type: str
    severity: str
    amount: float
    currency: str

    # Diagnosis & Reasoning
    diagnosis: Optional[Dict[str, Any]]
    
    # Policy Guardrails
    guardrail_result: Optional[Dict[str, Any]]
    is_compliant: bool
    requires_human_approval: bool
    is_approved: bool

    # Execution & Action
    action_result: Optional[Dict[str, Any]]
    case_status: str

    # Financial & Audit
    cost_usd: float
    recovered_amount: float
    audit_sequence_id: Optional[int]
    
    # Workflow logging
    execution_logs: List[str]
    error_message: Optional[str]
