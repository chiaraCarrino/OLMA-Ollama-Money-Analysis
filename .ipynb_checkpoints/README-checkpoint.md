<p align="center">
  <img src="images/olma_piccola.png" width="300"/>
</p>

<p align="center">
  🇮🇹 <a href="README_IT.md">Versione italiana</a>
</p>

---

### *Have you ever tried to analyze your bank transactions and ended up staring at a CSV with dates in three different formats, amounts with mismatched decimal separators, columns named "Txn Amount (Funding Card)", and merchants written as `POS 00234 VISA CARREFOUR MKT`?*

Online solutions exist — Spendee, Revolut Analytics, various budgeting tools. But they all share two fundamental problems: **you have to upload your banking data to third-party servers**, and they rarely support the raw export format your bank actually produces.

**OLMA** was born out of this frustration. It is a **fully local** application that runs on your own machine, sends no data to any cloud service, and turns any bank CSV — however messy — into a complete analytics dashboard covering as many years of history as you want to explore.

---

## Screenshots

<p align="center">
  <img src="assets/screen_start.png" width="800"/>
  <br/>
  <em>Home — upload and column mapping</em>
</p>
<p align="center">
  <img src="assets/screen_dashboard.png" width="800"/>
  <br/>
  <em>Dashboard — income and expense analysis</em>
</p>
<p align="center">
  <img src="assets/screen_chat.png" width="800"/>
  <br/>
  <em>Chat — natural language queries over your transactions</em>
</p>

---

## What OLMA does

- **Robust CSV parsing** for real-world bank exports: automatic separator detection, malformed row handling, automatic header row detection even in files with leading metadata rows
- **Intelligent column mapping**: automatically detects columns (date, amount, merchant, category, description) via configurable aliases, with manual override from the UI
- **Hybrid transaction classification**:
  - *First pass* — deterministic lookup against a local JSON dictionary (`categorie_spese.json`)
  - *Second pass (fallback)* — **local LLM via Ollama**: no calls to OpenAI, no data leaving your network
- **Natural language chat interface**: ask questions about your transactions in plain language — "How much did I spend on restaurants in 2024?", "What is my highest spending category?", "Average monthly spend on fuel?" — and get answers grounded in your real data
- **Analytics dashboard** built with Plotly: spending by category, time-series trends with monthly/weekly/daily granularity, category×month heatmap, top merchants, effective monthly and annual savings with rolling average and cumulative balance
- **Export** to filtered CSV and Excel
- **Multilingual support** (IT / EN)

---

## Agentic architecture

OLMA runs two independent agentic pipelines, both fully local.

```
AGENT 1 — Classification (batch, offline)      AGENT 2 — Financial chat (real-time)
──────────────────────────────────────         ──────────────────────────────────────
Input: raw CSV description                     Input: natural language question
       "POS 00234 VISA CARREFOUR MKT"                 "How much did I spend on pizza in 2025?"
            │                                                   │
            ▼                                                   ▼
    Tool 1: lookup_json                            LLM reads the question
    (regex + substring on dictionary)              and selects the right tool
            │                                                   │
      match? ──NO──▶ Tool 2: classify_llm     ┌────────────────┼───────────────┐
            │         (Ollama, JSON output)    ▼                ▼               ▼
            ▼                           compute_          search_          query_
      Persistent disk cache             statistics        text             dataframe
      (shelve + MD5 hash)               (aggregations)   (str.contains)   (pandas)
            │                                   │
            ▼                                   ▼
    {merchant, category,               Result already computed
     confidence, source}               → LLM formats the reply
```

### Why two separate agents?

The two tasks have fundamentally different requirements. Classification runs once per transaction, deterministically, at import time — it needs speed and consistency. The chat agent runs interactively and needs to understand intent, select the right computation, and explain results in natural language. Keeping them separate means each can be optimised independently without interference.

### Both use Ollama — but with different models

Ollama is the runtime: the system that downloads, manages, and serves models on your machine. It is not a specific model, it is the infrastructure. The two agents choose different models because their tasks have different levels of difficulty:

| | Agent 1 — classifications | Agent 2 — chat |
|---|---|---|
| Recommended model | `llama3.2` (3B parametri) | `qwen2.5:14b` (14B parametri) |
| Why | Simple and repetitive task: given a text, choose a category among 20. A small model is enough and is faster. | Complex task: understand the intent, choose the right tool, pass correct JSON parameters. A more capable model is needed. |
| Protocollo Ollama | `POST /api/generate` — single completion | `POST /api/chat` — chat with tool calling, multiple turns |
| Call volumes | Potentially hundreds on import (one per non-cached transaction) | One per user question |

In both cases no data leaves your machine — this is the guarantee that matters.


### Why ToolCallingAgent instead of CodeAgent?

The chat agent uses a tool-calling pattern rather than asking the LLM to generate Python code. With 7–14B models running locally, generating syntactically valid pandas code reliably is difficult. Selecting a tool and providing JSON parameters is a much simpler task — and one these models handle well. Tool selection, parameter extraction, and result formatting are handled entirely by the LLM at runtime; no hardcoded routing.

### Why a deterministic fallback?

Local models occasionally respond in prose instead of calling a tool. A keyword-based fallback (`fallback_dispatch`) catches these cases and routes the query directly to the right function, ensuring the user always gets an answer grounded in real data — even when the model misbehaves.

### Why Ollama instead of a cloud API?

Bank transactions are sensitive personal data. Ollama runs the model **entirely on your local machine**: no tokens are sent to OpenAI, Anthropic, or any external service. The model is downloaded once and then works fully offline.

The classification prompt uses **constrained generation**: the model receives a closed list of 20 categories and must respond exclusively in JSON, making the output reliably parseable without complex post-processing.

---

## What you can ask the chat agent

The chat interface understands questions about your transactions in natural language:

| Question | What happens internally |
|---|---|
| "What is my highest spending category?" | `compute_statistics(top5_categorie)` |
| "Average monthly spend on restaurants?" | `compute_statistics(media_mensile_uscite, filtro_categoria=Ristoranti)` |
| "How much did I spend on fuel in 2024?" | `compute_statistics(totale_uscite, filtro_anno=2024, filtro_merchant=...)` |
| "How much did I spend on pizza in 2025?" | `search_text(keyword=pizza, filtro_anno=2025)` |
| "Highest single expense last year?" | `query_dataframe(df.nlargest(1, '_uscita'))` |
| "Monthly spending breakdown?" | `compute_statistics(spesa_per_mese)` |

If a category or merchant you ask about does not exist in your data, the agent tells you clearly and lists the categories it does know about — it never invents numbers.

---

## Classifier architecture

```
Transaction description
        │
        ▼
┌─────────────────────┐
│  JSON lookup        │  ← regex + substring match on categorie_spese.json
│  (deterministic)    │    confidence: high / medium
└─────────┬───────────┘
          │ no match
          ▼
┌─────────────────────┐
│  Ollama LLM         │  ← local model via Ollama REST API
│  (fallback)         │    prompt with JSON output constrained to 20 categories
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Disk cache         │  ← shelve + MD5 hash of the description
│  (persistent)       │    avoids re-inference on already-seen descriptions
└─────────────────────┘
```

<p align="center">
  <img src="assets/screen_ollama.png" width="800"/>
  <br/>
  <em>Ollama enrichment</em>
</p>

---

## Tech stack

| Layer | Technologies |
|---|---|
| UI & routing | Streamlit (multi-page) |
| Data processing | pandas, Python `csv`, `io` |
| Visualization | Plotly (go + px) |
| Classification agent | regex, JSON lookup, Ollama REST API |
| Chat agent | Ollama tool calling (`/api/chat`), `httpx` |
| Caching | Python `shelve` + MD5 hashing |
| Containerization | Docker + Docker Compose (optional profiles) |
| LLM locale — classification | Ollama + `llama3.2` |
| LLM locale — chat | Ollama + `qwen2.5:14b` (recommended) |

---

## Requirements

- [Docker](https://www.docker.com/products/docker-desktop) and Docker Compose installed
- Nothing else — Ollama is optional (see below)

---

## Installation

```bash
git clone https://github.com/chiaraCarrino/OLMA-Ollama-Money-Analysis.git
cd OLMA-Ollama-Money-Analysis
```

---

## Startup — choose your scenario

### Option 1 — You already have Ollama installed on your machine

Ollama is already running on your machine at `localhost:11434`? Copy the configuration template and set the URL:

```bash
cp .env.example .env
```

Open `.env` and set:
```
OLLAMA_URL=http://host.docker.internal:11434/api/generate
```

Then start only the app container:
```bash
docker-compose up
```

### Option 2 — You don't have Ollama and want Docker to handle everything

Docker will automatically download Ollama and the model (~2–5GB, first time only):

```bash
docker-compose --profile with-ollama up
```

The `model-puller` service downloads the model and then stops by itself. From the second run onwards the model is already stored in the Docker volume and startup is immediate.

### Option 3 — You don't want to use Ollama at all

```bash
docker-compose up
```

OLMA works without Ollama too, using only the JSON lookup for classification. Transactions not matched by the dictionary are assigned to the *Other* category. The chat agent will not be available without a running Ollama instance.

---

In all cases, the app is available at **[http://localhost:8501](http://localhost:8501)**

To stop it:
```bash
docker-compose down
```

---

## Recommended model

For the best experience with both the classification agent and the chat agent, we recommend `qwen2.5:14b` (or `qwen2.5:7b` if you have less than 8GB of VRAM) and `llama3.2` for the classification:

```bash
ollama pull qwen2.5:14b
ollama pull llama3.2 
```

---

## How to use the app

1. **Upload your CSV** — or try the included demo files (clean and messy)
2. **Check the column mapping** — OLMA detects them automatically; correct via the dropdown if needed
3. **Run enrichment** (optional) — only if your CSV is missing category/merchant columns
4. **Start the analysis** — access the full dashboard
5. **Ask questions** — use the chat interface to query your data in natural language
6. **Filter and explore** — use the sidebar to filter by date range and transaction type
7. **Export** — download the result as CSV or Excel

---

## Customizing categories

The `categorie_spese.json` file is the classifier's dictionary. Adding a new rule requires no code changes:

```json
{
  "Supermercato & Alimentari": [
    "carrefour", "esselunga", "conad", "lidl", "eurospin"
  ],
  "Ristorazione & Bar": [
    "mcdonald", "bar centrale", "just eat", "deliveroo"
  ],
  "Abbonamenti & Servizi digitali": [
    "netflix", "spotify", "amazon prime"
  ]
}
```

Matching is case-insensitive and supports both exact word boundary matching (high confidence) and partial substring matching (medium confidence).

---

## Privacy

OLMA is designed with privacy as an architectural constraint, not a feature:

- No data is sent to remote servers
- Both the classification agent and the chat agent use Ollama locally: the model runs on your machine or in your Docker container
- Everything stays on `localhost`
- No analytics, telemetry, or connections to external services

---

## Project structure

```
olma/
├── Home.py                            # Main page: upload, mapping, enrichment
├── pages/
│   └── 1_Analisi_Entrate_e_Uscite.py  # Dashboard + chat interface
├── enrich.py                          # Classification agent: JSON + Ollama
├── chat_agent.py                      # Chat agent: tool calling via Ollama
├── translations.py                    # IT/EN strings
├── categorie_spese.json               # Category dictionary (customizable)
├── esempio_pulito.csv                 # Clean demo file
├── esempio_sporco.csv                 # Messy demo file
├── assets/                            # README images
├── images/
│   └── olma_piccola.png
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Roadmap

- [ ] Direct XLSX input support
- [ ] Category rules configurable from the UI
- [ ] Monthly budget with alerts
- [ ] Year-over-year comparison by category
- [ ] Multi-account support (aggregate multiple CSV files)
- [ ] Chat history persistence across sessions

---

## License

Apache License 2.0
