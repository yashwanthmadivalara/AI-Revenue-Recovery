# ⚡ AI Revenue Recovery System

[![CI Pipeline](https://github.com/your-org/ai-revenue-recovery/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/ai-revenue-recovery)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker)](https://www.docker.com/)

An autonomous, enterprise-grade **AI Revenue Recovery and Dunning Platform**. It seamlessly transitions from real-time telemetry risk detection to root-cause reasoning (LangGraph), policy & compliance guardrail validation, multi-channel bounded execution, and an immutable, cryptographically chained financial audit ledger with net ROI attribution.

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
  [ Decision & Diagnosis Agent (LangGraph) ]
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

## 🚀 Key System Features & Blueprint

### 1. Ingestion & Event Detection
- **Multi-Gateway Webhooks**: Native parsers for Stripe (`payment_intent.payment_failed`, `invoice.payment_failed`), Razorpay (`payment.failed`, `subscription.halted`), and Chargebee.
- **ERP Aging Feed**: Ingestion for NetSuite / QuickBooks batch accounts receivable reports (30, 60, 90+ day delinquency).
- **Risk Classifier**: Separates recoverable soft declines (e.g. `insufficient_funds`, `processing_error`) from hard terminal declines (`stolen_card`, `fraudulent`).

### 2. Diagnosis & Strategy Agent (LangGraph Reasoning)
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
- **Voice AI Dispatcher**: Initiates outbound Vapi AI / Twilio Voice calls with conversational intent extraction.

### 5. Append-Only Financial Audit Ledger & ROI Engine
- **Cryptographic Hash Chain**: Every transaction, cost, and recovered dollar is chained using SHA-256 (`previous_hash` + `payload` → `current_hash`).
- **Net ROI Attribution**:
  $$\text{Net Recovered Revenue} = \text{Gross Recovered} - \text{Gateway Fees} - \text{Comms Costs} - \text{AI Token Costs}$$
- **1-Click Chain Verification**: Instant endpoint & UI button to prove ledger integrity with zero data tampering.

---

## 🛠️ Tech Stack

| Component | Technology |
| :--- | :--- |
| **Agent Orchestration** | [LangGraph](https://github.com/langchain-ai/langgraph) / LangChain Core |
| **Backend Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python 3.10 - 3.12) |
| **Database & ORM** | SQLAlchemy 2.0 (Async) • SQLite (Default) / PostgreSQL + Redis |
| **Frontend UI** | Real-time Dashboard with Tailwind CSS, Chart.js & Jinja2 |
| **Communication Providers** | Twilio, Vapi AI, Resend, SendGrid (Live hooks + Mock Simulators) |
| **Payment Integrations** | Stripe, Razorpay, Chargebee APIs |
| **Testing & CI** | Pytest, Pytest-Asyncio, Pytest-Cov, GitHub Actions CI |

---

## ⚡ Quickstart Guide

### 1. Clone & Install Dependencies

```bash
git clone https://github.com/your-org/ai-revenue-recovery.git
cd ai-revenue-recovery

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install requirements
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

```bash
cp .env.example .env
```
*(By default, the application runs with zero configuration using SQLite and high-fidelity mock engines. You can optionally add `OPENAI_API_KEY`, `STRIPE_SECRET_KEY`, or `TWILIO_ACCOUNT_SID` for live integrations).*

### 3. Run the Interactive Web Dashboard & Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- Open **Web Dashboard**: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
- Open **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧪 CLI Interactive Simulation Lab

Run the full end-to-end multi-agent recovery lifecycle across all four production scenarios:

```bash
python -m app.cli.demo --scenarios all
```

### Supported Scenarios:
1. **`soft_decline`**: Stripe insufficient funds ($450) → Schedules 24h liquidity-optimized gateway retry.
2. **`abandoned_checkout`**: High-value cart ($1,200) → Dispatches personalized email with a 5% dynamic discount link.
3. **`overdue_b2b_hinglish`**: NetSuite 65-day delinquent B2B invoice (₹4,200) → Multilingual Hinglish Voice AI call that negotiates and logs a Promise-to-Pay (P2P) date.
4. **`active_dispute_blocked`**: Open customer chargeback ($1,500) → Emergency compliance kill-switch blocks all automated outreach.

---

## 🐳 Docker & Docker Compose Deployment

Run the complete production stack (FastAPI Application + PostgreSQL 16 + Redis 7):

```bash
# Build and run containers
docker-compose up --build -d

# View application logs
docker-compose logs -f app

# Stop containers
docker-compose down
```

---

## 📡 REST API & Webhook Endpoints

### Ingestion Webhooks
- `POST /api/v1/webhooks/stripe` — Ingests raw Stripe webhooks
- `POST /api/v1/webhooks/razorpay` — Ingests raw Razorpay webhooks
- `POST /api/v1/webhooks/chargebee` — Ingests raw Chargebee webhooks
- `POST /api/v1/webhooks/erp` — Ingests NetSuite / QuickBooks batch invoice feeds

### Recovery Operations
- `POST /api/v1/recovery/trigger` — Manually triggers end-to-end recovery for any event
- `GET /api/v1/recovery/actions` — Lists recent bounded tool execution logs

### Compliance Guardrails
- `GET /api/v1/guardrails/config` — Retrieves active guardrail rules & limits
- `POST /api/v1/guardrails/evaluate` — Evaluates compliance for a specific customer & channel

### Financial Audit Ledger
- `GET /api/v1/ledger/entries` — Lists append-only audit trail records
- `GET /api/v1/ledger/metrics` — Computes gross recovery, costs, and net ROI
- `GET /api/v1/ledger/cohorts` — Breakdown analysis across cohorts and risk types
- `GET /api/v1/ledger/verify-integrity` — Verifies SHA-256 cryptographic chain integrity

---

## 🧪 Running Automated Tests

Run the full pytest suite with test coverage:

```bash
pytest -v --cov=app tests/
```

---

## 📄 License

This project is licensed under the **Apache License 2.0** — see the [LICENSE](LICENSE) file for details.
