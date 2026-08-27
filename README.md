# ⚡ AI Revenue Recovery System

[![Node.js](https://img.shields.io/badge/Node.js-20%2B%20%7C%2022-339933.svg?logo=nodedotjs)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0%2B-3178C6.svg?logo=typescript)](https://www.typescriptlang.org/)
[![Express](https://img.shields.io/badge/Express-5.0-000000.svg?logo=express)](https://expressjs.com)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

An autonomous, enterprise-grade **AI Revenue Recovery and Dunning Platform**. It seamlessly transitions from real-time telemetry risk detection to root-cause reasoning (LangGraph-style state machine), policy & compliance guardrail validation, multi-channel bounded execution, and an immutable, cryptographically chained financial audit ledger with net ROI attribution.

---

## 📌 Quick Guide Menu

| Section | Description | Quick Link |
| :--- | :--- | :--- |
| **⚡ Quickstart** | Clone, install dependencies & start the dev server | [Jump to Quickstart](#-quickstart-guide) |
| **🧪 Scenarios** | 4 simulated failure & recovery workflows | [Jump to Scenarios](#-interactive-simulation-lab) |
| **🏛️ Architecture** | 5-stage autonomous recovery lifecycle | [Jump to Architecture](#️-end-to-end-system-architecture) |
| **📡 API & Docs** | REST routes, webhook endpoints & Swagger UI | [Jump to REST API](#-rest-api--webhook-endpoints) |
| **⛓️ Audit Ledger** | Cryptographic SHA-256 hash chaining & Net ROI | [Jump to Ledger Info](#5-append-only-financial-audit-ledger--roi-engine) |
| **🛡️ Guardrails** | TCPA compliance & Dispute Killswitch rules | [Jump to Guardrails](#3-policy--compliance-guardrail-engine) |

---

## 🏛️ End-to-End System Architecture

```
[ Data Ingestion / Telemetry ]
  ├── Webhooks (Stripe, Razorpay, Adyen, Chargebee)
  ├── ERP & Accounting Feed (NetSuite, QuickBooks)
  └── App Analytics (Mixpanel, Segment)
              │
              ▼
  [ Risk Detection Engine ]
  ├── Soft-Decline Rule & Pattern Classifier
  ├── Abandoned Checkout Inactivity Detector
  ├── Invoice Aging (30/60/90 Day) Evaluator
  └── Expired Mandate / AutoPay Watcher
              │
              ▼ (Flags Risk Event)
  [ Decision & Diagnosis Agent ]
  ├── Root Cause Analysis (Technical vs. Liquidity vs. Intent)
  ├── Multi-Channel Strategy Selector (Retry vs. Email vs. SMS vs. Voice)
  └── Dynamic Generator (Personalized messaging & Hinglish Voice Script)
              │
              ▼
  [ Policy & Compliance Guardrails ]
  ├── Contact Frequency Cap (Max 3/week, TCPA/GDPR quiet hours)
  ├── Active Dispute / Chargeback Kill-Switch
  ├── Promise-to-Pay (P2P) Cooldown Lock
  └── Human-in-the-Loop Gate for High-Value Overdue Receivables (> $5,000)
              │
              ▼ (Safe & Approved Action)
  [ Execution / Action Layer ]
  ├── Smart Gateway Retry Scheduler (Stripe / Razorpay API)
  ├── Dynamic Recovery Email Dispatcher (SendGrid / Resend)
  ├── SMS Short-Link Dispatcher (Twilio)
  └── Voice AI Agent with Promise-to-Pay Collector (Vapi AI / Twilio Voice)
              │
              ▼
  [ Financial Audit & Analytics Ledger ]
  ├── Cryptographically Chained Append-Only Audit Trail (SHA-256)
  ├── Net ROI Attribution Engine (Recovered $ - Gateway Fees - AI/Comms Cost)
  └── Cohort Analytics & Real-Time Metrics API / Web Dashboard
```

---

## 🚀 Key System Features

### 1. Ingestion & Event Detection
- **Multi-Gateway Webhooks**: Native parsers for Stripe (`payment_intent.payment_failed`, `invoice.payment_failed`), Razorpay (`payment.failed`, `subscription.halted`), and Chargebee.
- **ERP Aging Feed**: Ingestion for NetSuite / QuickBooks batch accounts receivable reports (30, 60, 90+ day delinquency).
- **Risk Classifier**: Separates recoverable soft declines (e.g. `insufficient_funds`, `processing_error`) from hard terminal declines (`stolen_card`, `fraudulent`).

### 2. Diagnosis & Strategy Agent
- **Root-Cause Analysis**: Distinguishes between temporary card limits, customer churn intent, and payment friction.
- **Multilingual & Hinglish Voice Scripts**: Interactive conversational AI prompts for Indian & global enterprise receivables.
- **Dynamic Incentives**: Automated time-bounded discounts (e.g. 5% - 10%) or flexible installment plans for high-ticket carts.

### 3. Policy & Compliance Guardrails
- **Emergency Dispute Kill-Switch**: Halts all outreach immediately if a customer opens a chargeback, ticket, or legal dispute.
- **Contact Frequency Capping**: Hard enforcement of maximum 3 contact attempts per 7-day rolling window.
- **TCPA / TRAI Quiet Hours**: Automatic timezone calculation to prevent night-time calls/SMS (9 PM – 8 AM).
- **Promise-to-Pay (P2P) Freeze**: Pauses automated recovery sequences when a customer commits to pay by a specific date (+ grace period).

### 4. Bounded Action Layer
- **Smart Gateway Retries**: Schedules delayed execution during optimal cardholder liquidity windows (e.g., post-salary 24h backoff).
- **HMAC Dynamic Payment Links**: One-click secure payment links with embedded dynamic discounts and expiration timers.
- **Voice AI Dispatcher**: Initiates outbound voice calls with conversational intent extraction.

### 5. Append-Only Financial Audit Ledger & ROI Engine
- **Cryptographic Hash Chain**: Every transaction, cost, and recovered dollar is chained using SHA-256 (`previous_hash` + `payload` → `current_hash`).
- **Net ROI Attribution**:
  $$\text{Net Recovered Revenue} = \text{Gross Recovered} - \text{Gateway Fees} - \text{Comms Costs} - \text{AI Token Costs}$$
- **1-Click Chain Verification**: Instant endpoint & UI button to prove ledger integrity with zero data tampering.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Language & Runtime** | [Node.js](https://nodejs.org/) (ES Modules) • [TypeScript](https://www.typescriptlang.org/) |
| **Server Framework** | [Express 5](https://expressjs.com/) |
| **Bundling & Execution** | `tsx` (Development) • `esbuild` (Production Bundle) |
| **Frontend UI** | Real-time Dashboard with Tailwind CSS, Chart.js & Vanilla JS |
| **API Documentation** | Interactive Swagger UI (`/docs`) |
| **Cryptographic Ledger** | Node.js `crypto` (SHA-256 hash chaining) |

---

## ⚡ Quickstart Guide

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/yashwanthmadivalara/AI-Revenue-Recovery.git
cd AI-Revenue-Recovery

# Install dependencies
npm install
```

### 2. Configure Environment (Optional)

```bash
cp .env.example .env
```
*(By default, the application runs out-of-the-box on port 3000).*

### 3. Run Development Server

```bash
npm run dev
```

- Open **Web Dashboard**: [http://localhost:3000/](http://localhost:3000/)
- Open **Interactive Swagger API Docs**: [http://localhost:3000/docs](http://localhost:3000/docs)

### 4. Production Build

```bash
npm run build
npm start
```

---

## 🧪 Interactive Simulation Lab

Run the full end-to-end multi-agent recovery lifecycle across four realistic scenarios:

### Supported Scenarios:
1. **`soft_decline`**: Stripe insufficient funds ($450) → Schedules 24h liquidity-optimized gateway retry.
2. **`abandoned_checkout`**: High-value cart ($1,200) → Dispatches personalized email with a 5% dynamic discount link.
3. **`overdue_b2b_hinglish`**: NetSuite 65-day delinquent B2B invoice (₹4,200) → Multilingual Hinglish Voice AI call that negotiates and logs a Promise-to-Pay (P2P) date.
4. **`active_dispute_blocked`**: Open customer chargeback ($1,500) → Emergency compliance kill-switch blocks all automated outreach.

Trigger scenarios via API:
```bash
curl -X POST http://localhost:3000/api/v1/simulator/run/soft_decline
curl -X POST http://localhost:3000/api/v1/simulator/run/abandoned_checkout
curl -X POST http://localhost:3000/api/v1/simulator/run/overdue_b2b_hinglish
curl -X POST http://localhost:3000/api/v1/simulator/run/active_dispute_blocked
```

---

## 📡 REST API & Webhook Endpoints

### System & Documentation
- `GET /api/v1/health` — Engine health status
- `GET /docs` — Interactive Swagger API documentation

### Ingestion Webhooks
- `POST /api/v1/webhooks/stripe` — Ingests raw Stripe webhooks
- `POST /api/v1/webhooks/razorpay` — Ingests raw Razorpay webhooks
- `POST /api/v1/webhooks/chargebee` — Ingests raw Chargebee webhooks
- `POST /api/v1/webhooks/erp` — Ingests NetSuite / QuickBooks batch invoice feeds

### Recovery Operations & Simulation
- `GET /api/v1/simulator/scenarios` — Lists available simulation scenarios
- `POST /api/v1/simulator/run/:scenarioKey` — Executes state machine on a simulation scenario
- `POST /api/v1/recovery/trigger` — Manually triggers end-to-end recovery for any event
- `GET /api/v1/recovery/actions` — Lists recent bounded tool execution logs

### Compliance Guardrails
- `GET /api/v1/guardrails/config` — Retrieves active guardrail rules & limits
- `POST /api/v1/guardrails/evaluate` — Evaluates compliance for a specific customer & channel

### Financial Audit Ledger
- `GET /api/v1/ledger/entries` — Lists append-only audit trail records
- `GET /api/v1/ledger/metrics` — Computes gross recovery, costs, and net ROI
- `GET /api/v1/ledger/cohorts` — Breakdown analysis across cohorts and risk types
- `GET /api/v1/ledger/verify-integrity` — Cryptographically verifies SHA-256 hash chain

---

## 🧪 Linting & Type Checking

Run the TypeScript compiler to verify type safety:

```bash
npm run lint
```

---

## 📄 License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
