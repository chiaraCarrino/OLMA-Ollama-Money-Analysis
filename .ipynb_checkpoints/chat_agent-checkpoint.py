import httpx
import json
import traceback
import pandas as pd
import os

#OLLAMA_URL   = os.getenv("OLLAMA_CHAT_URL", "http://localhost:11434/api/chat")
OLLAMA_URL   = os.getenv("OLLAMA_CHAT_URL", "http://host.docker.internal:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen2.5:14b")

# ── TOOL FUNCTIONS ─────────────────────────────────────────────────────────


def describe_dataframe(df: pd.DataFrame) -> str:
    out = [f"Righe totali: {len(df)}"]
    try:
        out.append(f"Periodo: {df['data'].min().date()} → {df['data'].max().date()}")
    except Exception:
        pass
    if "categoria" in df.columns:
        cat = df.groupby("categoria")["_uscita"].agg(["count","sum"])
        out.append("\nCategorie disponibili:")
        for cat_name, row in cat.iterrows():
            out.append(f"  {cat_name}: {int(row['count'])} transazioni, € {row['sum']:,.2f}")
    if "nome_merchant" in df.columns:
        out.append("\nTop 10 merchant:")
        for m, n in df["nome_merchant"].value_counts().head(10).items():
            out.append(f"  {m}: {n}x")
    return "\n".join(out)


def compute_statistics(df: pd.DataFrame, operazione: str,
                       filtro_anno: str = "", filtro_categoria: str = "",filtro_merchant: str = "") -> str:
    if filtro_anno:
        try:
            df = df[df["_anno"] == int(filtro_anno)]
        except ValueError:
            pass
    if filtro_categoria:
        df = df[df["categoria"].str.lower() == filtro_categoria.lower()]
        
    if filtro_merchant:  # ← aggiunto
        df = df[df["nome_merchant"].str.contains(filtro_merchant, case=False, na=False)]
        if len(df) == 0:
            return f"Nessuna transazione trovata per il merchant '{filtro_merchant}'."

    def fmt(v):
        return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    op = operazione.strip().lower()
    if op == "totale_uscite":
        return f"Totale uscite: {fmt(df['_uscita'].sum())}"
    if op == "totale_entrate":
        return f"Totale entrate: {fmt(df['_entrata'].sum())}"
    if op == "media_mensile_uscite":
        # Quanti mesi distinti ci sono nel dataset (eventualmente filtrato per categoria)?
        n_mesi = df["_mese_str"].nunique()
        totale = df["_uscita"].sum()
        if n_mesi == 0:
            return "Nessun dato disponibile."
        media = totale / n_mesi
        return (
            f"Totale speso: {fmt(totale)}\n"
            f"Numero di mesi nel periodo: {n_mesi}\n"
            f"Media mensile: {fmt(media)}"
        )
    if op == "top5_categorie":
        top = df.groupby("categoria")["_uscita"].sum().sort_values(ascending=False).head(5)
        return "Top 5 categorie:\n" + "\n".join(f"  {c}: {fmt(v)}" for c, v in top.items())
    if op == "top5_merchant":
        top = df.groupby("nome_merchant")["_uscita"].sum().sort_values(ascending=False).head(5)
        return "Top 5 merchant:\n" + "\n".join(f"  {m}: {fmt(v)}" for m, v in top.items())
    if op == "spesa_per_mese":
        m = df.groupby("_mese_nome")["_uscita"].sum()
        return "Spesa per mese:\n" + "\n".join(f"  {k}: {fmt(v)}" for k, v in m.items())
    if op == "spesa_per_anno":
        a = df.groupby("_anno")["_uscita"].sum()
        return "Spesa per anno:\n" + "\n".join(f"  {int(k)}: {fmt(v)}" for k, v in a.items())
    if op == "confronto_anni":
        a = df.groupby("_anno")["_uscita"].sum()
        return "Confronto annuale:\n" + "\n".join(f"  {int(k)}: {fmt(v)}" for k, v in a.items())
    return f"Operazione '{operazione}' non riconosciuta."


def search_text(df: pd.DataFrame, keyword: str, filtro_anno: str = "") -> str:
    if filtro_anno:
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
    totale = trovate["_uscita"].sum()
    def fmt(v):
        return f"€ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    righe = trovate[["data","nome_merchant","descrizione","_uscita"]].to_string(index=False, max_rows=10)
    return f"Trovate {len(trovate)} transazioni con '{keyword}':\nTotale: {fmt(totale)}\n\n{righe}"


def query_dataframe(df: pd.DataFrame, codice: str) -> str:
    local_vars = {"df": df.copy(), "pd": pd, "risultato": None}
    try:
        exec(codice, {}, local_vars)  # noqa: S102
        risultato = local_vars.get("risultato")
        if risultato is None:
            return "Il codice non ha impostato `risultato`."
        if isinstance(risultato, pd.DataFrame):
            return risultato.to_string(index=False, max_rows=30)
        if isinstance(risultato, pd.Series):
            return risultato.to_string(max_rows=30)
        if isinstance(risultato, float):
            return f"€ {risultato:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return str(risultato)
    except Exception:
        return f"Errore:\n{traceback.format_exc(limit=3)}"


# ── DISPATCHER ─────────────────────────────────────────────────────────────

def dispatch(tool_name: str, args: dict, df: pd.DataFrame) -> str:
    if tool_name == "compute_statistics":
        return compute_statistics(df, **args)
    if tool_name == "search_text":
        return search_text(df, **args)
    if tool_name == "query_dataframe":
        return query_dataframe(df, **args)
    if tool_name == "describe_dataframe":
        return describe_dataframe(df)
    return f"Tool '{tool_name}' non riconosciuto."


# ── SCHEMA DEI TOOL ──────────────────

TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "compute_statistics",
            "description": (
                "Calcola statistiche aggregate sui movimenti bancari. "
                "USA SEMPRE questo tool per rispondere a domande sui dati — non inventare mai numeri. "
                "Esempi di domande: "
                "'categoria più alta' → operazione=top5_categorie; "
                "'media mensile ristoranti' → operazione=media_mensile_uscite, filtro_categoria=Ristoranti; "
                "'quanto ho speso nel 2025' → operazione=totale_uscite, filtro_anno=2025; "
                "'quanto ho speso da Burger King nel 2024' → operazione=totale_uscite, filtro_merchant=Burger King, filtro_anno=2024; "
                "'spesa per mese' → operazione=spesa_per_mese."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "operazione": {
                        "type": "string",
                        "enum": [
                            "totale_uscite", "totale_entrate",
                            "media_mensile_uscite", "top5_categorie",
                            "top5_merchant", "spesa_per_mese",
                            "spesa_per_anno", "confronto_anni"
                        ]
                    },
                    "filtro_anno":      {"type": "string"},
                    "filtro_categoria": {"type": "string"},
                    "filtro_merchant":  {"type": "string", "description": "Es. 'Burger King' o vuoto"},
                },
                "required": ["operazione"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_text",
            "description": (
                "Cerca transazioni per parola chiave in merchant o descrizione. "
                "Usa per domande tipo: pizza, carburante, amazon, palestra, ecc."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword":     {"type": "string"},
                    "filtro_anno": {"type": "string"},
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "query_dataframe",
            "description": (
                "Esegue codice pandas per query avanzate: spesa massima, minima, "
                "ordinamenti, filtri combinati. Usa come ultima risorsa."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "codice": {"type": "string"}
                },
                "required": ["codice"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "describe_dataframe",
            "description": (
                "Restituisce metadati: categorie disponibili, range date, "
                "merchant frequenti. Chiama per primo se non conosci i dati."
            ),
            "parameters": {"type": "object", "properties": {}}
        }
    },
]

def fallback_dispatch(domanda: str, df: pd.DataFrame) -> str:
    d = domanda.lower()

    import re
    anno_match = re.search(r"\b(202[0-9])\b", d)
    filtro_anno = anno_match.group(1) if anno_match else ""

    def filtra_anno(dataframe):
        if filtro_anno and "_anno" in dataframe.columns:
            try:
                return dataframe[dataframe["_anno"] == int(filtro_anno)]
            except ValueError:
                pass
        return dataframe

    categorie = list(df["categoria"].unique()) if "categoria" in df.columns else []

    # ── Media mensile per categoria ───────────────────────────────────────
    if "media" in d and "mensil" in d:
        filtro_cat = next((c for c in categorie if c.lower() in d), "")
        
        # Se non trova categoria, cerca per keyword nel testo
        if not filtro_cat:
            df_filtrato = filtra_anno(df)
            mask = (
                df_filtrato["nome_merchant"].str.contains(
                    d.split()[0], case=False, na=False)
                | df_filtrato["descrizione"].str.contains(
                    d.split()[0], case=False, na=False)
            )
            if mask.sum() == 0:
                return (f"Non ho trovato nessuna voce corrispondente "
                        f"a '{domanda}' nei tuoi dati.")

        return compute_statistics(df, "media_mensile_uscite",
                                  filtro_anno=filtro_anno,
                                  filtro_categoria=filtro_cat)

    # ── Totale speso per keyword o categoria ──────────────────────────────
    if "totale" in d or "quanto ho speso" in d or "speso" in d:
        # Prima cerca una categoria esatta
        filtro_cat = next((c for c in categorie if c.lower() in d), "")

        if filtro_cat:
            return compute_statistics(df, "totale_uscite",
                                      filtro_anno=filtro_anno,
                                      filtro_categoria=filtro_cat)

        # Poi cerca per keyword testuale nel merchant/descrizione
        # Estrai le parole significative dalla domanda (escludi stopwords)
        stopwords = {"quanto", "ho", "speso", "di", "nel", "in", "la", "il",
                     "le", "lo", "un", "una", "per", "del", "della", "dei"}
        parole = [p for p in re.findall(r"[a-zàèìòù]+", d) 
                  if p not in stopwords and len(p) > 2]

        for parola in parole:
            df_filtrato = filtra_anno(df)
            mask = (
                df_filtrato["nome_merchant"].str.contains(
                    parola, case=False, na=False)
                | df_filtrato["descrizione"].str.contains(
                    parola, case=False, na=False)
            )
            if mask.sum() > 0:
                return search_text(df, parola, filtro_anno=filtro_anno)

        # Nessuna categoria né keyword trovata → voce non presente
        parola_cercata = parole[0] if parole else domanda
        return (f"Non ho trovato nessuna voce chiamata '{parola_cercata}' "
                f"nei tuoi dati. Le categorie disponibili sono: "
                f"{', '.join(categorie)}.")

    # ── Top categorie ─────────────────────────────────────────────────────
    if "categoria" in d and any(k in d for k in ["più alta", "maggiore", "top"]):
        return compute_statistics(df, "top5_categorie", filtro_anno=filtro_anno)

    # ── Ricerca testuale generica ─────────────────────────────────────────
    stopwords = {"quanto", "ho", "speso", "di", "nel", "in", "la", "il",
                 "le", "lo", "un", "una", "per", "del", "della", "dei"}
    parole = [p for p in re.findall(r"[a-zàèìòù]+", d)
              if p not in stopwords and len(p) > 2]

    for parola in parole:
        df_filtrato = filtra_anno(df)
        mask = (
            df_filtrato["nome_merchant"].str.contains(parola, case=False, na=False)
            | df_filtrato["descrizione"].str.contains(parola, case=False, na=False)
        )
        if mask.sum() > 0:
            return search_text(df, parola, filtro_anno=filtro_anno)

    return ""

# ── AGENTE PRINCIPALE ──────────────────────────────────────────────────────

def ask_agent(domanda: str, df: pd.DataFrame) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "Sei un assistente finanziario personale. "
                "Rispondi sempre in italiano, in modo chiaro e conciso. "
                "REGOLA FONDAMENTALE: non rispondere mai a domande sui dati senza prima "
                "chiamare uno dei tool disponibili. Se non sei sicuro di quale categoria "
                "o merchant esiste nel dataset, chiama prima describe_dataframe. "
                "Non inventare mai numeri, categorie o merchant."
            )
        },
        {"role": "user", "content": domanda}
    ]

    # Turno 1 — il modello sceglie il tool
    try:
        resp = httpx.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "tools": TOOLS_SCHEMA,
            "stream": False,
        }, timeout=60).json()
    except Exception as e:
        return f"Errore di connessione a Ollama: {e}\nAssicurati che Ollama sia avviato."

    msg = resp.get("message", {})

    # Il modello ha risposto senza chiamare tool
    if not msg.get("tool_calls"):
    # Fallback: prova a capire cosa serve dalla domanda
        fallback_result = fallback_dispatch(domanda, df)
        if fallback_result:
            return fallback_result
        return msg.get("content", "Nessuna risposta.")

    # Esegui i tool e raccogli i risultati
    messages.append(msg)
    for tc in msg["tool_calls"]:
        tool_name = tc["function"]["name"]
        args = tc["function"]["arguments"]
        if isinstance(args, str):
            args = json.loads(args)
        risultato = dispatch(tool_name, args, df)
        messages.append({"role": "tool", "content": risultato})

    # Turno 2 — il modello formula la risposta finale in italiano
    try:
        resp2 = httpx.post(OLLAMA_URL, json={
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": False,
        }, timeout=60).json()
    except Exception as e:
        return f"Errore nella risposta finale: {e}"

    return resp2["message"].get("content", "Nessuna risposta.")