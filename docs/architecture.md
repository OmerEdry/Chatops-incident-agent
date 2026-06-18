# System Architecture: ChatOps Incident Management Agent

## 1. Overview
The ChatOps Incident Management Agent is an asynchronous, containerized backend system designed to streamline incident triage and analysis for engineering teams. It integrates messaging platforms (Telegram/WhatsApp) with an intelligent, dual-LLM routing engine to classify and resolve infrastructure alerts.

## 2. System Architecture Components


* **Gateway Layer (FastAPI):** Asynchronous API gateway responsible for handling incoming webhooks from Telegram and WhatsApp.
* **Routing Engine:**
    * **Tier 1 (Gemini):** High-speed classification. Analyzes the incoming payload to determine severity (Critical, Warning, Info) and intent.
    * **Tier 2 (Claude):** Deep Reasoning. Triggered by Tier 1 for complex alerts requiring log analysis, root cause suggestion, or cross-referencing documentation.
* **Data Layer (PostgreSQL):** Stores incident states, user session logs, and conversation history. Provides relational integrity for incident tracking.
* **Infrastructure:**
    * **Orchestration:** Docker Compose for local development; Kubernetes (EKS) for production.
    * **Deployment:** Containerized microservices ensuring environment consistency.

## 3. Data Flow
1.  **Ingestion:** User sends an alert log/message via messaging platform.
2.  **Triage:** FastAPI receives the request -> Gemini classifies the incident.
3.  **Analysis:** If classified as 'Complex', request is forwarded to Claude with context retrieved from PostgreSQL.
4.  **Response:** The agent returns a synthesized summary/fix proposal to the user via the original platform.
5.  **Persistence:** All exchanges are saved in PostgreSQL to maintain session state and build a knowledge base of past incidents.

## 4. Development Standards
* **Asynchronous First:** All I/O operations (API calls, DB queries) must be non-blocking.
* **Type Safety:** Strict use of Pydantic models for data validation.
* **Infrastructure as Code:** All infrastructure configurations must be version-controlled in the `k8s/` and `docker/` directories.

## 5. Project Directory Structure
The following structure must be maintained to ensure modularity and clean separation of concerns:

chatops-incident-agent/
├── .github/          # CI/CD workflows
├── docs/             # Documentation
├── src/              # Core application logic
│   ├── api/          # FastAPI routes
│   ├── core/         # Config, security, and router logic
│   ├── db/           # PostgreSQL connection and models
│   ├── services/     # Business logic (LLM integration)
│   └── main.py       # Application entry point
├── tests/            # Pytest and Playwright test suites
├── docker/           # Dockerfiles and docker-compose.yml
└── k8s/              # Kubernetes manifests