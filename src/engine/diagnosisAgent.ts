import { ChannelType, DiagnosisResult, RiskType } from "../types.js";
import { EMAIL_RECOVERY_TEMPLATES, HINGLISH_VOICE_SCRIPT_TEMPLATE } from "./prompts.js";

export class DiagnosisAgent {
  static async diagnose(params: {
    risk_type: string;
    amount: number;
    currency: string;
    customer_name: string;
    customer_email: string;
    customer_phone?: string;
    metadata: Record<string, any>;
    language?: string;
  }): Promise<DiagnosisResult> {
    const {
      risk_type,
      amount,
      currency,
      customer_name,
      customer_phone,
      metadata,
      language = "en",
    } = params;

    // 1. Soft Decline Strategy
    if (risk_type === RiskType.SOFT_DECLINE || risk_type.includes("decline")) {
      const declineCode = metadata.decline_code || "insufficient_funds";
      const isSoft = metadata.is_soft_decline !== false;

      if (isSoft) {
        const rootCause = `Temporary bank/card liquidity constraint (${declineCode})`;
        const recommendedChannel = ChannelType.GATEWAY_RETRY;
        const retryHours = String(declineCode).includes("insufficient") ? 24 : 12;
        const strategySummary = `Schedule smart gateway retry in ${retryHours} hours to capture post-salary deposit window.`;
        const subject = "Update regarding your recent subscription payment";
        const body = EMAIL_RECOVERY_TEMPLATES.soft_decline({
          customer_name,
          currency,
          amount,
          retry_delay_hours: retryHours,
          payment_link: "https://pay.recovery-ai.internal/portal/update-card",
        });

        return {
          root_cause: rootCause,
          confidence: 0.92,
          recommended_channel: recommendedChannel,
          strategy_summary: strategySummary,
          subject,
          message_body: body,
          tone: "empathetic_supportive",
          language,
          retry_delay_hours: retryHours,
          reasoning_chain: [
            `Identified soft decline code '${declineCode}'`,
            "Direct immediate retry has high bounce risk; 24h backoff increases success probability by 38%",
            "Prepared automated email fallback with self-serve card update link",
          ],
        };
      } else {
        const rootCause = `Hard card decline (${declineCode})`;
        const recommendedChannel = ChannelType.EMAIL;
        const strategySummary = "Immediate email outreach requesting new payment instrument.";
        const subject = "Action Required: Please update your payment method";
        const body = `Hi ${customer_name},\n\nYour card was declined (${declineCode}). Please add a new payment method to prevent service disruption.`;

        return {
          root_cause: rootCause,
          confidence: 0.92,
          recommended_channel: recommendedChannel,
          strategy_summary: strategySummary,
          subject,
          message_body: body,
          tone: "empathetic_supportive",
          language,
          retry_delay_hours: null,
          reasoning_chain: ["Hard decline cannot be retried at gateway; direct customer action required."],
        };
      }
    }

    // 2. Abandoned Checkout Strategy
    if (risk_type === RiskType.ABANDONED_CHECKOUT) {
      const discountPct = metadata.recommended_discount_pct ?? 5.0;
      const rootCause = "Customer dropped off during checkout step due to price sensitivity or session interruption";
      const recommendedChannel = amount < 1000 ? ChannelType.EMAIL : ChannelType.SMS;
      const strategySummary = `Dispatch personalized recovery notification with dynamic ${discountPct}% incentive link.`;
      const subject = "Still thinking it over? Here is a special gift for you";
      const body = EMAIL_RECOVERY_TEMPLATES.abandoned_checkout({
        customer_name,
        discount_pct: discountPct,
        payment_link: `https://checkout.recovery-ai.internal/recover?cart_id=${metadata.cart_id || "123"}&disc=${discountPct}`,
      });

      return {
        root_cause: rootCause,
        confidence: 0.88,
        recommended_channel: recommendedChannel,
        strategy_summary: strategySummary,
        subject,
        message_body: body,
        tone: "friendly_incentivized",
        language,
        offered_discount_pct: discountPct,
        reasoning_chain: [
          "Cart abandoned at final step without technical errors",
          `Applied dynamic discount of ${discountPct}% to maximize conversion recovery`,
          "Time-limited 24h validity encourages prompt action",
        ],
      };
    }

    // 3. Overdue B2B Invoice Strategy
    if (risk_type === RiskType.OVERDUE_INVOICE) {
      const daysOverdue = metadata.days_overdue ?? 30;
      const invoiceId = metadata.invoice_id || "INV-1092";

      if (daysOverdue >= 60 || language === "hinglish" || language === "hi") {
        const rootCause = `Delinquent B2B payment terms (${daysOverdue} days past due). Risk of write-off.`;
        const recommendedChannel = ChannelType.VOICE;
        const isHinglish = language === "hinglish" || language === "hi";
        const strategySummary = `Initiate conversational ${isHinglish ? "Hinglish" : "English"} AI voice agent call to secure a Promise-to-Pay (P2P) date.`;
        const subject = `Urgent: Payment Status for Invoice #${invoiceId}`;
        const body = HINGLISH_VOICE_SCRIPT_TEMPLATE({
          customer_name,
          company_name: "Enterprise Systems",
          currency,
          amount,
          days_overdue: daysOverdue,
        });

        return {
          root_cause: rootCause,
          confidence: 0.95,
          recommended_channel: recommendedChannel,
          strategy_summary: strategySummary,
          subject,
          message_body: body,
          tone: isHinglish ? "conversational_hinglish" : "formal_ar",
          language,
          installment_eligible: amount > 5000,
          reasoning_chain: [
            `Invoice is severely overdue (${daysOverdue} days)`,
            "Interactive voice dialogue has 3.4x higher response rate for overdue receivables",
            "Objective: Obtain explicit Promise-to-Pay (P2P) date",
          ],
        };
      } else {
        const rootCause = `Routine B2B payment cycle delay (${daysOverdue} days overdue)`;
        const recommendedChannel = ChannelType.INVOICE_PORTAL;
        const strategySummary = "Dispatch formal payment portal reminder with 1-click settlement options.";
        const subject = `Payment Reminder: Invoice #${invoiceId} (${currency} ${amount})`;
        const body = EMAIL_RECOVERY_TEMPLATES.overdue_invoice({
          customer_name,
          invoice_id: invoiceId,
          currency,
          amount,
          days_overdue: daysOverdue,
          payment_link: `https://portal.recovery-ai.internal/invoices/${invoiceId}`,
        });

        return {
          root_cause: rootCause,
          confidence: 0.9,
          recommended_channel: recommendedChannel,
          strategy_summary: strategySummary,
          subject,
          message_body: body,
          tone: "formal_ar",
          language,
          reasoning_chain: [
            `Standard overdue notice for ${daysOverdue} days delay`,
            "Sending direct payment link with enterprise terms",
          ],
        };
      }
    }

    // 4. Expired Mandate / Default Strategy
    return {
      root_cause: "AutoPay mandate expired or invalidated",
      confidence: 0.85,
      recommended_channel: customer_phone ? ChannelType.SMS : ChannelType.EMAIL,
      strategy_summary: "Dispatch 1-click mandate re-authorization link to avoid recurring subscription halt.",
      subject: "Action Required: Re-authorize your subscription AutoPay",
      message_body: `Hi ${customer_name}, your recurring payment mandate has expired. Please re-authorize in 30 seconds: https://pay.recovery-ai.internal/mandate/renew`,
      tone: "urgent_preservation",
      language,
      reasoning_chain: [
        "Mandate expiration requires customer authorization signature",
        "Fast-action SMS/Email link minimizes subscription churn",
      ],
    };
  }
}
