# 🏎️ F1 Race Intelligence Platform

An end-to-end Formula 1 race analytics platform combining telemetry analysis, tyre degradation prediction, and multi-agent AI pit strategy simulation.

## 🏛️ Repository Architecture

```text
f1-platform/
├── services/       # Go microservices and Python AI services
├── ml/             # ML models, training, and data pipelines
├── data/           # Local telemetry data and cache
├── proto/          # gRPC Protocol Buffer contracts
├── web/            # React + TypeScript dashboard
├── infra/          # Docker Compose and monitoring
├── docs/           # Architecture and technical documentation
├── .env.example
├── docker-compose.yml
├── F1_PLATFORM_PLAN.md
├── PROGRESS.md
└── README.md
```

## 📋 Prerequisites

- Docker Desktop and Docker Compose v2
- Python 3.10+
- Go 1.22+
- Node.js 18+ and npm
- Git

## 🚀 How to Start the Stack

### 1. Environment Setup

**Windows CMD:**
```cmd
copy .env.example .env
```

**PowerShell / Linux:**
```bash
cp .env.example .env
```

### 2. Start Infrastructure

```bash
docker compose up -d
```

### 3. Verify Services

```bash
docker compose ps
```

Check container health and inspect logs if any service fails:

```bash
docker compose logs -f
```

## 🧪 ML & Telemetry Pipeline

### 1. Set Up Python Environment

```bash
cd ml
python -m venv .venv
```

**Windows PowerShell:**
```powershell
.\.venv\Scripts\Activate.ps1
```

**Linux / macOS:**
```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Run FastF1 Smoke Test

```bash
python smoke-test.py
```

This test should verify telemetry retrieval and local caching.

## 🏁 Core Features

- Driver telemetry comparison
- Tyre degradation prediction
- Pit-stop decision support
- LangGraph multi-agent race strategy
- LangChain and RAG integration
- Qdrant vector search and Neo4j knowledge graph
- RabbitMQ asynchronous messaging
- REST, gRPC, and SOAP integrations
- Databricks data processing

## 📈 Roadmap & Progress

- [F1_PLATFORM_PLAN.md](F1_PLATFORM_PLAN.md) — Architecture and implementation roadmap.
- [PROGRESS.md](PROGRESS.md) — Current progress, completed tasks, and next steps.

## ⚠️ Note

The platform is intended initially for historical telemetry analysis and simulated race scenarios. Live predictions require an appropriate data feed and validated machine-learning models.
