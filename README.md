# AarthSaathi — Your Digital Financial Companion

> *The AI financial companion that protects people before it teaches them.*

Built for **Nomura KakushIN Coding Contest 2026** | Team: **Byte Me**

---

## What is AarthSaathi?

AarthSaathi is an AI-powered Financial Literacy Companion for Indian households, built on a RAG-powered multi-agent architecture.

It does not tell people what to do with money — it teaches them **HOW to think about money**, protecting them before empowering them.

**Core insight:** Indian household finance is FAMILIAL, not individual. One salary carries obligations for parents, children, and extended family. Generic rules like "save 20%" are useless and guilt-inducing. No existing product accounts for this reality.

AarthSaathi never recommends financial products — it recommends **learning paths** and **verified educational resources** grounded in RBI, SEBI, and IRDAI content, reducing hallucinations and ensuring full compliance with Indian financial regulations.

---

## The Problem

Only **27% of Indians** demonstrate basic financial literacy (RBI, 2023), yet India has 500M+ UPI users. The gap is not access — it is **understanding**.

| Persona | Profile | Core Problem |
|---------|---------|-------------|
| **Priya** | 32-yr teacher, ₹35,000/month | Sold products she doesn't understand, no trusted advisor |
| **Rajesh** | 24-yr gig worker, variable income | Predatory loan apps, no emergency fund, debt traps |
| **Divya** | 28-yr visually impaired professional | Financial apps inaccessible, compromised independence |

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Honest Budget Builder** | Real surplus after ALL family obligations — no generic rules |
| **Financial Readiness Score** | Stabilize first or invest — transparent, explained verdict |
| **Scam Literacy Module** | Teaches scam psychology BEFORE any investment education |
| **Investment Education** | SIP, FD, EPF, insurance with official verify links |
| **Monthly Expense Tracker** | Tracks spending with festival and variable expense support |
| **Government Scheme Navigator** | PM-KISAN, Jan Dhan, Atal Pension — eligibility and guidance |
| **Daily Financial News** | One simplified news item daily — plain language + audio |
| **Multilingual + Voice** | English, Hindi, Marathi, Kannada support |

---

## Guardian Agent Network

| Guardian Agent | Responsibility |
|----------------|----------------|
| **Family Context Agent** | Models income, obligations, dependents and goals |
| **Financial Health Agent** | Honest surplus, readiness score, stabilize-first verdict |
| **Scam Protection Agent** | Scam psychology and real vs fake comparison — BEFORE investment education |
| **Learning Agent** | RAG-grounded SIP, FD, EPF education with SEBI/RBI verify links |
| **Story Agent** | Audio/visual financial stories — common, best and worst case |
| **Government Scheme Agent** | PM-KISAN, Jan Dhan, Atal Pension eligibility and guidance |
| **News Agent** | Daily simplified financial news with audio output |
| **Accessibility Agent** | Voice input, multilingual output, screen-reader compatible |
| **Verification Agent** | Guard Rails — always-ON, blocks harmful phrases in every output |

---

## Architecture

```
USER INPUT (Voice / Text / OCR)
         │
         ▼
┌─────────────────────────────┐
│      INPUT LAYER            │
│  Voice · OCR · Text · TTS   │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────────────────┐
│      ORCHESTRATOR           │
│   LangGraph State Machine   │
└──────────────┬──────────────┘
               │
    ┌──────────▼──────────┐
    │    ENGINE LAYER      │  ← Deterministic · Pure Python · No AI
    │  Life Context        │
    │  Bifurcation         │
    │  Calculation         │
    │  Readiness Score     │
    └──────────┬───────────┘
               │
    ┌──────────▼──────────┐
    │    AGENT LAYER       │  ← Llama 3.1 via Groq · RAG-grounded
    │  Scam Protection     │
    │  Learning            │
    │  Story               │
    │  Scheme Navigator    │
    │  News                │
    └──────────┬───────────┘
               │
               ▼
┌─────────────────────────────┐
│   PERSONALISED DASHBOARD    │
│  Budget · Verdict · Learn   │
│  Voice-Ready · Accessible   │
└─────────────────────────────┘
               │
┌─────────────────────────────┐  ← Always-ON
│      GUARD RAILS LAYER      │     Wraps every agent output
│  Blocks harmful phrases      │     Filters before user sees it
└─────────────────────────────┘

DATA & STORAGE LAYER
  Session State (Streamlit)  →  RAG Knowledge Base (ChromaDB)  →  Groq Cloud API
```

---

## Project Structure

```
nomura-hackathon/
│
├── main.py                      # Streamlit frontend — 6 pages
│
├── agents/
│   ├── education_agent.py       # Teaches SIP, FD, EPF, insurance
│   ├── scam_literacy_agent.py   # Scam awareness and red flags
│   └── story_agent.py           # Financial stories — common/best/worst
│
├── engines/                     # Deterministic — no AI
│   ├── calculation.py           # Honest budget calculation
│   ├── bifurcation.py           # Fixed vs variable income
│   └── readiness_score.py       # Financial readiness scoring
│
├── layers/
│   └── guardrails.py            # Always-ON safety filter
│
├── orchestrator/
│   └── graph.py                 # LangGraph multi-agent pipeline
│
├── data/
│   ├── scam_patterns.json       # 7 Indian scam patterns
│   ├── stories.json             # 9 financial stories
│   └── schemes.json             # 5 government schemes
│
├── api/
│   ├── main.py                  # FastAPI backend
│   ├── routes.py                # API endpoints
│   ├── auth.py                  # API key authentication
│   └── dependencies.py          # Shared dependencies
│
├── config/
│   ├── settings.py              # App configuration
│   ├── paths.py                 # File paths
│   └── logging_config.py        # Logging setup
│
├── .env.example                 # Environment variables template
├── requirements.txt             # Python dependencies
└── README.md
```

---

## Tech Stack

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.x | Primary language |
| streamlit | 1.x | Frontend web UI — desktop & mobile |
| langgraph | 1.x | Multi-agent orchestration pipeline |
| langchain | 1.x | LLM integration utilities |
| groq | 1.x | LLM inference — Llama 3.1-8b-instant |
| fastapi | 1.x | REST API backend |
| chromadb | 0.4.x | RAG vector store — India-specific knowledge base |
| pandas | 2.x | Financial calculation engines |
| python-dotenv | 1.x | Environment variable management |
| meta-llama/Llama-3.1-8b-instant | 3.1 | AI model for all agents via Groq |

---

## Getting Started

### Prerequisites

- Python 3.x
- A free [Groq API key](https://console.groq.com)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/aarthsaathi.git
cd aarthsaathi

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

### Running the App

```bash
# Run Streamlit frontend
streamlit run main.py

# Run FastAPI backend (optional)
uvicorn api.main:app --reload
```

### Environment Variables

```env
GROQ_API_KEY=your_groq_api_key_here
HOST=0.0.0.0
PORT=8000
API_KEY_PEPPER=your_random_secret_here
```

---

## App Pages

| Page | Description |
|------|-------------|
| 🏠 **Onboarding** | Collects income, obligations, goals via text or voice |
| 📊 **My Dashboard** | Budget breakdown, readiness score, personalised next steps |
| 📚 **Learn** | Financial concept cards — SIP, FD, EPF with scam comparisons |
| 🛡️ **Scam Awareness** | Scam types, red flags, verification toolkit, helpline 1930 |
| 📖 **Stories** | Relatable audio/visual storyline courses |
| 📰 **Daily News** | One simplified financial news item daily |

---

## Responsible AI

AarthSaathi is built with responsible AI as a core principle:

- ✅ **Education only** — never recommends specific financial products
- ✅ **RAG-grounded** — every response verified against RBI, SEBI, IRDAI sources
- ✅ **Guard Rails** — always-ON filter blocks harmful phrases across all agent outputs
- ✅ **Transparent** — every explanation includes official verification links
- ✅ **Human-in-the-loop** — critical cases escalate to human guidance
- ✅ **No guaranteed returns** — any such language is blocked before reaching user

### Guard Rails Block List includes:
- "Guaranteed returns" / "100% safe"
- "Take a loan to invest"
- "Double your money"
- "Limited time offer" / "Act now"
- Specific stock or fund recommendations

---

## Data Sources

| Source | Usage |
|--------|-------|
| RBI (rbi.org.in) | FD rates, banking regulations, fraud alerts |
| SEBI (sebi.gov.in) | Mutual fund verification, investor education |
| IRDAI (irdai.gov.in) | Insurance product verification |
| amfiindia.com | Mutual fund registration checks |
| cybercrime.gov.in | Scam reporting guidance |
| indiapost.gov.in | PPF, Sukanya Samriddhi schemes |
| epfindia.gov.in | EPF balance and queries |

**Cybercrime Helpline: 1930**

---

## Team

| Member | Role |
|--------|------|
| **Aayush Patil** | Architecture, Engineering & System Design · Minor: Management & Finance · EXTC-SPIT |
| **Rameshwari Chaudhari** | Product Strategy, AI Systems & Research · Minor: Artificial Intelligence · EXTC-SPIT |

---

## Hackathon Context

Built for **Nomura KakushIN Coding Contest 2026**
Theme: *Financial Literacy & Agentic AI Hackathon — AarthSaathi: Financial Guardians*

---

## License

This project was built for the Nomura KakushIN Hackathon 2026. All rights reserved by Team Byte Me.

---

*"The AI financial companion that protects people before it teaches them."*
