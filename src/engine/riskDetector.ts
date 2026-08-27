import { IngestionEvent, RiskDetectionResult, RiskSeverity, RiskType } from "../types.js";

const SOFT_DECLINE_CODES = new Set([
  "insufficient_funds",
  "card_velocity_exceeded",
  "try_again_later",
  "processing_error",
  "issuer_unavailable",
  "temporary_hold",
  "exceeded_pin_retry",
  "timeout",
  "gateway_timeout",
  "network_error",
  "do_not_honor",
]);

const HARD_DECLINE_CODES = new Set([
  "stolen_card",
  "lost_card",
  "fraudulent",
  "card_expired",
  "invalid_account_number",
  "pickup_card",
  "restricted_card",
  "account_closed",
]);

export class SoftDeclineEvaluator {
  static evaluate(declineCode: string, amount: number): [boolean, RiskSeverity, string] {
    const normalizedCode = (declineCode || "generic").toLowerCase().replace(/\s+/g, "_");

    for (const soft of SOFT_DECLINE_CODES) {
      if (normalizedCode.includes(soft)) {
        let severity = RiskSeverity.LOW;
        if (amount > 1000) severity = RiskSeverity.HIGH;
        else if (amount > 200) severity = RiskSeverity.MEDIUM;
        return [true, severity, `Soft decline detected (${normalizedCode}): Eligible for smart gateway retry sequencing.`];
      }
    }

    for (const hard of HARD_DECLINE_CODES) {
      if (normalizedCode.includes(hard)) {
        return [false, RiskSeverity.CRITICAL, `Hard decline detected (${normalizedCode}): Direct card retry will fail. Requires customer payment method update.`];
      }
    }

    const severity = amount > 250 ? RiskSeverity.MEDIUM : RiskSeverity.LOW;
    return [true, severity, `Unclassified decline code (${normalizedCode}): Treated as potential soft decline with fallback outreach.`];
  }
}

export class CheckoutAbandonmentEvaluator {
  static evaluate(amount: number, metadata: Record<string, any> = {}): [RiskSeverity, string, number] {
    const hasPromoApplied = !!metadata.has_promo_applied;

    if (amount >= 1000) {
      const discountPct = !hasPromoApplied ? 5.0 : 0.0;
      return [
        RiskSeverity.HIGH,
        "High-value cart abandoned at checkout step. Priority recovery with dynamic discount incentive.",
        discountPct,
      ];
    } else if (amount >= 250) {
      const discountPct = !hasPromoApplied ? 10.0 : 0.0;
      return [
        RiskSeverity.MEDIUM,
        "Mid-value checkout abandonment. Standard automated email/SMS recovery sequence.",
        discountPct,
      ];
    } else {
      return [
        RiskSeverity.LOW,
        "Low-value cart abandonment. Single email notification.",
        0.0,
      ];
    }
  }
}

export class InvoiceAgingEvaluator {
  static evaluate(daysOverdue: number, amount: number): [RiskSeverity, string, boolean] {
    let severity: RiskSeverity;
    let reason: string;
    let requiresVoice: boolean;

    if (daysOverdue >= 90) {
      severity = RiskSeverity.CRITICAL;
      reason = `Invoice is ${daysOverdue} days delinquent (>90 days). High bad-debt write-off risk. Immediate AI Voice outreach or human collections required.`;
      requiresVoice = true;
    } else if (daysOverdue >= 60) {
      severity = RiskSeverity.HIGH;
      reason = `Invoice is ${daysOverdue} days delinquent (60-89 days). Medium bad-debt risk. Multilingual AI Voice call with Promise-to-Pay negotiation.`;
      requiresVoice = true;
    } else if (daysOverdue >= 30) {
      severity = RiskSeverity.MEDIUM;
      reason = `Invoice is ${daysOverdue} days overdue (30-59 days). Formal accounts receivable dunning notice & payment link.`;
      requiresVoice = false;
    } else {
      severity = RiskSeverity.LOW;
      reason = `Invoice is ${daysOverdue} days past due (<30 days). Friendly automated reminder.`;
      requiresVoice = false;
    }

    if (amount >= 10000) {
      severity = RiskSeverity.CRITICAL;
    }

    return [severity, reason, requiresVoice];
  }
}

export class MandateExpiryEvaluator {
  static evaluate(amount: number, metadata: Record<string, any> = {}): [RiskSeverity, string] {
    const daysUntilHalt = metadata.days_until_halt ?? 3;
    let severity = RiskSeverity.MEDIUM;
    if (amount > 1000 || daysUntilHalt <= 1) {
      severity = RiskSeverity.HIGH;
    }
    return [
      severity,
      `Recurring mandate expiry risk. Subscriptions will halt in ${daysUntilHalt} days unless renewed.`,
    ];
  }
}

export class RiskDetector {
  static evaluateEvent(event: IngestionEvent): RiskDetectionResult {
    const eventId = `risk_${Math.random().toString(36).substring(2, 14)}`;
    const eventType = (event.event_type || "").toLowerCase();
    const amount = event.amount;
    const metadata = event.metadata || {};

    let riskType: RiskType;
    let severity: RiskSeverity;
    let payload: Record<string, any>;

    if (eventType.includes("payment_failed") || eventType.includes("failed") || event.decline_code) {
      const [isSoft, sev, reason] = SoftDeclineEvaluator.evaluate(event.decline_code || "generic", amount);
      riskType = RiskType.SOFT_DECLINE;
      severity = sev;
      payload = {
        reason,
        is_soft_decline: isSoft,
        decline_code: event.decline_code,
        source_metadata: metadata,
      };
    } else if (eventType.includes("abandoned") || eventType.includes("checkout") || eventType.includes("cart_exit")) {
      riskType = RiskType.ABANDONED_CHECKOUT;
      const [sev, reason, discountPct] = CheckoutAbandonmentEvaluator.evaluate(amount, metadata);
      severity = sev;
      payload = {
        reason,
        recommended_discount_pct: discountPct,
        source_metadata: metadata,
      };
    } else if (eventType.includes("invoice") || eventType.includes("aged") || event.days_overdue !== undefined) {
      riskType = RiskType.OVERDUE_INVOICE;
      const days = event.days_overdue !== undefined ? event.days_overdue : 30;
      const [sev, reason, needsVoice] = InvoiceAgingEvaluator.evaluate(days, amount);
      severity = sev;
      payload = {
        reason,
        days_overdue: days,
        requires_voice: needsVoice,
        source_metadata: metadata,
      };
    } else if (eventType.includes("mandate") || eventType.includes("autopay") || eventType.includes("subscription.halted")) {
      riskType = RiskType.EXPIRED_MANDATE;
      const [sev, reason] = MandateExpiryEvaluator.evaluate(amount, metadata);
      severity = sev;
      payload = {
        reason,
        source_metadata: metadata,
      };
    } else {
      riskType = RiskType.UNKNOWN;
      severity = RiskSeverity.MEDIUM;
      payload = {
        reason: "Unclassified event ingested",
        source_metadata: metadata,
      };
    }

    return {
      event_id: eventId,
      source: event.source,
      event_type: event.event_type,
      risk_type: riskType,
      severity,
      amount,
      currency: event.currency,
      customer_id: event.customer_id,
      detected_at: new Date().toISOString(),
      raw_payload: payload,
    };
  }
}
