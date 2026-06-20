# 🤖 ChatOps Incident Agent

<div align="center">

[![CI Pipeline](https://img.shields.io/github/actions/workflow/status/omeredry/chatops-incident-agent/ci.yml?branch=main&label=CI%20Pipeline&logo=github-actions&logoColor=white&style=for-the-badge)](https://github.com/omeredry/chatops-incident-agent/actions)
[![Docker Pulls](https://img.shields.io/badge/Docker%20Pulls-GHCR-blue?logo=docker&logoColor=white&style=for-the-badge)](https://github.com/omeredry/chatops-incident-agent/pkgs/container/chatops-incident-agent)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white&style=for-the-badge)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-009688?logo=fastapi&logoColor=white&style=for-the-badge)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**An autonomous, AI-powered incident triage engine that transforms raw alerts into actionable root-cause analysis — in seconds.**

</div>

---

## 📋 Overview

The **ChatOps Incident Agent** is a production-grade, asynchronous backend system that sits at the intersection of DevOps automation and Agentic AI. It ingests incident alerts from platforms like **PagerDuty** and **GitHub** via a FastAPI webhook gateway, then intelligently routes them through a **dual-tier LLM reasoning pipeline** to classify severity, identify root causes, and surface recommended remediation steps — all without human triage.

At its core, the system uses a cost-efficient escalation strategy: **Google Gemini 2.5 Flash** performs high-speed severity classification (P1–P4) for every incoming alert. Only incidents classified as `P1_CRITICAL` or `P2_HIGH` are escalated to **Google Gemini 2.5 Pro** for deep-reasoning analysis, including root cause hypotheses and confidence-scored action plans. This tiered approach delivers enterprise-grade intelligence at scale without burning tokens on low-priority noise.

The entire system is containerized, CI/CD-enabled, and production-ready. A **GitHub Actions pipeline** runs the full test suite on every push, then builds and publishes a multi-stage Docker image to the **GitHub Container Registry (GHCR)**, ready for deployment on Kubernetes (AWS EKS).

---

## 📸 Visual Proof


> <img src="docs/discord-alert-pic-p1.png?v=2" width="330" style="margin: 5px;">
> <img src="docs/discord-alert-pic-p2.png?v=2" width="305" style="margin: 5px;">


> *The Discord notification below is triggered automatically for P1/P2 incidents, showing the AI-generated root cause, severity badge, and recommended actions.*

<!-- Replace this comment with your screenshot: -->
<!-- ![Discord Webhook Alert](docs/assets/discord-alert-screenshot.png) -->

---

## 🏗️ Architecture & Tech Stack

### Event Pipeline

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Incident Sources                             │
│              PagerDuty  ·  GitHub  ·  Custom Webhooks               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │  POST /api/v1/webhooks/incident
                               ▼
                    ┌──────────────────┐
                    │   FastAPI        │
                    │  Webhook Gateway │
                    │  (Async/ASGI)    │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  TIER 1 TRIAGE   │
                    │ Gemini 2.5 Flash │  ──► P3/P4: Return triage summary
                    │  (Fast · Cheap)  │
                    └────────┬─────────┘
                     P1/P2 only
                             │
                    ┌────────▼─────────┐        ┌──────────────────────┐
                    │ TIER 2 ANALYSIS  │        │  Discord Webhook      │
                    │  Gemini 2.5 Pro  │ ──────►│  (P1/P2 Alert Embed) │
                    │ (Deep Reasoning) │        └──────────────────────┘
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   PostgreSQL 15  │
                    │ (Async · asyncpg)│
                    │  Incident State  │
                    └──────────────────┘
```

### Technology Stack

| Layer | Technology | Role |
|---|---|---|
| **API Gateway** | FastAPI 0.111+ · Uvicorn | Async webhook ingestion, request validation, health checks |
| **AI — Tier 1** | Google Gemini 2.5 Flash | High-speed severity classification (P1–P4) |
| **AI — Tier 2** | Google Gemini 2.5 Pro | Deep root-cause analysis, remediation recommendations |
| **Database** | PostgreSQL 15 · asyncpg · SQLAlchemy 2.0 | Persistent incident state, message history (async ORM) |
| **Notifications** | Discord Webhooks | Color-coded P1/P2 alert embeds delivered in real time |
| **Alerting Source** | PagerDuty · GitHub · Custom | Structured webhook payload with source tagging |
| **Containerization** | Docker (multi-stage) · Docker Compose | Reproducible builds, local dev orchestration |
| **CI/CD** | GitHub Actions | Automated test → build → push pipeline |
| **Registry** | GitHub Container Registry (GHCR) | Versioned Docker image hosting (`ghcr.io`) |
| **Orchestration** | Kubernetes (AWS EKS) | Production-grade deployment target |
| **Data Validation** | Pydantic v2 · pydantic-settings | Strict type enforcement on all API boundaries and config |

---

## ✨ Key Features

### 🧠 Agentic Dual-LLM Root-Cause Analysis
The system implements an intelligent **escalation router** that automatically decides which AI model to engage based on incident severity. P3/P4 alerts receive instant, low-cost triage summaries. P1/P2 alerts trigger a second AI agent that reasons over the alert, hypothesizes the root cause, and returns a confidence-scored list of 2–5 recommended remediation actions. No human triage required.

### ⚡ Fully Asynchronous, Event-Driven Design
Every I/O operation — LLM API calls, database reads/writes, Discord notifications — is non-blocking. Built on Python's `asyncio` with `asyncpg` for direct PostgreSQL connections and FastAPI's `BackgroundTasks` for fire-and-forget Discord alerts. The event loop is never blocked, enabling high throughput under real-world incident load.

### 🔧 Structured Severity Classification
Incoming alerts are classified into a four-tier severity model:

| Severity | Label | Action |
|---|---|---|
| 🔴 | `P1_CRITICAL` | Tier-2 deep analysis + Discord alert |
| 🟠 | `P2_HIGH` | Tier-2 deep analysis + Discord alert |
| 🟡 | `P3_WARNING` | Tier-1 triage summary only |
| 🔵 | `P4_INFO` | Tier-1 triage summary only |

### 🚀 Automated CI/CD Pipeline
Every push to `main` triggers a **GitHub Actions** workflow that:
1. Runs the full `pytest` suite against a clean environment
2. Builds a hardened, multi-stage Docker image
3. Authenticates and pushes the image to **GHCR** (`ghcr.io/omeredry/chatops-incident-agent:latest`)

No manual builds. No deployment drift.

### 🛡️ Production-Grade Engineering Practices
- **Strict type safety** — full Pydantic v2 validation on every API boundary and every config key
- **Structured logging** — explicit `try/except` and `logging.getLogger` on all external API calls
- **Database integrity** — parameterized async queries, UUID primary keys, enum-validated status/severity columns
- **Container-first** — multi-stage Docker build minimizes final image size; health checks wired into Compose

---

## ⚙️ Environment Configuration

Copy the example file and populate your secrets:

```bash
cp .env.example .env
```

```ini
# .env.example

# Application
APP_NAME=ChatOps Incident Agent
APP_ENVIRONMENT=development   # development | staging | production
APP_DEBUG=False

# AI Services
GEMINI_API_KEY=your-gemini-api-key-here

# Notifications
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your_long_token_here

# Database
# Use DB_HOST=db when running via Docker Compose (matches service name)
# Use DB_HOST=localhost for local development outside Docker
DB_HOST=db
DB_PORT=5432
DB_USER=chatops_user
DB_PASSWORD=chatops_password
DB_NAME=chatops_db
```

> **Note:** `GEMINI_API_KEY` and `DISCORD_WEBHOOK_URL` are the only values that must be supplied before the system is functional. All other defaults work out-of-the-box with Docker Compose.

---

## 🚀 Quick Start

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/) installed
- A [Google Gemini API key](https://aistudio.google.com/app/apikey)
- A [Discord Webhook URL](https://support.discord.com/hc/en-us/articles/228383668) (for P1/P2 alerts)

### 1. Clone the repository

```bash
git clone https://github.com/omeredry/chatops-incident-agent.git
cd chatops-incident-agent
```

### 2. Configure environment variables

```bash
cp .env.example .env
# Open .env and fill in GEMINI_API_KEY and DISCORD_WEBHOOK_URL
```

### 3. Start all services

```bash
docker compose up -d
```

This spins up two containers:
- **`db`** — PostgreSQL 15 with automatic schema initialization
- **`api`** — FastAPI application on port `8000`

### 4. Verify the service is healthy

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","service":"chatops-agent"}
```

### 5. Send a test incident

```bash
curl -X POST http://localhost:8000/api/v1/webhooks/incident \
  -H "Content-Type: application/json" \
  -d '{
    "source": "pagerduty",
    "incident_id": "INC-001",
    "title": "Production database OOMKilled — pod restarting 50+ times",
    "description": "PostgreSQL pod in namespace prod-us-east-1 has exceeded memory limits.",
    "raw_data": {}
  }'
```

A `P1_CRITICAL` or `P2_HIGH` response will include a full `deep_analysis` block and trigger a Discord alert:

```json
{
  "summary": "...",
  "severity": "P1_CRITICAL",
  "reasoning": "...",
  "routed_to_claude": true,
  "deep_analysis": {
    "root_cause": "...",
    "recommended_actions": ["...", "..."],
    "confidence": "high"
  }
}
```

---

## 📂 Project Structure

```
chatops-incident-agent/
├── .github/workflows/ci.yml   # GitHub Actions: test → build → push
├── docker/
│   └── Dockerfile             # Multi-stage Python 3.11 build
├── docker-compose.yml         # Local dev: api + postgres
├── docs/
│   └── architecture.md        # Detailed system design documentation
├── k8s/                       # Kubernetes manifests (AWS EKS)
├── src/
│   ├── main.py                # FastAPI app entrypoint + lifespan
│   ├── api/
│   │   ├── routes.py          # POST /api/v1/webhooks/incident
│   │   └── schemas.py         # Pydantic request/response models
│   ├── core/config.py         # pydantic-settings environment config
│   ├── db/
│   │   ├── engine.py          # SQLAlchemy async engine + session factory
│   │   └── models.py          # Incident, IncidentMessage ORM models
│   └── services/
│       ├── router.py          # Escalation orchestration logic
│       ├── gemini_service.py  # Tier-1: Gemini Flash triage
│       ├── analysis_service.py# Tier-2: Gemini Pro deep analysis
│       └── discord.py         # Async Discord webhook notifications
└── tests/
    └── test_api.py            # Async API tests (pytest + httpx)
```

---

## 🤝 Contributing

Issues and pull requests are welcome. Please open an issue first to discuss significant changes.

---

<div align="center">

Built with Python 3.11 · FastAPI · Google Gemini · PostgreSQL · Docker · GitHub Actions

</div>
