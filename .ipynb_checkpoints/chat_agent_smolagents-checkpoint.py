"""
chat_agent.py — Agente conversazionale per analisi del dataframe di movimenti bancari.

Tool disponibili:
  - query_dataframe     : esegue codice pandas sul df e restituisce il risultato
  - describe_dataframe  : schema, categorie disponibili, range date, totali
  - compute_statistics  : aggregazioni predefinite (sum, mean, count, top N)

Uso da Streamlit:
    from chat_agent import build_chat_agent, ask_agent
    agent = build_chat_agent(df)
    risposta = ask_agent(agent, "Quanto ho speso in pizza nel 2025?")
"""

import json
import os
import traceback
import pandas as pd
from smolagents import Tool, CodeAgent
from smolagents.models import OpenAIServerModel

#OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://ollama:11434/v1")
#OLLAMA_URL = os.getenv("OLLAMA_URL", "http://ollama:11434/v1/api/generate")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/v1")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

# ─────────────────────────────────────────────
# TOOL 1 — query_dataframe
# Esegue codice pandas arbitrario sul dataframe
# ─────────────────────────────────────────────

class QueryDataframeTool(Tool):
    name = "query_dataframe"
    description = (
        "Esegue codice Python/pandas sul dataframe dei movimenti bancari chiamato `df`. "
        "Usa questo tool per filtrare, aggregare, sommare, contare o qualsiasi altra "
        "operazione sui dati. "
        "Colonne sempre disponibili: data (datetime), importo (float, negativo=uscita), "
        "nome_merchant (str), categoria (str), descrizione (str). "
        "Colonne helper: _importo (float), _uscita (float>=0 solo spese), "
        "_entrata (float>=0 solo entrate), _anno (int), _mese_num (int), "
        "_mese_str (str es. '2025-03'), _mese_nome (str es. 'Mar 2025'). "
        "Restituisce il risultato come stringa leggibile."
    )
    inputs = {
        "codice": {
            "type": "string",
            "description": (
                "Codice Python valido che usa `df` e salva il risultato in `risultato`. "
                "Esempi: "
                "risultato = df[df['categoria']=='Ristorazione & Bar']['_uscita'].sum() ; "
                "risultato = df[df['_anno']==2025].groupby('categoria')['_uscita'].sum().sort_values(ascending=False).head(5)"
            ),
        }
    }
    output_type = "string"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df

    def forward(self, codice: str) -> str:
        local_vars = {"df": self._df.copy(), "pd": pd, "risultato": None}
        try:
            exec(codice, {}, local_vars)  # noqa: S102
            risultato = local_vars.get("risultato")
            if risultato is None:
                return "Il codice non ha impostato la variabile `risultato`."
            if isinstance(risultato, pd.DataFrame):
                if len(risultato) == 0:
                    return "Nessun dato trovato."
                return risultato.to_string(index=False, max_rows=30)
            if isinstance(risultato, pd.Series):
                if len(risultato) == 0:
                    return "Nessun dato trovato."
                return risultato.to_string(max_rows=30)
            if isinstance(risultato, float):
                return f"€ {risultato:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            return str(risultato)
        except Exception:
            return f"Errore nell'esecuzione del codice:\n{traceback.format_exc(limit=3)}"


# ─────────────────────────────────────────────
# TOOL 2 — describe_dataframe
# Restituisce metadati utili per orientarsi
# ─────────────────────────────────────────────

class DescribeDataframeTool(Tool):
    name = "describe_dataframe"
    description = (
        "Restituisce una descrizione del dataframe: numero di righe, "
        "range di date, categorie disponibili con conteggio e totale speso, "
        "e i merchant più frequenti. "
        "Usa questo tool PRIMA di query_dataframe quando non sei sicuro "
        "di quali categorie o merchant esistono nel dataset."
    )
    inputs = {}
    output_type = "string"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df

    def forward(self) -> str:
        df = self._df
        out = []

        out.append(f"Righe totali: {len(df)}")

        if "_data" in df.columns or "data" in df.columns:
            col_d = "_data" if "_data" in df.columns else "data"
            try:
                date_min = pd.to_datetime(df[col_d], errors="coerce").min()
                date_max = pd.to_datetime(df[col_d], errors="coerce").max()
                out.append(f"Periodo: {date_min.date()} → {date_max.date()}")
            except Exception:
                pass

        if "categoria" in df.columns:
            col_imp = "_uscita" if "_uscita" in df.columns else "importo"
            cat_summary = (
                df.groupby("categoria")[col_imp]
                .agg(["count", "sum"])
                .rename(columns={"count": "n_transazioni", "sum": "totale_€"})
                .sort_values("totale_€", ascending=False)
            )
            out.append("\nCategorie disponibili (ordinate per spesa totale):")
            for cat, row in cat_summary.iterrows():
                out.append(
                    f"  {cat}: {int(row['n_transazioni'])} transazioni, "
                    f"€ {row['totale_€']:,.2f}"
                )

        if "nome_merchant" in df.columns:
            top_merchant = df["nome_merchant"].value_counts().head(10)
            out.append("\nTop 10 merchant per frequenza:")
            for merchant, count in top_merchant.items():
                out.append(f"  {merchant}: {count}x")

        return "\n".join(out)


# ─────────────────────────────────────────────
# TOOL 3 — compute_statistics
# Aggregazioni veloci senza scrivere codice
# ─────────────────────────────────────────────

class ComputeStatisticsTool(Tool):
    name = "compute_statistics"
    description = (
        "Calcola statistiche aggregate predefinite sul dataframe. "
        "Usa questo tool per domande del tipo: "
        "'quanto ho speso in totale', 'media mensile', 'mese con più spese', "
        "'top N categorie', 'confronto tra anni'."
    )
    inputs = {
        "operazione": {
            "type": "string",
            "description": (
                "Una di: "
                "'totale_uscite', 'totale_entrate', 'media_mensile_uscite', "
                "'top5_categorie', 'top5_merchant', 'spesa_per_mese', "
                "'spesa_per_anno', 'confronto_anni'."
            ),
        },
        "filtro_anno": {
            "type": "string",
            "description": "Anno da filtrare (es. '2025'). Lascia vuoto per tutti gli anni.",
            "nullable": False
        },
        "filtro_categoria": {
            "type": "string",
            "description": "Categoria da filtrare (es. 'Ristorazione & Bar'). Lascia vuoto per tutte.",
            "nullable": False
        },
    }
    output_type = "string"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df

    def forward(
        self,
        operazione: str,
        filtro_anno: str = "",
        filtro_categoria: str = "",
    ) -> str:
        df = self._df.copy()

        # Applica filtri
        if filtro_anno and "_anno" in df.columns:
            try:
                df = df[df["_anno"] == int(filtro_anno)]
            except ValueError:
                #print(df)
                pass
        if filtro_categoria and "categoria" in df.columns:
            df = df[df["categoria"].str.lower() == filtro_categoria.lower()]

        col_usc = "_uscita"   if "_uscita"   in df.columns else "importo"
        col_ent = "_entrata"  if "_entrata"  in df.columns else "importo"

        def fmt(v):
            return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        op = operazione.strip().lower()

        if op == "totale_uscite":
            return f"Totale uscite: {fmt(df[col_usc].sum())}"

        if op == "totale_entrate":
            return f"Totale entrate: {fmt(df[col_ent].sum())}"

        if op == "media_mensile_uscite" and "_mese_str" in df.columns:
            media = df.groupby("_mese_str")[col_usc].sum().mean()
            return f"Media mensile uscite: {fmt(media)}"

        if op == "top5_categorie" and "categoria" in df.columns:
            top = df.groupby("categoria")[col_usc].sum().sort_values(ascending=False).head(5)
            lines = [f"  {cat}: {fmt(val)}" for cat, val in top.items()]
            return "Top 5 categorie per spesa:\n" + "\n".join(lines)

        if op == "top5_merchant" and "nome_merchant" in df.columns:
            top = df.groupby("nome_merchant")[col_usc].sum().sort_values(ascending=False).head(5)
            lines = [f"  {m}: {fmt(val)}" for m, val in top.items()]
            return "Top 5 merchant per spesa:\n" + "\n".join(lines)

        if op == "spesa_per_mese" and "_mese_nome" in df.columns:
            monthly = df.groupby("_mese_nome")[col_usc].sum()
            lines = [f"  {m}: {fmt(v)}" for m, v in monthly.items()]
            return "Spesa per mese:\n" + "\n".join(lines)

        if op == "spesa_per_anno" and "_anno" in df.columns:
            yearly = df.groupby("_anno")[col_usc].sum()
            lines = [f"  {int(a)}: {fmt(v)}" for a, v in yearly.items()]
            return "Spesa per anno:\n" + "\n".join(lines)

        if op == "confronto_anni" and "_anno" in df.columns:
            yearly = df.groupby("_anno")[col_usc].sum()
            lines = [f"  {int(a)}: {fmt(v)}" for a, v in yearly.items()]
            return "Confronto annuale uscite:\n" + "\n".join(lines)

        return f"Operazione '{operazione}' non riconosciuta o dati insufficienti."

# ─────────────────────────────────────────────
# TOOL 4 — search text
# Ricerca nel testo della domanda le categorie del dataset
# ─────────────────────────────────────────────

class SearchTextTool(Tool):
    name = "search_text"
    description = (
        "Cerca transazioni che contengono una parola chiave nel nome del merchant "
        "o nella descrizione. Usa questo tool per domande tipo: "
        "'quanto ho speso in pizza', 'spese per carburante', 'Amazon', ecc. "
        "Restituisce il totale speso, il numero di transazioni e le righe trovate."
    )
    inputs = {
        "keyword": {
            "type": "string",
            "description": "Parola chiave da cercare (es. 'pizza', 'benzina', 'amazon')",
        },
        "filtro_anno": {
            "type": "string",
            "description": "Anno da filtrare (es. '2025'). Lascia vuoto per tutti.",
            "nullable": False,
        },
    }
    output_type = "string"

    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df

    def forward(self, keyword: str, filtro_anno: str = "") -> str:
        df = self._df.copy()
        if filtro_anno and "_anno" in df.columns:
            try:
                df = df[df["_anno"] == int(filtro_anno)]
            except ValueError:
                pass

        mask = (
            df["nome_merchant"].str.contains(keyword, case=False, na=False)
            | df["descrizione"].str.contains(keyword, case=False, na=False)
        )
        trovate = df[mask]

        if len(trovate) == 0:
            return f"Nessuna transazione trovata con '{keyword}'."

        col_usc = "_uscita" if "_uscita" in df.columns else "importo"
        totale = trovate[col_usc].sum()
        n = len(trovate)

        def fmt(v):
            return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

        righe = trovate[["data", "nome_merchant", "descrizione", col_usc]].to_string(index=False, max_rows=10)
        return (
            f"Trovate {n} transazioni con '{keyword}':\n"
            f"Totale speso: {fmt(totale)}\n\n"
            f"Dettaglio (max 10 righe):\n{righe}"
        )

# ─────────────────────────────────────────────
# BUILD AGENT
# ─────────────────────────────────────────────

###def build_chat_agent(df: pd.DataFrame) -> CodeAgent:
###    """
###    Costruisce il CodeAgent con i tre tool legati al dataframe.
###    Chiamare una volta sola e salvare in st.session_state.
###    """
###    model = OpenAIServerModel(
###        model_id=OLLAMA_MODEL,
###        api_base=OLLAMA_URL,
###        api_key="ollama",
###    )
###    agent = CodeAgent(
###        tools=[
###            DescribeDataframeTool(df),
###            ComputeStatisticsTool(df),
###            QueryDataframeTool(df),
###        ],
###        model=model,
###        max_steps=2,
###        verbosity_level=2
###    )
###    return agent

from smolagents import ToolCallingAgent, OpenAIServerModel  # ← ToolCallingAgent

def build_chat_agent(df: pd.DataFrame) -> ToolCallingAgent:
    model = OpenAIServerModel(
        model_id="qwen2.5:14b",           # ← modello con buon tool calling
        api_base="http://localhost:11434/v1",
        api_key="ollama",
    )
    agent = ToolCallingAgent(             # ← più semplice per modelli locali
        tools=[
            DescribeDataframeTool(df),
            ComputeStatisticsTool(df),
            QueryDataframeTool(df),
            SearchTextTool(df),
        ],
        model=model,
        max_steps=3,
        verbosity_level=2,
    )
    return agent



    


def ask_agent(agent: CodeAgent, domanda: str) -> str:
    """
    Invia una domanda all'agente e restituisce la risposta come stringa.
    """
    task = (
        f"Sei un assistente finanziario personale. Rispondi in italiano, "
        f"in modo chiaro e conciso, alla seguente domanda sui movimenti bancari "
        f"dell'utente. Usa i tool disponibili per ottenere i dati reali dal dataframe.\n\n"
        f"Domanda: {domanda}"
    )
    try:
        risposta = agent.run(task)
        return str(risposta)
    except Exception as e:
        #return f"Non sono riuscito a rispondere: {e}"
        import traceback
        return traceback.format_exc()
