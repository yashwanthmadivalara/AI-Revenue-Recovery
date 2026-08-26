from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from app.models.event_models import ChannelType, RiskType


class DiagnosisResult(BaseModel):
    root_cause: str = Field(..., description="E.g., Temporary card limit, Technical gateway error, Cash flow crunch")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    recommended_channel: ChannelType = Field(..., description="Channel to execute recovery")
    strategy_summary: str = Field(..., description="Actionable strategy summary")
    
    # Message Generation
    subject: Optional[str] = Field(None, description="Email subject if email is chosen")
    message_body: Optional[str] = Field(None, description="Message text or voice agent prompt")
    tone: Optional[str] = Field("empathetic_professional", description="Tone of recovery outreach")
    language: Optional[str] = Field("en", description="Language e.g. en, hinglish, hi")
    
    # Custom strategy parameters
    retry_delay_hours: Optional[int] = Field(None, description="Optimal retry delay in hours")
    offered_discount_pct: Optional[float] = Field(0.0, description="Dynamic discount percentage")
    installment_eligible: bool = Field(False, description="Whether installment plan is suggested")
    
    reasoning_chain: List[str] = Field(default_factory=list, description="Step-by-step reasoning")


class CaseDiagnosisResponse(BaseModel):
    case_id: str
    risk_type: RiskType
    diagnosis: DiagnosisResult
