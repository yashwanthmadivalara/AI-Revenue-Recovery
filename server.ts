import express from "express";
import cors from "cors";
import path from "path";
import { fileURLToPath } from "url";
import { SimulatorEngine } from "./src/engine/simulator.js";
import { AuditLedgerService } from "./src/engine/auditLedger.js";
import { ComplianceGuardrails } from "./src/engine/complianceGuardrails.js";
import { ActionDispatcher } from "./src/engine/actionDispatcher.js";
import { RecoveryWorkflow } from "./src/engine/workflowGraph.js";
import { IngestionEvent, RecoveryAgentState } from "./src/types.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();
const PORT = 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// Pre-seed simulator with initial scenarios so the dashboard starts with realistic ledger data
async function seedInitialData() {
  try {
    await SimulatorEngine.runScenario("soft_decline");
    await SimulatorEngine.runScenario("abandoned_checkout");
    await SimulatorEngine.runScenario("overdue_b2b_hinglish");
  } catch (err) {
    console.error("Initial seeding error:", err);
  }
}

// 1. Health Endpoint
app.get("/api/v1/health", (req, res) => {
  res.json({
    status: "healthy",
    system: "AI Revenue Recovery Engine",
    version: "1.0.0",
    engine: "Autonomous LangGraph State Machine",
    ledger: "SHA-256 Hash-Chained Append-Only",
    timestamp: new Date().toISOString(),
  });
});

// 2. Simulator Endpoints
app.get("/api/v1/simulator/scenarios", (req, res) => {
  res.json(SimulatorEngine.listScenarios());
});

app.post("/api/v1/simulator/run/:scenarioKey", async (req, res) => {
  const { scenarioKey } = req.params;
  const result = await SimulatorEngine.runScenario(scenarioKey);
  res.json(result);
});

// 3. Ledger & Financial Analytics Endpoints
app.get("/api/v1/ledger/metrics", (req, res) => {
  const metrics = AuditLedgerService.getSummaryMetrics();
  res.json(metrics);
});

app.get("/api/v1/ledger/entries", (req, res) => {
  const limit = parseInt(req.query.limit as string) || 50;
  const entries = AuditLedgerService.getEntries(limit);
  res.json(entries);
});

app.get("/api/v1/ledger/cohorts", (req, res) => {
  const cohorts = AuditLedgerService.getCohortBreakdown();
  res.json(cohorts);
});

app.get("/api/v1/ledger/verify-integrity", async (req, res) => {
  const validation = await AuditLedgerService.verifyChainIntegrity();
  res.json(validation);
});

// 4. Recovery Actions & Manual Trigger
app.get("/api/v1/recovery/actions", (req, res) => {
  const limit = parseInt(req.query.limit as string) || 50;
  const actions = ActionDispatcher.getActionRecords(limit);
  res.json(actions);
});

app.post("/api/v1/recovery/trigger", async (req, res) => {
  const event = req.body as IngestionEvent;
  if (!event || !event.customer_id || event.amount === undefined) {
    return res.status(400).json({ error: "Invalid ingestion event payload" });
  }

  const caseId = `rec_${Math.random().toString(36).substring(2, 10)}`;
  const initialState: RecoveryAgentState = {
    case_id: caseId,
    customer_id: event.customer_id,
    customer_name: event.customer_name || "Valued Client",
    customer_email: event.customer_email || "client@example.com",
    customer_phone: event.customer_phone,
    customer_timezone: "UTC",
    customer_language: "en",
    has_active_dispute: false,
    has_opted_out: false,
    ingestion_event: event,
    risk_type: "",
    severity: "",
    amount: event.amount,
    currency: event.currency || "USD",
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
    execution_logs: [`Ingested custom event for customer ${event.customer_id}`],
  };

  const finalState = await RecoveryWorkflow.run(initialState);
  res.json(finalState);
});

// 5. Guardrails Endpoints
app.get("/api/v1/guardrails/config", (req, res) => {
  res.json({
    max_contact_attempts_per_week: ComplianceGuardrails.MAX_CONTACT_ATTEMPTS_PER_WEEK,
    high_value_threshold_usd: ComplianceGuardrails.HIGH_VALUE_THRESHOLD_USD,
    enable_quiet_hours: ComplianceGuardrails.ENABLE_QUIET_HOURS,
    enable_dispute_killswitch: ComplianceGuardrails.ENABLE_DISPUTE_KILLSWITCH,
  });
});

app.post("/api/v1/guardrails/evaluate", async (req, res) => {
  const result = await ComplianceGuardrails.evaluate(req.body);
  res.json(result);
});

// 6. Webhooks Ingestion Endpoints
app.post("/api/v1/webhooks/stripe", async (req, res) => {
  const body = req.body;
  const event: IngestionEvent = {
    source: "stripe",
    event_type: body.type || "payment_intent.payment_failed",
    customer_id: body.data?.object?.customer || "cust_stripe_live",
    amount: (body.data?.object?.amount || 10000) / 100.0,
    currency: (body.data?.object?.currency || "usd").toUpperCase(),
    decline_code: body.data?.object?.last_payment_error?.code || "insufficient_funds",
    metadata: body,
  };
  const result = await RecoveryWorkflow.run({
    case_id: `wh_stripe_${Math.random().toString(36).substring(2, 8)}`,
    customer_id: event.customer_id,
    customer_name: "Stripe Customer",
    customer_email: "stripe.user@example.com",
    customer_timezone: "UTC",
    customer_language: "en",
    has_active_dispute: false,
    has_opted_out: false,
    ingestion_event: event,
    risk_type: "",
    severity: "",
    amount: event.amount,
    currency: event.currency,
    is_compliant: true,
    requires_human_approval: false,
    is_approved: false,
    case_status: "open",
    cost_usd: 0,
    recovered_amount: 0,
    execution_logs: ["Ingested live Stripe webhook"],
  });
  res.json({ status: "processed", case_id: result.case_id });
});

app.post("/api/v1/webhooks/razorpay", async (req, res) => {
  res.json({ status: "processed", source: "razorpay" });
});

app.post("/api/v1/webhooks/chargebee", async (req, res) => {
  res.json({ status: "processed", source: "chargebee" });
});

app.post("/api/v1/webhooks/erp", async (req, res) => {
  res.json({ status: "processed", source: "erp" });
});

// 7. Interactive API Documentation (/docs)
app.get("/docs", (req, res) => {
  res.send(`<!DOCTYPE html>
<html>
<head>
  <title>AI Revenue Recovery - Swagger API Docs</title>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
  <style>
    body { margin: 0; background: #0f172a; }
    .swagger-ui { filter: invert(88%) hue-rotate(180deg); }
    .swagger-ui .topbar { display: none; }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js"></script>
  <script>
    window.onload = () => {
      window.ui = SwaggerUIBundle({
        spec: {
          openapi: "3.0.0",
          info: {
            title: "AI Revenue Recovery Engine API",
            version: "1.0.0",
            description: "Autonomous Risk Detection, LangGraph Reasoning, Compliance Guardrails, and SHA-256 Append-Only Financial Audit Ledger."
          },
          paths: {
            "/api/v1/health": { get: { summary: "System Health Status", responses: { "200": { description: "OK" } } } },
            "/api/v1/simulator/scenarios": { get: { summary: "List Available Scenarios", responses: { "200": { description: "OK" } } } },
            "/api/v1/simulator/run/{scenarioKey}": { post: { summary: "Run Simulation Scenario", parameters: [{ name: "scenarioKey", in: "path", required: true, schema: { type: "string" } }], responses: { "200": { description: "OK" } } } },
            "/api/v1/ledger/metrics": { get: { summary: "Get ROI & Recovery KPI Metrics", responses: { "200": { description: "OK" } } } },
            "/api/v1/ledger/entries": { get: { summary: "Get Financial Ledger Entries", responses: { "200": { description: "OK" } } } },
            "/api/v1/ledger/verify-integrity": { get: { summary: "Cryptographically Verify SHA-256 Hash Chain", responses: { "200": { description: "OK" } } } },
            "/api/v1/recovery/trigger": { post: { summary: "Trigger Recovery Pipeline on Ingestion Event", responses: { "200": { description: "OK" } } } },
            "/api/v1/guardrails/config": { get: { summary: "Get Guardrail Compliance Rules", responses: { "200": { description: "OK" } } } }
          }
        },
        dom_id: '#swagger-ui',
      });
    };
  </script>
</body>
</html>`);
});

// Fallback to Dashboard
app.use((req, res) => {
  res.sendFile(path.join(__dirname, "public", "index.html"));
});

// Start server immediately on port 3000
app.listen(PORT, "0.0.0.0", () => {
  console.log(`AI Revenue Recovery Engine listening on http://0.0.0.0:${PORT}`);
  seedInitialData();
});
