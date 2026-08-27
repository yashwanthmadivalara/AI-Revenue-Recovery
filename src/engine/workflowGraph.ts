import { ActionDispatcher } from "./actionDispatcher.js";
import { AuditLedgerService } from "./auditLedger.js";
import { ComplianceGuardrails } from "./complianceGuardrails.js";
import { DiagnosisAgent } from "./diagnosisAgent.js";
import { RiskDetector } from "./riskDetector.js";
import {
  ActionDispatchPayload,
  CaseStatus,
  ChannelType,
  IngestionEvent,
  LedgerEntryType,
  RecoveryAgentState,
} from "../types.js";

export class RecoveryWorkflow {
  static async run(initialState: RecoveryAgentState): Promise<RecoveryAgentState> {
    const state: RecoveryAgentState = { ...initialState };
    state.execution_logs = [...(state.execution_logs || [])];

    // Node 1: Detect Risk
    state.execution_logs.push("Executing Node: detect_risk");
    const ingestionEvent = state.ingestion_event as IngestionEvent;
    const riskResult = RiskDetector.evaluateEvent(ingestionEvent);
    state.risk_result = riskResult;
    state.risk_type = riskResult.risk_type;
    state.severity = riskResult.severity;
    state.amount = riskResult.amount;
    state.currency = riskResult.currency;
    state.execution_logs.push(
      `Risk Classified: [${riskResult.risk_type}] Severity [${riskResult.severity}]`
    );

    // Node 2: Diagnose Root Cause
    state.execution_logs.push("Executing Node: diagnose_root_cause");
    const rawPayload = riskResult.raw_payload || {};
    const diagnosis = await DiagnosisAgent.diagnose({
      risk_type: state.risk_type,
      amount: state.amount,
      currency: state.currency,
      customer_name: state.customer_name,
      customer_email: state.customer_email,
      customer_phone: state.customer_phone,
      metadata: rawPayload,
      language: state.customer_language,
    });
    state.diagnosis = diagnosis;
    state.execution_logs.push(
      `Strategy Formulated: Channel [${diagnosis.recommended_channel}] | Root Cause: ${diagnosis.root_cause}`
    );

    // Node 3: Evaluate Guardrails
    state.execution_logs.push("Executing Node: evaluate_guardrails");
    const evaluation = await ComplianceGuardrails.evaluate({
      customer_id: state.customer_id,
      customer_timezone: state.customer_timezone,
      channel: diagnosis.recommended_channel,
      amount: state.amount,
      has_active_dispute: state.has_active_dispute,
      has_opted_out: state.has_opted_out,
    });
    state.guardrail_result = evaluation;
    state.is_compliant = evaluation.is_compliant;
    state.requires_human_approval = evaluation.requires_human_approval;

    if (evaluation.is_compliant) {
      state.execution_logs.push("Guardrails Passed: Full compliance verified.");
    } else {
      const violationsStr = evaluation.violations.map((v) => v.message).join(", ");
      state.execution_logs.push(`Guardrails BLOCKED: ${violationsStr}`);
    }

    // Conditional Routing
    if (state.is_compliant) {
      // Node 4: Execute Action
      state.execution_logs.push("Executing Node: execute_action");
      const channel = diagnosis.recommended_channel || ChannelType.EMAIL;
      const payload: ActionDispatchPayload = {
        case_id: state.case_id,
        channel,
        recipient_email: state.customer_email,
        recipient_phone: state.customer_phone,
        subject: diagnosis.subject,
        content: diagnosis.message_body,
        amount: state.amount,
        currency: state.currency,
        metadata: {
          customer_id: state.customer_id,
          diagnosis,
          retry_delay_hours: diagnosis.retry_delay_hours,
          discount_pct: diagnosis.offered_discount_pct ?? 0.0,
        },
      };

      const result = await ActionDispatcher.dispatch(payload);
      state.action_result = result;
      state.cost_usd = result.cost_usd;
      state.execution_logs.push(
        `Action Dispatched [${channel}]: Status [${result.status}] Ref [${result.external_reference_id || "--"}] Cost [$${result.cost_usd.toFixed(4)}]`
      );

      let simulatedRecovered = 0.0;
      if (["success", "simulated", "delivered", "completed"].includes(result.status)) {
        simulatedRecovered = state.amount;
      }
      state.recovered_amount = simulatedRecovered;
      state.case_status =
        simulatedRecovered > 0 ? CaseStatus.RESOLVED : CaseStatus.EXECUTING;

      // Node 5: Record Ledger
      state.execution_logs.push("Executing Node: record_ledger");
      const ledgerEntry = await AuditLedgerService.recordEntry({
        case_id: state.case_id,
        entry_type: LedgerEntryType.ACTION_DISPATCHED,
        amount: state.amount,
        currency: state.currency,
        gross_recovered: simulatedRecovered,
        gateway_fee: simulatedRecovered > 0 ? simulatedRecovered * 0.02 : 0.0,
        communication_cost: result.cost_usd,
        ai_token_cost: 0.002,
        metadata: {
          risk_type: state.risk_type,
          channel: diagnosis.recommended_channel,
          status: state.case_status,
        },
      });

      state.audit_sequence_id = ledgerEntry.sequence_id;
      state.execution_logs.push(
        `Financial Ledger Updated: Seq #${ledgerEntry.sequence_id} Hash [${ledgerEntry.current_hash.slice(0, 12)}...] Net Recovered [$${ledgerEntry.net_recovered.toFixed(2)}]`
      );
    } else {
      // Node: Block and Log
      state.execution_logs.push("Case Blocked by Policy Guardrails. Halting outreach.");
      const status = state.has_active_dispute
        ? CaseStatus.PAUSED_DISPUTE
        : CaseStatus.GUARDRAIL_BLOCKED;
      state.case_status = status;

      const ledgerEntry = await AuditLedgerService.recordEntry({
        case_id: state.case_id,
        entry_type: LedgerEntryType.CASE_CLOSED,
        amount: state.amount,
        currency: state.currency,
        gross_recovered: 0,
        gateway_fee: 0,
        communication_cost: 0,
        ai_token_cost: 0.001,
        metadata: {
          blocked_reason: evaluation.violations,
          status,
        },
      });
      state.audit_sequence_id = ledgerEntry.sequence_id;
    }

    return state;
  }
}
