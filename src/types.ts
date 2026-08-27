export enum RiskType {
  SOFT_DECLINE = "soft_decline",
  ABANDONED_CHECKOUT = "abandoned_checkout",
  OVERDUE_INVOICE = "overdue_invoice",
  EXPIRED_MANDATE = "expired_mandate",
  UNKNOWN = "unknown",
}

export enum RiskSeverity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export enum ChannelType {
  GATEWAY_RETRY = "gateway_retry",
  EMAIL = "email",
  SMS = "sms",
  VOICE = "voice",
  INVOICE_PORTAL = "invoice_portal",
  MANUAL_ESCALATION = "manual_escalation",
}

export enum CaseStatus {
  OPEN = "open",
  DIAGNOSED = "diagnosed",
  GUARDRAIL_BLOCKED = "guardrail_blocked",
  PAUSED_DISPUTE = "paused_dispute",
  PENDING_APPROVAL = "pending_human_approval",
  EXECUTING = "executing",
  RESOLVED = "resolved",
  FAILED = "failed",
}

export enum LedgerEntryType {
  RISK_IDENTIFIED = "risk_identified",
  ACTION_DISPATCHED = "action_dispatched",
  FEE_INCIDENT = "fee_incident",
  RECOVERY_SUCCESS = "recovery_success",
  RECOVERY_FAILED = "recovery_failed",
  CASE_CLOSED = "case_closed",
}

export interface IngestionEvent {
  source: string;
  event_type: string;
  customer_id: string;
  customer_name?: string;
  customer_email?: string;
  customer_phone?: string;
  amount: number;
  currency: string;
  decline_code?: string;
  days_overdue?: number;
  metadata?: Record<string, any>;
}

export interface RiskDetectionResult {
  event_id: string;
  source: string;
  event_type: string;
  risk_type: RiskType;
  severity: RiskSeverity;
  amount: number;
  currency: string;
  customer_id: string;
  detected_at: string;
  raw_payload: Record<string, any>;
}

export interface DiagnosisResult {
  root_cause: string;
  confidence: number;
  recommended_channel: ChannelType;
  strategy_summary: string;
  subject?: string;
  message_body?: string;
  tone?: string;
  language: string;
  retry_delay_hours?: number | null;
  offered_discount_pct?: number;
  installment_eligible?: boolean;
  reasoning_chain?: string[];
}

export interface GuardrailViolation {
  rule_name: string;
  severity: "block" | "warning";
  message: string;
}

export interface GuardrailEvaluationResult {
  is_compliant: boolean;
  requires_human_approval: boolean;
  violations: GuardrailViolation[];
  evaluated_at: string;
  contact_count_last_7_days: number;
  has_active_dispute: boolean;
  active_promise_to_pay: boolean;
  is_quiet_hours: boolean;
}

export interface ActionDispatchPayload {
  case_id: string;
  channel: ChannelType;
  recipient_email?: string;
  recipient_phone?: string;
  subject?: string;
  content?: string;
  amount: number;
  currency: string;
  metadata?: Record<string, any>;
}

export interface ActionDispatchResult {
  action_id: string;
  case_id: string;
  channel: ChannelType;
  status: string;
  idempotency_key: string;
  external_reference_id?: string | null;
  cost_usd: number;
  dispatched_at: string;
  details: Record<string, any>;
}

export interface FinancialLedgerEntry {
  sequence_id: number;
  entry_id: string;
  case_id: string;
  entry_type: LedgerEntryType;
  amount: number;
  currency: string;
  gross_recovered: number;
  gateway_fee: number;
  communication_cost: number;
  ai_token_cost: number;
  net_recovered: number;
  previous_hash: string;
  current_hash: string;
  metadata: Record<string, any>;
  timestamp: string;
}

export interface FinancialMetricsResponse {
  total_revenue_at_risk: number;
  total_recovered_revenue: number;
  total_recovery_costs: number;
  net_recovered_revenue: number;
  overall_recovery_rate_pct: number;
  net_roi_multiple: number;
  total_cases_processed: number;
  resolved_cases_count: number;
  active_cases_count: number;
  guardrail_blocked_count: number;
}

export interface CohortRecoveryStats {
  risk_type: string;
  total_cases: number;
  total_at_risk_usd: number;
  recovered_usd: number;
  recovery_rate_pct: number;
  avg_hours_to_recover: number;
}

export interface RecoveryAgentState {
  case_id: string;
  customer_id: string;
  customer_name: string;
  customer_email: string;
  customer_phone?: string;
  customer_timezone: string;
  customer_language: string;
  has_active_dispute: boolean;
  has_opted_out: boolean;
  ingestion_event: Record<string, any>;
  risk_result?: Record<string, any>;
  risk_type: string;
  severity: string;
  amount: number;
  currency: string;
  diagnosis?: DiagnosisResult | null;
  guardrail_result?: GuardrailEvaluationResult | null;
  is_compliant: boolean;
  requires_human_approval: boolean;
  is_approved: boolean;
  action_result?: ActionDispatchResult | null;
  case_status: CaseStatus | string;
  cost_usd: number;
  recovered_amount: number;
  audit_sequence_id?: number | null;
  execution_logs: string[];
  error_message?: string | null;
}
