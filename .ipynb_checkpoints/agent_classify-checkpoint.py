"""
agent_classify.py — Agente smolagents con due tool:
  - lookup_json   : cerca nel dizionario di esempi
  - classify_llm  : chiama Ollama per classificazione semantica

L'agente decide autonomamente quale tool usare (e in quale ordine).
Viene importato da enrich.py in sostituzione del fallback manuale.
"""

import json
import os
import re
import requests
from smolagents import Tool, CodeAgent
from smolagents.models import OpenAIServerModel

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://ollama:11434/v1")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

CATEGORIE = [
    "Supermercato & Alimentari", "Ristorazione & Bar", "Carburante",
    "Trasporti", "Assicurazioni", "Casa & Utenze", "Casa & Spese",
    "Salute & Farmacia", "Shopping & Abbigliamento",
    "Intrattenimento & Svago", "Abbonamenti & Servizi digitali",
    "Sport & Benessere", "Viaggi & Vacanze", "Istruzione & Libri",
    "Tasse & Banche", "Regali & Donazioni", "Stipendio & Reddito",
    "Entrate extra", "Trasferimento tra conti", "Altro",
]

# ─────────────────────────────────────────────
# TOOL 1 — lookup JSON
# ─────────────────────────────────────────────

class LookupJsonTool(Tool):
    name        = "lookup_json"
    description = (
        "Cerca la descrizione del movimento bancario nel dizionario di esempi noti. "
        "Restituisce un JSON con nome_merchant, categoria e confidenza, "
        "oppure null se non trovato."
    )
    inputs = {
        "descrizione": {
            "type": "string",
            "description": "La descrizione grezza del movimento bancario",
        }
    }
    output_type = "string"

    def __init__(self, esempi: dict):
        super().__init__()
        self.esempi = esempi

    def forward(self, descrizione: str) -> str:
        desc_lower = descrizione.lower()
        best_match = best_categoria = best_confidenza = None
        best_len = 0

        for categoria, valori in self.esempi.items():
            for valore in valori:
                valore_lower = valore.lower()
                pattern = r'\b' + re.escape(valore_lower) + r'\b'
                if re.search(pattern, desc_lower):
                    if len(valore_lower) > best_len:
                        best_match, best_categoria = valore, categoria
                        best_confidenza, best_len = "alta", len(valore_lower)
                    continue
                if valore_lower in desc_lower:
                    if len(valore_lower) > best_len:
                        best_match, best_categoria = valore, categoria
                        best_confidenza, best_len = "media", len(valore_lower)

        if best_match:
            return json.dumps({
                "nome_merchant": best_match,
                "categoria":     best_categoria,
                "confidenza":    best_confidenza,
                "fonte":         "json",
            }, ensure_ascii=False)

        return json.dumps(None)


# ─────────────────────────────────────────────
# TOOL 2 — classify LLM (Ollama)
# ─────────────────────────────────────────────

class ClassifyLlmTool(Tool):
    name        = "classify_llm"
    description = (
        "Usa il modello LLM locale (via Ollama) per classificare semanticamente "
        "un movimento bancario quando il lookup JSON non ha trovato corrispondenze. "
        "Restituisce un JSON con nome_merchant, categoria e confidenza."
    )
    inputs = {
        "descrizione": {
            "type": "string",
            "description": "La descrizione grezza del movimento bancario",
        }
    }
    output_type = "string"

    def forward(self, descrizione: str) -> str:
        categorie_lista = "\n".join(f"  - {c}" for c in CATEGORIE)
        prompt = (
            f"Sei un esperto di movimenti bancari italiani. Analizza questa descrizione "
            f"e restituisci SOLO un oggetto JSON valido, senza testo aggiuntivo.\n\n"
            f"Categorie disponibili:\n{categorie_lista}\n\n"
            f"Movimento: \"{descrizione}\"\n\n"
            f"Rispondi SOLO con:\n"
            f'{{\"nome_merchant\": \"nome leggibile\", \"categoria\": \"una delle categorie\", '
            f'\"confidenza\": \"alta/media/bassa\"}}'
        )
        try:
            resp = requests.post(
                f"{OLLAMA_URL.rstrip('/v1')}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
                timeout=60,
            )
            resp.raise_for_status()
            testo = resp.json().get("response", "")
            inizio = testo.find("{")
            fine   = testo.rfind("}") + 1
            if inizio == -1 or fine == 0:
                raise ValueError("Nessun JSON nella risposta")
            risultato = json.loads(testo[inizio:fine])
            risultato.setdefault("nome_merchant", descrizione)
            risultato.setdefault("categoria",     "Altro")
            risultato.setdefault("confidenza",    "bassa")
            risultato["fonte"] = "ollama"
            return json.dumps(risultato, ensure_ascii=False)
        except Exception as e:
            return json.dumps({
                "nome_merchant": descrizione,
                "categoria":     "Altro",
                "confidenza":    "bassa",
                "fonte":         "errore",
                "errore":        str(e),
            }, ensure_ascii=False)


# ─────────────────────────────────────────────
# AGENTE
# ─────────────────────────────────────────────

def build_agent(esempi: dict) -> CodeAgent:
    """
    Costruisce un CodeAgent smolagents con i due tool.
    Il modello LLM (Ollama) decide autonomamente quale tool invocare.
    """
    model = OpenAIServerModel(
        model_id=OLLAMA_MODEL,
        api_base=OLLAMA_URL,
        api_key="ollama",          # Ollama non richiede chiave reale
    )

    agent = CodeAgent(
        tools=[
            LookupJsonTool(esempi),
            ClassifyLlmTool(),
        ],
        model=model,
        max_steps=3,               # lookup → eventuale LLM → risposta
    )
    return agent


def classifica_con_agente(descrizione: str, agent: CodeAgent) -> dict:
    """
    Chiede all'agente di classificare una descrizione.
    L'agente decide se usare lookup_json, classify_llm, o entrambi.
    Ritorna sempre un dict con nome_merchant, categoria, confidenza, fonte.
    """
    task = (
        f"Classifica questo movimento bancario: \"{descrizione}\"\n\n"
        f"Prima prova con lookup_json. "
        f"Se restituisce null, usa classify_llm. "
        f"Restituisci il JSON risultante così com'è, senza modifiche."
    )
    try:
        risposta = agent.run(task)
        # smolagents restituisce la risposta finale come stringa
        if isinstance(risposta, str):
            inizio = risposta.find("{")
            fine   = risposta.rfind("}") + 1
            if inizio != -1 and fine > 0:
                risultato = json.loads(risposta[inizio:fine])
                risultato.setdefault("nome_merchant", descrizione)
                risultato.setdefault("categoria",     "Altro")
                risultato.setdefault("confidenza",    "bassa")
                risultato.setdefault("fonte",         "agente")
                return risultato
    except Exception as e:
        print(f"  Agente error per '{descrizione[:50]}': {e}")

    return {
        "nome_merchant": descrizione,
        "categoria":     "Altro",
        "confidenza":    "bassa",
        "fonte":         "errore",
    }
