import crypto from "crypto";
import { ActionDispatchPayload, ActionDispatchResult, ChannelType } from "../types.js";
import { ComplianceGuardrails } from "./complianceGuardrails.js";

export interface ActionRecordItem {
  id: string;
  case_id: string;
  channel: string;
  status: string;
  cost_usd: number;
  dispatched_at: string;
  details: Record<string, any>;
}

const actionRecords: ActionRecordItem[] = [];

export class DynamicPaymentLinkGenerator {
  static generateLink(params: {
    case_id: string;
    amount: number;
    discount_pct?: number;
    currency?: string;
    expires_in_hours?: number;
  }): {
    link_id: string;
    url: string;
    original_amount: number;
    discount_pct: number;
    final_payable_amount: number;
    currency: string;
    expires_in_hours: number;
  } {
    const {
      case_id,
      amount,
      discount_pct = 0.0,
      currency = "USD",
      expires_in_hours = 48,
    } = params;
    const linkId = `link_${Math.random().toString(36).substring(2, 12)}`;
    const finalAmount = Math.round(amount * (1 - discount_pct / 100) * 100) / 100;
    const secret = process.env.SECRET_KEY || "revenue_recovery_secret_key_2026";
    const signatureRaw = `${case_id}:${finalAmount}:${currency}:${secret}`;
    const signature = crypto.createHash("sha256").update(signatureRaw).digest("hex").slice(0, 16);

    const url = `https://pay.recovery-ai.internal/checkout/${linkId}?case=${case_id}&amt=${finalAmount}&cur=${currency}&sig=${signature}`;

    return {
      link_id: linkId,
      url,
      original_amount: amount,
      discount_pct,
      final_payable_amount: finalAmount,
      currency,
      expires_in_hours,
    };
  }
}

export class ActionDispatcher {
  static generateIdempotencyKey(payload: ActionDispatchPayload): string {
    const raw = `${payload.case_id}:${payload.channel}:${payload.amount}:${new Date().toISOString().slice(0, 13)}`;
    return crypto.createHash("sha256").update(raw).digest("hex").slice(0, 32);
  }

  static getActionRecords(limit: number = 50): ActionRecordItem[] {
    return [...actionRecords].reverse().slice(0, limit);
  }

  static async dispatch(payload: ActionDispatchPayload): Promise<ActionDispatchResult> {
    const idempotencyKey = this.generateIdempotencyKey(payload);
    const actionId = `act_${Math.random().toString(36).substring(2, 14)}`;
    const channel = payload.channel;
    let details: Record<string, any> = {};
    let costUsd = 0.0;
    let status = "dispatched";
    let externalRef: string | null = null;

    try {
      if (channel === ChannelType.GATEWAY_RETRY) {
        const delayHours = payload.metadata?.retry_delay_hours ?? 24;
        externalRef = `gw_retry_${Math.random().toString(36).substring(2, 10)}`;
        costUsd = 0.0;
        status = "success";
        details = {
          retry_id: externalRef,
          scheduled_in_hours: delayHours,
          target_timestamp: new Date(Date.now() + delayHours * 3600 * 1000).toISOString(),
          gateway_engine: "Stripe Smart Retries v2",
          cost_usd: costUsd,
        };
      } else if (channel === ChannelType.EMAIL) {
        const linkInfo = DynamicPaymentLinkGenerator.generateLink({
          case_id: payload.case_id,
          amount: payload.amount,
          discount_pct: payload.metadata?.discount_pct ?? 0.0,
          currency: payload.currency,
        });
        externalRef = `msg_email_${Math.random().toString(36).substring(2, 10)}`;
        costUsd = 0.001;
        status = "delivered";
        details = {
          message_id: externalRef,
          recipient: payload.recipient_email || "customer@example.com",
          subject: payload.subject || "Payment Notification",
          payment_link: linkInfo.url,
          discount_applied_pct: linkInfo.discount_pct,
          cost_usd: costUsd,
        };
      } else if (channel === ChannelType.SMS) {
        const linkInfo = DynamicPaymentLinkGenerator.generateLink({
          case_id: payload.case_id,
          amount: payload.amount,
          discount_pct: payload.metadata?.discount_pct ?? 0.0,
          currency: payload.currency,
        });
        externalRef = `sms_${Math.random().toString(36).substring(2, 10)}`;
        costUsd = 0.0075;
        status = "delivered";
        details = {
          message_id: externalRef,
          recipient: payload.recipient_phone || "+15550192834",
          body_preview: payload.content?.slice(0, 80),
          payment_link: linkInfo.url,
          cost_usd: costUsd,
        };
      } else if (channel === ChannelType.VOICE) {
        externalRef = `vcall_${Math.random().toString(36).substring(2, 10)}`;
        costUsd = 0.045;
        status = "completed";
        details = {
          call_id: externalRef,
          recipient_phone: payload.recipient_phone || "+919876543210",
          language: payload.metadata?.diagnosis?.language || "hinglish",
          call_duration_seconds: 42,
          promise_to_pay_secured: true,
          promised_date: new Date(Date.now() + 2 * 24 * 3600 * 1000).toISOString().split("T")[0],
          cost_usd: costUsd,
        };
      } else {
        const linkInfo = DynamicPaymentLinkGenerator.generateLink({
          case_id: payload.case_id,
          amount: payload.amount,
          currency: payload.currency,
        });
        externalRef = linkInfo.link_id;
        status = "delivered";
        costUsd = 0.001;
        details = {
          portal_link: linkInfo,
          cost_usd: costUsd,
        };
      }

      const record: ActionRecordItem = {
        id: actionId,
        case_id: payload.case_id,
        channel: String(channel),
        status,
        cost_usd: costUsd,
        dispatched_at: new Date().toISOString(),
        details,
      };
      actionRecords.push(record);

      // Track contact for frequency limits
      const customerId = payload.metadata?.customer_id || "cust_1";
      ComplianceGuardrails.logContact(customerId, String(channel));
    } catch (err: any) {
      status = "failed";
      details = { error: err.message || String(err) };
    }

    return {
      action_id: actionId,
      case_id: payload.case_id,
      channel,
      status,
      idempotency_key: idempotencyKey,
      external_reference_id: externalRef,
      cost_usd: costUsd,
      dispatched_at: new Date().toISOString(),
      details,
    };
  }
}
