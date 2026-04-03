# OLMA 💳
### *Have you ever tried to analyze your bank transactions and ended up staring at a CSV with dates in three different formats, amounts with mismatched decimal separators, columns named "Txn Amount (Funding Card)", and merchants written as `POS 00234 VISA CARREFOUR MKT`?*

Online solutions exist — Spendee, Revolut Analytics, various budgeting tools. But they all share two fundamental problems: **you have to upload your banking data to third-party servers**, and they rarely support the raw export format your bank actually produces.

**OLMA** was born out of this frustration. It is a **fully local** application that runs on your own machine, sends no data to any cloud service, and turns any bank CSV — however messy — into a complete analytics dashboard covering as many years of history as you want to explore.

---

## What OLMA does

- **Robust CSV parsing** for real-world bank exports: automatic separator detection, malformed row handling, automatic header row detection even in files with leading metadata rows
- **Intelligent column mapping**: automatically detects columns (date, amount, merchant, category, description) via configurable aliases, with manual override from the UI
- **Hybrid transaction classification**:
  - *First pass* — deterministic lookup against a local JSON dictionary (`categorie_spese.json`)
  - *Second pass (fallback)* — **local LLM via Ollama**: no calls to OpenAI, no data leaving your network
- **Analytics dashboard** built with Plotly: spending by category, time-series trends with monthly/weekly/daily granularity, category×month heatmap, top merchants, effective monthly and annual savings with rolling average and cumulative balance
- **Export** to filtered CSV and Excel
- **Multilingual support** (IT / EN)

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
│  Ollama LLM         │  ← llama3.2 via local REST API
│  (fallback)         │    prompt with JSON output constrained to 20 categories
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Disk cache         │  ← shelve + MD5 hash of the description
│  (persistent)       │    avoids re-inference on already-seen descriptions
└─────────────────────┘
```

**Why Ollama instead of a cloud API?**
Bank transactions are sensitive personal data. Ollama runs the model **entirely on your local machine**: no tokens are sent to OpenAI, Anthropic, or any external service. The `llama3.2` model is downloaded once and then works fully offline.

The prompt engineering uses **constrained generation**: the model receives a closed list of 20 categories and must respond exclusively in JSON, making the output reliably parseable without complex post-processing.

---

## Tech stack

| Layer | Technologies |
|---|---|
| UI & routing | Streamlit (multi-page) |
| Data processing | pandas, Python `csv`, `io` |
| Visualization | Plotly (go + px) |
| Classification | regex, JSON lookup, Ollama REST API |
| Caching | Python `shelve` + MD5 hashing |
| Containerization | Docker + Docker Compose (optional profiles) |
| Local LLM | Ollama + llama3.2 |

---

## Requirements

- [Docker](https://www.docker.com/products/docker-desktop) and Docker Compose installed
- Nothing else — Ollama is optional (see below)

---

## Installation

```bash
git clone https://github.com/your-username/olma.git
cd olma
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

Docker will automatically download Ollama and the llama3.2 model (~2GB, first time only):

```bash
docker-compose --profile with-ollama up
```

The `model-puller` service downloads the model and then stops by itself. From the second run onwards the model is already stored in the Docker volume and startup is immediate.

### Option 3 — You don't want to use Ollama at all

```bash
docker-compose up
```

OLMA works without Ollama too, using only the JSON lookup. Transactions not matched by the dictionary are assigned to the *Other* category. You can explicitly disable the LLM fallback from the interface using the **"Use Ollama as fallback"** checkbox.

---

In all cases, the app is available at **[http://localhost:8501](http://localhost:8501)**

To stop it:
```bash
docker-compose down
```

---

## How to use the app

1. **Upload your CSV** — or try the included demo files (clean and messy)
2. **Check the column mapping** — OLMA detects them automatically; correct via the dropdown if needed
3. **Run enrichment** (optional) — only if your CSV is missing category/merchant columns
4. **Start the analysis** — access the full dashboard
5. **Filter and explore** — use the sidebar to filter by date range and transaction type
6. **Export** — download the result as CSV or Excel

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
- The LLM classifier uses Ollama locally: the model runs on your machine or in your Docker container
- Everything stays on `localhost`
- No analytics, telemetry, or connections to external services

---

## Project structure

```
olma/
├── Home.py                            # Main page: upload, mapping, enrichment
├── pages/
│   └── 1_Analisi_Entrate_e_Uscite.py  # Dashboard with all charts
├── enrich.py                          # Hybrid classifier: JSON + Ollama
├── translations.py                    # IT/EN strings
├── categorie_spese.json               # Category dictionary (customizable)
├── esempio_pulito.csv                 # Clean demo file
├── esempio_sporco.csv                 # Messy demo file
├── images/
│   └── olma_piccola.png
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example                       # Environment variable template
└── .gitignore
```

---

## Roadmap

- [ ] Direct XLSX input support
- [ ] Category rules configurable from the UI
- [ ] Monthly budget with alerts
- [ ] Year-over-year comparison by category
- [ ] Multi-account support (aggregate multiple CSV files)

---

## License

MIT — free to use, modify, and distribute.
