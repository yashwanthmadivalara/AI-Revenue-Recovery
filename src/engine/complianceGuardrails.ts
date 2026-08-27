import { ChannelType, GuardrailEvaluationResult, GuardrailViolation } from "../types.js";

// In-memory contact history & promise-to-pay tracker
const customerContactHistory = new Map<string, { timestamp: number; channel: string }[]>();
const customerPromises = new Map<string, { promiseDate: number; amount: number }>();
const customerDisputes = new Set<string>(["cust_dispute_12"]);
const customerOptOuts = new Set<string>();

export class ComplianceGuardrails {
  static MAX_CONTACT_ATTEMPTS_PER_WEEK = 3;
  static HIGH_VALUE_THRESHOLD_USD = 5000.0;
  static ENABLE_QUIET_HOURS = true;
  static ENABLE_DISPUTE_KILLSWITCH = true;

  static logContact(customerId: string, channel: string) {
    const list = customerContactHistory.get(customerId) || [];
    list.push({ timestamp: Date.now(), channel });
    customerContactHistory.set(customerId, list);
  }

  static getRecentContactCount(customerId: string): number {
    const list = customerContactHistory.get(customerId) || [];
    const oneWeekAgo = Date.now() - 7 * 24 * 60 * 60 * 1000;
    return list.filter((item) => item.timestamp >= oneWeekAgo).length;
  }

  static isWithinQuietHours(timezoneStr: string = "UTC", channel: string = "email"): boolean {
    if (!this.ENABLE_QUIET_HOURS) return false;

    // Email and gateway retries and portals are allowed 24/7
    if (
      channel === ChannelType.EMAIL ||
      channel === ChannelType.GATEWAY_RETRY ||
      channel === ChannelType.INVOICE_PORTAL
    ) {
      return false;
    }

    try {
      const now = new Date();
      const formatter = new Intl.DateTimeFormat("en-US", {
        timeZone: timezoneStr,
        hour: "numeric",
        hour12: false,
      });
      const hour = parseInt(formatter.format(now), 10);

      // Quiet hours: 21:00 (9 PM) to 08:00 (8 AM)
      if (hour >= 21 || hour < 8) {
        return true;
      }
      return false;
    } catch {
      const utcHour = new Date().getUTCHours();
      return utcHour >= 21 || utcHour < 8;
    }
  }

  static async evaluate(params: {
    customer_id: string;
    customer_timezone?: string;
    channel?: string;
    amount?: number;
    has_active_dispute?: boolean;
    has_opted_out?: boolean;
  }): Promise<GuardrailEvaluationResult> {
    const {
      customer_id,
      customer_timezone = "UTC",
      channel = "email",
      amount = 0,
      has_active_dispute = false,
      has_opted_out = false,
    } = params;

    const violations: GuardrailViolation[] = [];
    let requiresHumanApproval = false;

    // 1. Opt-out check
    if (has_opted_out || customerOptOuts.has(customer_id)) {
      violations.push({
        rule_name: "OPT_OUT_BLOCK",
        severity: "block",
        message: "Customer has opted out of automated communications.",
      });
    }

    // 2. Active Dispute / Chargeback Killswitch
    const hasDispute = has_active_dispute || customerDisputes.has(customer_id);
    if (this.ENABLE_DISPUTE_KILLSWITCH && hasDispute) {
      violations.push({
        rule_name: "DISPUTE_KILLSWITCH",
        severity: "block",
        message: "Active payment dispute or chargeback detected. Outreach halted immediately.",
      });
    }

    // 3. Promise-to-Pay Cooldown
    const promise = customerPromises.get(customer_id);
    const hasActivePromise = promise ? promise.promiseDate > Date.now() : false;
    if (hasActivePromise) {
      violations.push({
        rule_name: "PROMISE_TO_PAY_COOLDOWN",
        severity: "block",
        message: "Customer has an active, unexpired Promise-to-Pay commitment. Outreach paused.",
      });
    }

    // 4. Frequency Limiter (Weekly cap)
    const recentContacts = this.getRecentContactCount(customer_id);
    if (recentContacts >= this.MAX_CONTACT_ATTEMPTS_PER_WEEK) {
      violations.push({
        rule_name: "FREQUENCY_LIMIT_EXCEEDED",
        severity: "block",
        message: `Contact cap reached (${recentContacts}/${this.MAX_CONTACT_ATTEMPTS_PER_WEEK} attempts in last 7 days).`,
      });
    }

    // 5. Quiet hours check
    const inQuietHours = this.isWithinQuietHours(customer_timezone, channel);
    if (inQuietHours) {
      violations.push({
        rule_name: "QUIET_HOURS_RESTRICTION",
        severity: "block",
        message: `Outreach blocked during local quiet hours for timezone '${customer_timezone}'.`,
      });
    }

    // 6. High Value Human Approval Check
    if (amount >= this.HIGH_VALUE_THRESHOLD_USD) {
      requiresHumanApproval = true;
      violations.push({
        rule_name: "HIGH_VALUE_GATE",
        severity: "warning",
        message: `High-value recovery ($${amount.toFixed(2)} >= $${this.HIGH_VALUE_THRESHOLD_USD.toFixed(2)}). Flagged for human review.`,
      });
    }

    const isCompliant = !violations.some((v) => v.severity === "block");

    return {
      is_compliant: isCompliant,
      requires_human_approval: requiresHumanApproval,
      violations,
      evaluated_at: new Date().toISOString(),
      contact_count_last_7_days: recentContacts,
      has_active_dispute: hasDispute,
      active_promise_to_pay: hasActivePromise,
      is_quiet_hours: inQuietHours,
    };
  }
}
