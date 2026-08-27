import { IngestionEvent, RecoveryAgentState } from "../types.js";
import { RecoveryWorkflow } from "./workflowGraph.js";

export const SCENARIOS: Record<string, IngestionEvent> = {
  soft_decline: {
    source: "stripe",
    event_type: "payment_intent.payment_failed",
    customer_id: "cust_stripe_88",
    customer_name: "Sarah Jenkins",
    customer_email: "sarah.j@acmecloud.io",
    customer_phone: "+14155552671",
    amount: 450.0,
    currency: "USD",
    decline_code: "insufficient_funds",
    metadata: { subscription_tier: "Pro Annual", retry_count: 1 },
  },
  abandoned_checkout: {
    source: "mixpanel",
    event_type: "checkout.abandoned",
    customer_id: "cust_cart_99",
    customer_name: "Marcus Vance",
    customer_email: "m.vance@designpro.com",
    customer_phone: "+14155559812",
    amount: 1200.0,
    currency: "USD",
    metadata: { cart_items_count: 3, time_spent_seconds: 180 },
  },
  overdue_b2b_hinglish: {
    source: "netsuite",
    event_type: "invoice.aged_60",
    customer_id: "cust_b2b_india_42",
    customer_name: "Rajesh Sharma",
    customer_email: "rajesh@sharmalogistics.in",
    customer_phone: "+919876543210",
    amount: 4200.0,
    currency: "INR",
    days_overdue: 65,
    metadata: { invoice_id: "INV-IN-8891", terms: "Net 30" },
  },
  active_dispute_blocked: {
    source: "stripe",
    event_type: "payment_intent.payment_failed",
    customer_id: "cust_dispute_12",
    customer_name: "Disputed Client",
    customer_email: "legal@disputed.com",
    customer_phone: "+14155550000",
    amount: 1500.0,
    currency: "USD",
    decline_code: "insufficient_funds",
    metadata: { has_active_dispute: true },
  },
};

export class SimulatorEngine {
  static listScenarios(): string[] {
    return Object.keys(SCENARIOS);
  }

  static async runScenario(scenarioKey: string) {
    const data = SCENARIOS[scenarioKey];
    if (!data) {
      return { error: `Scenario '${scenarioKey}' not found. Choose from ${Object.keys(SCENARIOS).join(", ")}` };
    }

    const caseId = `sim_${scenarioKey}_${Math.random().toString(36).substring(2, 8)}`;
    const isDisputed = Boolean(data.metadata?.has_active_dispute);

    const initialState: RecoveryAgentState = {
      case_id: caseId,
      customer_id: data.customer_id,
      customer_name: data.customer_name || "Valued Client",
      customer_email: data.customer_email || "client@example.com",
      customer_phone: data.customer_phone,
      customer_timezone: data.currency.toLowerCase().includes("in") ? "Asia/Kolkata" : "UTC",
      customer_language: data.currency.toLowerCase().includes("in") ? "hinglish" : "en",
      has_active_dispute: isDisputed,
      has_opted_out: false,
      ingestion_event: data,
      risk_type: "",
      severity: "",
      amount: data.amount,
      currency: data.currency,
      diagnosis: null,
      guardrail_result: null,
      is_compliant: true,
      requires_human_approval: false,
      is_approved: false,
      action_result: null,
      case_status: "open",
      cost_usd: 0.0,
      recovered_amount: 0.0,
      audit_sequence_id: null,
      execution_logs: [
        `Starting Scenario [${scenarioKey}] with amount ${data.amount} ${data.currency}`,
      ],
      error_message: null,
    };

    const finalState = await RecoveryWorkflow.run(initialState);

    return {
      scenario: scenarioKey,
      case_id: caseId,
      status: finalState.case_status,
      risk_type: finalState.risk_type,
      severity: finalState.severity,
      amount: finalState.amount,
      currency: finalState.currency,
      diagnosis: finalState.diagnosis,
      guardrail_result: finalState.guardrail_result,
      action_result: finalState.action_result,
      recovered_amount: finalState.recovered_amount,
      audit_sequence_id: finalState.audit_sequence_id,
      execution_logs: finalState.execution_logs,
    };
  }
}
