import crypto from "crypto";
import {
  CohortRecoveryStats,
  FinancialLedgerEntry,
  FinancialMetricsResponse,
  LedgerEntryType,
} from "../types.js";

const GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000";

const ledgerRecords: FinancialLedgerEntry[] = [];
let nextSequenceId = 1;

export class AuditLedgerService {
  static calculateHash(params: {
    previous_hash: string;
    entry_id: string;
    case_id: string;
    entry_type: string;
    amount: number;
    net_recovered: number;
    timestamp_str: string;
  }): string {
    const {
      previous_hash,
      entry_id,
      case_id,
      entry_type,
      amount,
      net_recovered,
      timestamp_str,
    } = params;
    const cleanNet = Math.abs(net_recovered) < 1e-9 ? 0.0 : net_recovered;
    const cleanAmt = Math.abs(amount) < 1e-9 ? 0.0 : amount;
    const payload = `${previous_hash}|${entry_id}|${case_id}|${entry_type}|${cleanAmt.toFixed(4)}|${cleanNet.toFixed(4)}|${timestamp_str}`;
    return crypto.createHash("sha256").update(payload).digest("hex");
  }

  static async recordEntry(entry: {
    case_id: string;
    entry_type: LedgerEntryType;
    amount: number;
    currency: string;
    gross_recovered?: number;
    gateway_fee?: number;
    communication_cost?: number;
    ai_token_cost?: number;
    metadata?: Record<string, any>;
  }): Promise<FinancialLedgerEntry> {
    const entryId = `led_${Math.random().toString(36).substring(2, 14)}`;
    const now = new Date();
    // Format YYYY-MM-DD HH:MM:SS
    const timestampStr = now.toISOString().replace("T", " ").substring(0, 19);

    const grossRecovered = entry.gross_recovered || 0.0;
    const gatewayFee = entry.gateway_fee || 0.0;
    const commCost = entry.communication_cost || 0.0;
    const aiCost = entry.ai_token_cost || 0.0;
    const totalCosts = gatewayFee + commCost + aiCost;
    let netRecovered = grossRecovered > 0 ? grossRecovered - totalCosts : -totalCosts;
    if (Math.abs(netRecovered) < 1e-9) {
      netRecovered = 0.0;
    }

    const previousRecord = ledgerRecords.length > 0 ? ledgerRecords[ledgerRecords.length - 1] : null;
    const previousHash = previousRecord ? previousRecord.current_hash : GENESIS_HASH;

    const currentHash = this.calculateHash({
      previous_hash: previousHash,
      entry_id: entryId,
      case_id: entry.case_id,
      entry_type: String(entry.entry_type),
      amount: entry.amount,
      net_recovered: netRecovered,
      timestamp_str: timestampStr,
    });

    const record: FinancialLedgerEntry = {
      sequence_id: nextSequenceId++,
      entry_id: entryId,
      case_id: entry.case_id,
      entry_type: entry.entry_type,
      amount: entry.amount,
      currency: entry.currency,
      gross_recovered: grossRecovered,
      gateway_fee: gatewayFee,
      communication_cost: commCost,
      ai_token_cost: aiCost,
      net_recovered: netRecovered,
      previous_hash: previousHash,
      current_hash: currentHash,
      metadata: entry.metadata || {},
      timestamp: now.toISOString(),
    };

    ledgerRecords.push(record);
    return record;
  }

  static getEntries(limit: number = 50): FinancialLedgerEntry[] {
    return [...ledgerRecords].reverse().slice(0, limit);
  }

  static async verifyChainIntegrity(): Promise<{
    is_valid: boolean;
    total_records_verified: number;
    last_verified_hash?: string;
    broken_sequence_id?: number;
    tampered_sequence_id?: number;
    error?: string;
  }> {
    let expectedPrevHash = GENESIS_HASH;

    for (const r of ledgerRecords) {
      if (r.previous_hash !== expectedPrevHash) {
        return {
          is_valid: false,
          total_records_verified: ledgerRecords.length,
          broken_sequence_id: r.sequence_id,
          error: `Previous hash mismatch at sequence ${r.sequence_id}`,
        };
      }

      const timestampStr = r.timestamp.replace("T", " ").substring(0, 19);
      const recalculated = this.calculateHash({
        previous_hash: r.previous_hash,
        entry_id: r.entry_id,
        case_id: r.case_id,
        entry_type: String(r.entry_type),
        amount: r.amount,
        net_recovered: r.net_recovered,
        timestamp_str: timestampStr,
      });

      if (recalculated !== r.current_hash) {
        return {
          is_valid: false,
          total_records_verified: ledgerRecords.length,
          tampered_sequence_id: r.sequence_id,
          error: `Data tampering detected at sequence ${r.sequence_id}`,
        };
      }

      expectedPrevHash = r.current_hash;
    }

    return {
      is_valid: true,
      total_records_verified: ledgerRecords.length,
      last_verified_hash: expectedPrevHash,
    };
  }

  static getSummaryMetrics(): FinancialMetricsResponse {
    let totalAtRisk = 0.0;
    let totalGrossRecovered = 0.0;
    let totalGatewayFee = 0.0;
    let totalCommCost = 0.0;
    let totalAiCost = 0.0;
    const caseIds = new Set<string>();
    let guardrailBlocked = 0;

    for (const r of ledgerRecords) {
      totalAtRisk += r.amount;
      totalGrossRecovered += r.gross_recovered;
      totalGatewayFee += r.gateway_fee;
      totalCommCost += r.communication_cost;
      totalAiCost += r.ai_token_cost;
      caseIds.add(r.case_id);
      if (r.metadata?.status === "guardrail_blocked" || r.metadata?.status === "paused_dispute") {
        guardrailBlocked++;
      }
    }

    const totalCosts = totalGatewayFee + totalCommCost + totalAiCost;
    const netRecovered = totalGrossRecovered - totalCosts;
    const recoveryRate = totalAtRisk > 0 ? (totalGrossRecovered / totalAtRisk) * 100.0 : 0.0;
    const roiMultiple = totalCosts > 0 ? netRecovered / totalCosts : 0.0;

    return {
      total_revenue_at_risk: Math.round(totalAtRisk * 100) / 100,
      total_recovered_revenue: Math.round(totalGrossRecovered * 100) / 100,
      total_recovery_costs: Math.round(totalCosts * 100) / 100,
      net_recovered_revenue: Math.round(netRecovered * 100) / 100,
      overall_recovery_rate_pct: Math.round(recoveryRate * 10) / 10,
      net_roi_multiple: Math.round(roiMultiple * 100) / 100,
      total_cases_processed: caseIds.size,
      resolved_cases_count: caseIds.size - guardrailBlocked,
      active_cases_count: 0,
      guardrail_blocked_count: guardrailBlocked,
    };
  }

  static getCohortBreakdown(): CohortRecoveryStats[] {
    const cohortMap: Record<string, { cases: number; at_risk: number; recovered: number }> = {
      soft_decline: { cases: 0, at_risk: 0.0, recovered: 0.0 },
      abandoned_checkout: { cases: 0, at_risk: 0.0, recovered: 0.0 },
      overdue_invoice: { cases: 0, at_risk: 0.0, recovered: 0.0 },
      expired_mandate: { cases: 0, at_risk: 0.0, recovered: 0.0 },
    };

    for (const r of ledgerRecords) {
      const rtype = r.metadata?.risk_type || "soft_decline";
      if (cohortMap[rtype]) {
        cohortMap[rtype].cases++;
        cohortMap[rtype].at_risk += r.amount;
        cohortMap[rtype].recovered += r.gross_recovered;
      }
    }

    return Object.entries(cohortMap).map(([rtype, data]) => {
      const atRisk = data.at_risk;
      const rec = data.recovered;
      const rate = atRisk > 0 ? (rec / atRisk) * 100.0 : 0.0;
      return {
        risk_type: rtype,
        total_cases: data.cases,
        total_at_risk_usd: Math.round(atRisk * 100) / 100,
        recovered_usd: Math.round(rec * 100) / 100,
        recovery_rate_pct: Math.round(rate * 10) / 10,
        avg_hours_to_recover: 18.5,
      };
    });
  }
}
