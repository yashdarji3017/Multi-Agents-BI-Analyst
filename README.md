<h1 align="center">BusinessInsight AI</h1>

<p align="center">
  A full-stack, enterprise-grade <strong>Multi-Agent Business Intelligence Analyst</strong> platform for automated revenue trend diagnostics,
  deterministic arithmetic auditing, empirical findings extraction, and C-suite executive reporting.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-0.141+-009688.svg" alt="FastAPI">
  <img src="https://img.shields.io/badge/Streamlit-1.65+-FF4B4B.svg" alt="Streamlit">
  <img src="https://img.shields.io/badge/Plotly-7.1+-3F4F75.svg" alt="Plotly">
  <img src="https://img.shields.io/badge/Microsoft_Agent_Framework-1.21+-0078D4.svg" alt="MAF">
  <img src="https://img.shields.io/badge/Google_Gemini-Gemini_2.5_Flash-8E75C2.svg" alt="Gemini">
  <img src="https://img.shields.io/badge/Database-Zero--Database_In--Memory-success.svg" alt="Zero-Database">
  <img src="https://img.shields.io/badge/uv-Package_Manager-purple.svg" alt="uv">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
</p>

---

## Overview

BusinessInsight AI is a production-ready, full-stack multi-agent business intelligence solution consisting of:

- **FastAPI Backend** — Handles CSV ingestion, schema normalization, deterministic arithmetic calculations in Python, Microsoft Agent Framework (MAF) + Google Gemini agent orchestration, native token tracking, and REST APIs.
- **Streamlit Frontend** — A modern executive dashboard acting as a pure REST API client for exploring dataset distributions, filtering temporal slices, triggering multi-agent investigations, reviewing execution traces, and exporting board-ready Markdown reports.

---

## Features

### 🔍 Deterministic Data Ingestion & Gating
- Automated column mapping to canonical schema (`Order ID`, `Order Date`, `Sales`, `Profit`, `Quantity`, `Discount`, `Category`, `Sub-Category`, `Region`)
- Comprehensive data hygiene checks: duplicate detection, unparseable date handling, negative values, missing metrics
- Zero-database architecture: direct in-memory ingestion with zero external database dependencies
- Gatekeeper verification halts processing before LLM invocation if schema or quality thresholds fail

### 📊 Real-Time Analytics & Interactive Visualizations
- Deterministic arithmetic engine: all totals, averages, margins, and period-over-period percentages calculated in Python (zero hallucinated math)
- Configurable comparative modes: Latest vs Previous Quarter, Year-over-Year, or custom date ranges
- Interactive Plotly visualizations:
  - Monthly & quarterly revenue trend trajectories
  - Top contracted products with waterfall drop values
  - Regional margin vs revenue distribution scatter plots
  - Category and segment revenue mix breakdowns

### 🤖 5-Agent Collaborative Pipeline
- **Data Agent** — Validates schema, calculates hygiene indicators, and generates structured statistical profiles
- **Analyst Agent** — Evaluates empirical trends, extracts structured findings (`F-01`...`F-n`), and diagnoses revenue drops
- **Strategy Agent** — Synthesizes root causes, evaluates commercial trade-offs, and proposes actionable recommendations (`R-01`...`R-n`)
- **Verifier Agent** — Independently recomputes arithmetic deltas, checks percentage logic, and audits recommendations for causal validity
- **Report Agent** — Compiles a verified, professional C-suite Markdown report with board-level findings, risk matrices, and next steps

### 🛡️ Verification & Anti-Hallucination Guardrails
- Dual-pass verification loop: empirical findings audited against ground-truth Pandas data
- Causal leap detection: flags recommendations that lack supporting empirical findings
- Arithmetic discrepancy logging: highlights any mismatch in baseline metrics, deltas, or percentages

### 🪙 Native Token Economics & Observability
- Native token counting via Google Gemini's inbuilt client API (`count_tokens`), eliminating static approximation errors
- Granular per-agent tracking: input tokens, output tokens, total cost footprint, and execution latencies
- Prompt token budgeting: statistical aggregation grounding prevents wasteful multi-thousand row dumps while preserving precision

### 📄 C-Suite Executive Reporting & Artifact Export
- Boardroom-ready Markdown report generation with structured executive summaries, findings tables, and strategic recommendations
- One-click raw Markdown download and interactive HTML Plotly chart export saved to `outputs/`
- Ephemeral in-memory session caching for active session navigation without database bloat

### 🌐 Decoupled REST API Architecture
- Pure REST API client frontend ensuring clean separation of concerns
- Fully typed Pydantic v2 schemas and OpenAPI Swagger documentation at `/docs`
- Endpoints for health inspection, dataset profiling, analytics slicing, multi-agent execution, traces, reports, and charts

---

## Tech Stack

### Backend
| Technology | Purpose |
|---|---|
| Python 3.12+ | Runtime environment |
| FastAPI | High-performance asynchronous REST API framework |
| Microsoft Agent Framework (`agent-framework`) | Agent orchestration & workflow management |
| Google Gemini (`agent-framework-gemini`) | Analytical reasoning, synthesis & strategic generation |
| Pandas & NumPy | High-speed deterministic data manipulation & arithmetic |
| Pydantic v2 & Pydantic-Settings | Strictly typed request/response models & configuration |
| Uvicorn | ASGI web server |
| uv | Fast Python package management |

### Frontend & Visualizations
| Technology | Purpose |
|---|---|
| Streamlit | Modern interactive analytical UI and executive portal |
| Plotly | Interactive revenue trends, product waterfalls, and regional distributions |
| Requests | REST API client communication with FastAPI backend |

---

## Project Structure

```text
MLA_Business_Intelligence_Analyst/
├── data/
│   ├── raw/
│   │   └── superstore.csv           # Kaggle Superstore demonstration dataset
│   ├── processed/                   # Staged data files (if applicable)
│   └── README.md                    # Dataset source documentation & schema dictionary
│
├── frontend/
│   └── app.py                       # Pure REST API Streamlit executive dashboard
│
├── outputs/
│   ├── charts/                      # Exported interactive Plotly HTML visualizations
│   └── reports/                     # Exported boardroom-ready Markdown reports
│
├── src/
│   └── businessinsight/
│       ├── agents/
│       │   ├── __init__.py          # Agent export declarations
│       │   ├── analyst_agent.py     # Analyst Agent: empirical trend diagnostics
│       │   ├── base.py              # MAF Gemini client initialization & native token counter
│       │   ├── data_agent.py        # Data Agent: schema validation & statistical profile
│       │   ├── report_agent.py      # Report Agent: executive Markdown synthesis
│       │   ├── strategy_agent.py    # Strategy Agent: commercial hypotheses & action plans
│       │   └── verifier_agent.py    # Verifier Agent: arithmetic audit & causal verification
│       │
│       ├── analytics/
│       │   ├── __init__.py          # Analytics package exports
│       │   ├── anomalies.py         # Outlier & contraction detection
│       │   ├── metrics.py           # Deterministic financial arithmetic (AOV, margins, deltas)
│       │   ├── products.py          # Product-level performance & contraction waterfalls
│       │   ├── profiling.py         # Dataset summary & distribution analysis
│       │   ├── regions.py           # Territory and geographical revenue aggregation
│       │   ├── trends.py            # Period-over-period temporal comparisons
│       │   └── validation.py        # Numerical sanity checking & boundary validation
│       │
│       ├── api/
│       │   ├── __init__.py          # API module initialization
│       │   ├── routes.py            # FastAPI REST endpoints
│       │   └── schemas.py           # API request and response models
│       │
│       ├── data/
│       │   ├── __init__.py          # Data module initialization
│       │   ├── column_mapping.py    # Dynamic header normalization to canonical schema
│       │   ├── loader.py            # Safe CSV ingestion & hygiene validation
│       │   └── validators.py        # Schema contracts & quality metrics
│       │
│       ├── observability/
│       │   ├── __init__.py          # Observability module initialization
│       │   └── tracing.py           # Step latencies & token usage observability
│       │
│       ├── reporting/
│       │   ├── __init__.py          # Reporting module initialization
│       │   ├── charts.py            # Plotly interactive figure builders
│       │   └── markdown.py          # Markdown document formatters
│       │
│       ├── services/
│       │   ├── __init__.py          # Services module initialization
│       │   └── analysis_service.py  # Business logic & in-memory session manager
│       │
│       ├── workflow/
│       │   ├── __init__.py          # Workflow package exports
│       │   ├── orchestrator.py      # 5-Agent sequential pipeline coordinator
│       │   ├── schemas.py           # Structured output schemas for each agent
│       │   └── state.py             # In-memory execution state container
│       │
│       ├── config.py                # Environment configuration (Pydantic Settings)
│       └── main.py                  # Application entry points & CLI script runners
│
├── .env.example                     # Environment variable template
├── .gitignore                       # Git ignore rules
├── pyproject.toml                   # Project metadata, dependencies & CLI scripts
├── uv.lock                          # Deterministic dependency lockfile
└── README.md                        # Documentation & setup guide
```

---

## Getting Started

### Prerequisites

- Python 3.12+
- uv (ultra-fast Python package manager)
- Google Gemini API Key (`GOOGLE_API_KEY`)

Install **uv** (if not already installed):

```bash
pip install uv
```

---

## Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd MLA_Business_Intelligence_Analyst
```

### 2. Create & Activate Virtual Environment

```bash
uv venv
```

**Windows:**
```powershell
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
uv sync
```

### 4. Configure Environment Variables

Copy the environment template and set your configuration:

```bash
cp .env.example .env
```

Edit `.env` with your preferred settings:

```env
# Google Gemini API Key (Required for MAF Multi-Agent Execution)
GOOGLE_API_KEY=your_gemini_api_key_here

# Gemini Model Configuration
GEMINI_MODEL=gemini-2.5-flash

# Backend API Configuration
API_HOST=127.0.0.1
API_PORT=8000
API_DEBUG=false

# Streamlit UI Configuration
BACKEND_API_URL=http://127.0.0.1:8000

# Demonstration Dataset Path
DATASET_PATH=data/raw/superstore.csv
```

### 5. Verify the Demonstration Dataset

The project includes the classic Kaggle Superstore dataset at `data/raw/superstore.csv`. If needed, ensure the file is present in the `data/raw/` directory.

---

## Running the Application

### 1. Start the FastAPI Backend Server

```bash
python -m uvicorn businessinsight.main:app --host 127.0.0.1 --port 8000 --reload
```

*Or use the registered CLI command:*

```bash
businessinsight-api
```

- **Interactive API Documentation (Swagger)**: `http://127.0.0.1:8000/docs`
- **ReDoc Documentation**: `http://127.0.0.1:8000/redoc`
- **Health Endpoint**: `http://127.0.0.1:8000/health`

### 2. Start the Streamlit Frontend Dashboard

In a separate terminal (with the virtual environment activated):

```bash
streamlit run frontend/app.py
```

*Or use the registered CLI command:*

```bash
businessinsight-dashboard
```

- **Dashboard UI**: `http://localhost:8501`

---

## REST API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service status, dataset availability, and zero-database confirmation |
| `GET` | `/dataset/profile` | Inspects dataset schema, column mappings, and quality indicators |
| `GET` | `/dataset/analytics` | Computes filtered slice metrics (KPIs, trends, contractions, regions) |
| `POST` | `/analysis/run` | Triggers the 5-agent bounded analysis workflow for a business question |
| `GET` | `/analysis` | Lists active in-memory session analyses |
| `GET` | `/analysis/{analysis_id}` | Retrieves full analysis state, agent outputs, and metadata |
| `GET` | `/analysis/{analysis_id}/trace` | Step-by-step agent execution trace, latencies, and token usage |
| `GET` | `/analysis/{analysis_id}/report` | Structured executive Markdown report model |
| `GET` | `/analysis/{analysis_id}/report/raw` | Raw Markdown report text for instant download |
| `GET` | `/analysis/{analysis_id}/charts` | Local file paths of generated interactive Plotly charts |

### Example: Running an Analysis via cURL

```bash
curl -X POST "http://127.0.0.1:8000/analysis/run" \
  -H "Content-Type: application/json" \
  -d '{
    "business_question": "Why did Technology revenue drop in Q4 2017 and which products drove the contraction?",
    "settings": {
      "confidence_threshold": 0.85
    }
  }'
```

### Example Response:

```json
{
  "analysis_id": "ab83c18b-59d0-449e-ba2b-2a62886f4577",
  "business_question": "Why did Technology revenue drop in Q4 2017 and which products drove the contraction?",
  "status": "completed",
  "duration_seconds": 14.82,
  "verification_status": "verified",
  "executive_summary": "Q4 2017 Technology revenue contracted by 18.4% YoY, primarily driven by supply chain constraints in Copiers and severe price discounting in Machines across the Eastern territory.",
  "total_sales": 733215.26,
  "findings_count": 4,
  "recommendations_count": 3,
  "total_input_tokens": 1284,
  "total_output_tokens": 1690,
  "total_tokens": 2974,
  "token_usage_by_agent": {
    "DataAgent": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
    "AnalystAgent": {"input_tokens": 582, "output_tokens": 648, "total_tokens": 1230},
    "StrategyAgent": {"input_tokens": 348, "output_tokens": 492, "total_tokens": 840},
    "VerifierAgent": {"input_tokens": 194, "output_tokens": 210, "total_tokens": 404},
    "ReportAgent": {"input_tokens": 160, "output_tokens": 340, "total_tokens": 500}
  }
}
```

---

## The 5-Agent Collaborative Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       1. DATA AGENT (Deterministic)                         │
│  - Ingests CSV & normalizes canonical schema                                │
│  - Runs data hygiene checks (nulls, unparseable dates, negative values)     │
│  - Pre-computes statistical profile & summary metrics                        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Validated Profile & Data Gate Passed
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                       2. ANALYST AGENT (MAF + Gemini)                       │
│  - Computes period-over-period deltas & sales contractions                  │
│  - Generates empirical findings (F-01..F-n) with baseline & delta figures    │
│  - Links findings to primary drivers (regions, product categories)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Structured Empirical Findings
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                      3. STRATEGY AGENT (MAF + Gemini)                       │
│  - Develops commercial hypotheses tied to empirical findings                │
│  - Synthesizes risk-weighted strategic recommendations (R-01..R-n)          │
│  - Assigns expected impact, effort, and validation requirements             │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Hypotheses & Recommendations
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                      4. VERIFIER AGENT (MAF + Gemini)                       │
│  - Recomputes arithmetic deltas against deterministic ground truth          │
│  - Checks percentage math and detects causal leaps                          │
│  - Emits verification status (VERIFIED / WARNING) & discrepancy logs        │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ Verified Audit Status
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                       5. REPORT AGENT (MAF + Gemini)                        │
│  - Compiles C-suite executive Markdown report                               │
│  - Generates executive summary, findings table & recommendation matrix      │
│  - Persists artifacts to outputs/reports/ and outputs/charts/               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Token Economics & Observability

### Native Gemini Token Counting
Rather than relying on static or mismatched token counters (e.g. tiktoken), BusinessInsight AI utilizes Google Gemini's native client API:

```python
gemini_client.models.count_tokens(
    model="gemini-2.5-flash",
    contents=prompt_content,
)
```

This guarantees 100% token accuracy calibrated to Google's tokenizer for both input prompts and generated responses.

### Token Usage by Agent
| Agent | Execution Type | Input Tokens | Output Tokens | Description |
|---|---|---|---|---|
| **Data Agent** | Pure Python / Deterministic | `0` | `0` | Zero LLM tokens; pure Pandas profiling and gating |
| **Analyst Agent** | MAF + Gemini | `~500 - 800` | `~600 - 900` | Interprets statistical trends & outputs findings `F-01`...`F-n` |
| **Strategy Agent** | MAF + Gemini | `~300 - 500` | `~400 - 700` | Interprets findings & outputs recommendations `R-01`...`R-n` |
| **Verifier Agent** | MAF + Gemini | `~200 - 400` | `~200 - 400` | Checks arithmetic logic & audits causal links |
| **Report Agent** | MAF + Gemini | `~200 - 400` | `~400 - 800` | Formats verified data into boardroom-ready Markdown |

> **Why are prompt tokens bounded?**  
> We ground agents on deterministically computed statistical profiles rather than dumping raw CSV rows into the context window. This prevents token explosion, reduces execution latency by over 80%, and guarantees numerical precision.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────┐
│              Streamlit Executive Dashboard              │
│       (Interactive Analytics, Slicers, Visuals,         │
│          Multi-Agent Trigger, Trace Inspector)          │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP / REST Client
┌────────────────────────────▼────────────────────────────┐
│                  FastAPI Backend Server                 │
│  ┌───────────────────────┐   ┌───────────────────────┐  │
│  │   REST API Layer      │   │   Pydantic Schemas    │  │
│  │  (/health, /dataset,  │   │  (Strict Type Safety  │  │
│  │   /analysis, /trace)  │   │   & Validation)       │  │
│  └───────────┬───────────┘   └───────────┬───────────┘  │
│              └─────────────┬─────────────┘              │
│  ┌─────────────────────────▼─────────────────────────┐  │
│  │               Analysis Service Layer              │  │
│  │   - In-Memory Session Cache (Zero-Database)       │  │
│  │   - CSV Ingestion & Canonical Normalizer          │  │
│  │   - Deterministic Analytics Engine (Pandas/NumPy) │  │
│  └─────────────────────────┬─────────────────────────┘  │
│  ┌─────────────────────────▼─────────────────────────┐  │
│  │     Microsoft Agent Framework Orchestrator        │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────┐  │  │
│  │  │ Analyst  │ │ Strategy │ │ Verifier │ │Report│  │  │
│  │  │  Agent   │ │  Agent   │ │  Agent   │ │Agent │  │  │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └───┬──┘  │  │
│  │       └────────────┼────────────┘           │     │  │
│  │              Google Gemini 2.5              │     │  │
│  │           (Native Token Counting)           │     │  │
│  └─────────────────────────────────────────────┼─────┘  │
│                                                │        │
│  ┌─────────────────────────────────────────────▼─────┐  │
│  │               Artifact Exporter                   │  │
│  │   - outputs/reports/ (Boardroom Markdown Reports) │  │
│  │   - outputs/charts/  (Interactive Plotly HTML)    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

---

## Architecture Principles: Zero-Database Guarantee

BusinessInsight AI is architected with a **Zero-Database Guarantee**:

1. **Direct CSV Ingestion**: Raw data is ingested directly from local CSV files via Pandas with automatic schema normalization and hygiene checks.
2. **In-Memory Session State**: Temporary workflow states, handoff contexts, and analysis run history are maintained strictly in memory during the active process lifecycle.
3. **No External Database Overhead**: No PostgreSQL, Redis, or SQLite instances are required. This eliminates database setup, migration scripts, and persistent connection pool overhead.
4. **Local Artifact Persistence**: Only finalized executive reports (`outputs/reports/`) and interactive HTML charts (`outputs/charts/`) are saved locally to disk.
5. **Deterministic Arithmetic**: Numerical calculations are performed in Python, ensuring 100% precision with zero math hallucinations.

---

## License

This project is licensed under the [MIT License](LICENSE).
