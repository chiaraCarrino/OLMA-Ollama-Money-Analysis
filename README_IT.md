<p align="center">
  <img src="images/olma_piccola.png" width="300"/>
</p>

<p align="center">
  EN <a href="README.md">Versione italiana</a>
</p>

---

# OLMA 💳
### *Ti è mai capitato di voler analizzare i tuoi movimenti bancari e trovarti davanti a un CSV con date in tre formati diversi, importi con la virgola che fa le virgolette, colonne che si chiamano "Txn Amount (Funding Card)" e merchant scritti come `POS 00234 VISA CARREFOUR MKT`?*

Esistono soluzioni online — Spendee, Revolut Analytics, strumenti di budget vari. Ma ci sono due problemi fondamentali: **devi caricare i tuoi dati bancari su server di terzi**, e spesso non supportano il formato grezzo che la tua banca esporta.

**OLMA** nasce da questa frustrazione. È un'applicazione **completamente locale**, che gira sul tuo PC, che non trasmette nessun dato a nessun servizio cloud, e che trasforma qualsiasi CSV bancario — sporco quanto vuoi — in una dashboard di analisi completa su tutti gli anni che vuoi esplorare.

---

## Cosa fa OLMA

- **Parsing robusto** di CSV bancari reali: rilevamento automatico del separatore, gestione delle righe malformate, individuazione automatica della riga di intestazione anche in file con metadata iniziali
- **Column mapping intelligente**: rileva automaticamente le colonne (data, importo, merchant, categoria, descrizione) tramite alias configurabili, con override manuale dall'interfaccia
- **Classificazione ibrida delle transazioni**:
  - *Primo livello* — lookup deterministico su un dizionario JSON locale (`categorie_spese.json`)
  - *Secondo livello (fallback)* — **LLM locale via Ollama**: nessuna chiamata a OpenAI, nessun dato che esce dalla tua rete
- **Dashboard di analisi** con Plotly: spese per categoria, andamento temporale con granularità mensile/settimanale/giornaliera, heatmap categoria×mese, top merchant, risparmio effettivo mensile e annuale con media mobile e cumulato
- **Export** in CSV e Excel filtrati
- **Supporto multilingua** (IT / EN)

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

---

## Architettura del classificatore

```
Descrizione transazione
        │
        ▼
┌─────────────────────┐
│  Lookup JSON        │  ← regex + substring match su categorie_spese.json
│  (deterministic)    │    confidenza: alta / media
└─────────┬───────────┘
          │ nessun match
          ▼
┌─────────────────────┐
│  Ollama LLM         │  ← llama3.2 via REST API locale
│  (fallback)         │    prompt con output JSON vincolato a 20 categorie
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Cache su disco     │  ← shelve + hash MD5 della descrizione
│  (persistente)      │    evita re-inferenza su descrizioni già viste
└─────────────────────┘
```

**Perché Ollama e non un'API cloud?**
I dati bancari sono dati personali sensibili. Ollama fa girare il modello **interamente in locale**: nessun token viene inviato a OpenAI, Anthropic o qualsiasi altro servizio esterno. Il modello `llama3.2` viene scaricato una volta sola e poi funziona offline.


<p align="center">
  <img src="assets/screen_ollama.png" width="800"/>
  <br/>
  <em>Ollama enrichment</em>
</p>

---

## Stack tecnico

| Layer | Tecnologie |
|---|---|
| UI & routing | Streamlit (multi-page) |
| Data processing | pandas, Python `csv`, `io` |
| Visualizzazione | Plotly (go + px) |
| Classificazione | regex, JSON lookup, Ollama REST API |
| Caching | Python `shelve` + MD5 hashing |
| Containerizzazione | Docker + Docker Compose (profili opzionali) |
| LLM locale | Ollama + llama3.2 |

---

## Requisiti

- [Docker](https://www.docker.com/products/docker-desktop) e Docker Compose installati
- Nient'altro — Ollama è opzionale (vedi sotto)

---

## Installazione

```bash
git clone https://github.com/tuo-username/olma.git
cd olma
```

---

## Avvio — scegli il tuo caso

### Caso 1 — Hai già Ollama installato sul tuo PC

Ollama gira già sulla tua macchina su `localhost:11434`? Copia il file di configurazione e modifica l'URL:

```bash
cp .env.example .env
```

Apri `.env` e imposta:
```
OLLAMA_URL=http://host.docker.internal:11434/api/generate
```

Poi avvia solo il container dell'app:
```bash
docker-compose up
```

### Caso 2 — Non hai Ollama e vuoi che Docker lo gestisca tutto

Docker scaricherà automaticamente Ollama e il modello llama3.2 (~2GB, solo la prima volta):

```bash
docker-compose --profile with-ollama up
```

Il servizio `model-puller` si occupa di scaricare il modello e poi si ferma da solo. Dalla seconda volta in poi il modello è già presente nel volume Docker e l'avvio è immediato.

### Caso 3 — Non vuoi usare Ollama per niente

```bash
docker-compose up
```

OLMA funziona anche senza Ollama usando solo il lookup JSON. Le transazioni non riconosciute dal dizionario vengono assegnate alla categoria *Altro*. Puoi disabilitare esplicitamente il fallback LLM dall'interfaccia con il checkbox **"Usa Ollama come fallback"**.

---

In tutti i casi, l'app è disponibile su **[http://localhost:8501](http://localhost:8501)**

Per fermarla:
```bash
docker-compose down
```

---

## Come usare l'app

1. **Carica il tuo CSV** — o prova con i file demo inclusi (pulito e sporco)
2. **Verifica il mapping delle colonne** — OLMA le rileva automaticamente; correggile se necessario dal menu a tendina
3. **Esegui l'arricchimento** (opzionale) — solo se mancano le colonne categoria/merchant nel tuo CSV
4. **Avvia l'analisi** — accedi alla dashboard con tutti i grafici
5. **Filtra ed esplora** — usa la sidebar per filtrare per periodo e tipo di movimento
6. **Esporta** — scarica il risultato in CSV o Excel

---

## Personalizzare le categorie

Il file `categorie_spese.json` è il dizionario del classificatore. Aggiungere una nuova regola non richiede di toccare il codice:

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

Il match è case-insensitive e supporta sia corrispondenza esatta di parola (alta confidenza) che corrispondenza parziale (media confidenza).

---

## Privacy

OLMA è progettata con la privacy come vincolo architetturale:

- Nessun dato viene inviato a server remoti
- Il classificatore LLM usa Ollama in locale: il modello gira sulla tua macchina o nel tuo container Docker
- Tutto rimane su `localhost`
- Non ci sono analytics, telemetria o connessioni a servizi esterni

---

## Struttura del progetto

```
olma/
├── Home.py                            # Pagina principale: upload, mapping, enrich
├── pages/
│   └── 1_Analisi_Entrate_e_Uscite.py  # Dashboard con tutti i grafici
├── enrich.py                          # Classificatore ibrido JSON + Ollama
├── translations.py                    # Stringhe IT/EN
├── categorie_spese.json               # Dizionario categorie (personalizzabile)
├── esempio_pulito.csv                 # File demo
├── esempio_sporco.csv                 # File demo con irregolarità
├── images/
│   └── olma_piccola.png
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example                       # Template variabili d'ambiente
└── .gitignore
```

---

## Roadmap

- [ ] Supporto XLSX come input diretto
- [ ] Regole di classificazione personalizzabili dall'interfaccia
- [ ] Budget mensile con alert
- [ ] Confronto anno su anno per categoria
- [ ] Supporto multi-conto (aggregazione di più CSV)

---

## Licenza

MIT — libero di usare, modificare e distribuire.
