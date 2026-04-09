"""
enrich.py — Classificatore ibrido: lookup JSON + fallback Ollama
- Preserva tutte le colonne originali del CSV
- Gestisce righe con ; dentro i campi (bad lines)
- Aggiunge: nome_merchant, categoria, confidenza, fonte

Uso: python enrich.py --input movimenti.csv --output movimenti_arricchiti.csv
"""

import requests
import pandas as pd
import json
import argparse
import os
import re
import time
import shelve
import hashlib
import io
import csv
from agent_classify import build_agent, classifica_con_agente

# ─────────────────────────────────────────────
# CONFIGURAZIONE
# ─────────────────────────────────────────────


#OLLAMA_URL    = "http://host.docker.internal:11434/api/generate"
OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
EXAMPLES_FILE = "categorie_spese.json"

_BASE = os.getcwd()
CACHE_FILE = os.path.join(_BASE, "cache_ollama")

CATEGORIE = [
    "Supermercato & Alimentari",
    "Ristorazione & Bar",
    "Carburante",
    "Trasporti",
    "Assicurazioni",
    "Casa & Utenze",
    "Casa & Spese",
    "Salute & Farmacia",
    "Shopping & Abbigliamento",
    "Intrattenimento & Svago",
    "Abbonamenti & Servizi digitali",
    "Sport & Benessere",
    "Viaggi & Vacanze",
    "Istruzione & Libri",
    "Tasse & Banche",
    "Regali & Donazioni",
    "Stipendio & Reddito",
    "Entrate extra",
    "Trasferimento tra conti",
    "Altro"
]

# ─────────────────────────────────────────────
# CARICAMENTO CSV — robusto ai ; nei campi
# ─────────────────────────────────────────────

def carica_csv(path: str, separatore: str) -> pd.DataFrame:
    sep_escaped = re.escape(separatore)
    """
    Legge il CSV in modo robusto:
    1. Prima prova la lettura standard con quoting corretto
    2. Se ci sono bad lines, le recupera sostituendo i ; extra nei campi
       con uno spazio, in modo da non perdere nessuna riga
    """
    
    # Tentativo 1: lettura standard
    try:
        df = pd.read_csv(
            path,
            sep=sep_escaped,
            encoding="utf-8-sig",
            engine="python",
            quoting=0,
            on_bad_lines="error",
            #skiprows=4
            
        )
        print(f"   Lettura standard riuscita — {len(df)} righe.")
        return df
    except Exception:
        pass

    # Tentativo 2: correzione manuale riga per riga
    print(f"   Rilevate righe con '{separatore}' nei campi. Applico correzione automatica...")
    
    with open(path, "r", encoding="utf-8-sig") as f:
        righe = f.readlines()
       

    

    n_colonne = len(righe[0].split(separatore))
    righe_corrette = [righe[0]]
    n_corrette = 0

    for i, riga in enumerate(righe[1:], start=2):
        parti = riga.rstrip("\n").split(separatore)
        if len(parti) == n_colonne:
            righe_corrette.append(riga)
        elif len(parti) > n_colonne:
            riga_corretta=riga.replace('; ui', ',')
            
            
            # Unisce le colonne in eccesso nell'ultima colonna
            
            righe_corrette.append(riga_corretta+ "\n")
            n_corrette += 1
            print(f"     Riga {i} corretta: {riga_corretta.strip()[:80]}...")
            
        else:
            print(f"     Riga {i} skippata (troppo poche colonne): {riga.strip()[:80]}")

    print(f"   {n_corrette} righe corrette, {len(righe_corrette) - 1} righe totali caricate.")

    df = pd.read_csv(
        io.StringIO("".join(righe_corrette)),
        sep=sep_escaped,
        encoding="utf-8-sig",
        engine="python"
    )
    return df.dropna(axis=1)

# ─────────────────────────────────────────────
# CARICAMENTO ESEMPI JSON
# ─────────────────────────────────────────────

def carica_esempi(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"File esempi non trovato: '{path}'")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ─────────────────────────────────────────────
# STEP 1 — LOOKUP JSON (case-insensitive)
# ─────────────────────────────────────────────

def classifica_con_json(descrizione: str, esempi: dict) -> dict | None:
    desc_lower = descrizione.lower()
    best_match = best_categoria = best_confidenza = None
    best_len = 0

    for categoria, valori in esempi.items():
        for valore in valori:
            valore_lower = valore.lower()

            pattern = r'\b' + re.escape(valore_lower) + r'\b'
            if re.search(pattern, desc_lower):
                if len(valore_lower) > best_len:
                    best_match, best_categoria, best_confidenza, best_len = valore, categoria, "alta", len(valore_lower)
                continue

            if valore_lower in desc_lower:
                if len(valore_lower) > best_len:
                    best_match, best_categoria, best_confidenza, best_len = valore, categoria, "media", len(valore_lower)

    if best_match:
        return {"nome_merchant": best_match, "categoria": best_categoria, "confidenza": best_confidenza, "fonte": "json"}
    return None

# ─────────────────────────────────────────────
# STEP 2 — FALLBACK OLLAMA
# ─────────────────────────────────────────────

def costruisci_prompt_ollama(descrizione: str) -> str:
    categorie_lista = "\n".join(f"  - {c}" for c in CATEGORIE)
    return f"""Sei un esperto di movimenti bancari italiani. Analizza questa descrizione di un movimento bancario e restituisci SOLO un oggetto JSON valido, senza testo aggiuntivo, senza backtick, senza spiegazioni.

Categorie disponibili:
{categorie_lista}

Movimento da classificare: "{descrizione}"

Rispondi SOLO con questo JSON (nome_merchant deve essere il nome leggibile del negozio/servizio, non la stringa grezza):
{{"nome_merchant": "nome leggibile del merchant", "categoria": "una delle categorie sopra", "confidenza": "alta/media/bassa"}}"""


def classifica_con_ollama(descrizione: str, cache: shelve.Shelf) -> dict:
    chiave = hashlib.md5(descrizione.encode()).hexdigest()

    if chiave in cache:
        cached = dict(cache[chiave])
        cached["fonte"] = "ollama_cache"
        return cached

    prompt = costruisci_prompt_ollama(descrizione)
    try:
        response = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            timeout=60
        )
        response.raise_for_status()
        testo = response.json().get("response", "")

        inizio = testo.find("{")
        fine   = testo.rfind("}") + 1
        if inizio == -1 or fine == 0:
            raise ValueError("Nessun JSON nella risposta Ollama")

        risultato = json.loads(testo[inizio:fine])
        risultato.setdefault("nome_merchant", descrizione)
        risultato.setdefault("categoria", "Altro")
        risultato.setdefault("confidenza", "bassa")

        cache[chiave] = risultato
        time.sleep(0.1)
        return {**risultato, "fonte": "ollama"}

    except Exception as e:
        print(f"    Ollama error per '{descrizione[:50]}': {e}")
        return {"nome_merchant": descrizione, "categoria": "Altro", "confidenza": "bassa", "fonte": "errore"}

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Classificatore ibrido: JSON + Ollama fallback")
    parser.add_argument("--input",      required=True)
    parser.add_argument("--output",     required=True)
    parser.add_argument("--colonna",    default="Descrizione")
    parser.add_argument("--separatore", default=";")
    parser.add_argument("--esempi",     default=EXAMPLES_FILE)
    parser.add_argument("--no-ollama",  action="store_true")
    args = parser.parse_args()

    print(f"Carico esempi da '{args.esempi}'...")
    esempi = carica_esempi(args.esempi)
    print(f"   {len(esempi)} categorie, {sum(len(v) for v in esempi.values())} valori totali.")

    print(f"\nCarico '{args.input}'...")
    df = carica_csv(args.input, args.separatore)

    if args.colonna not in df.columns:
        print(f"Colonna '{args.colonna}' non trovata. Disponibili: {list(df.columns)}")
        return

    print(f"   Colonne originali: {list(df.columns)}")
    print(f"   {len(df)} movimenti caricati.")

    descrizioni_uniche = df[args.colonna].dropna().unique()
    print(f"\nDescrizioni uniche: {len(descrizioni_uniche)}")

    contatori = {"json_alta": 0, "json_media": 0, "ollama": 0, "errore": 0}
    mappa = {}

    with shelve.open(CACHE_FILE) as cache:
        agent = None
    if not args.no_ollama:
        print("\nInizializzo agente smolagents...")
        agent = build_agent(esempi)
        print("   Agente pronto.")

    with shelve.open(CACHE_FILE) as cache:
        for i, desc in enumerate(descrizioni_uniche, 1):
            desc_str = str(desc)

            # Cache hit — salta tutto
            chiave = hashlib.md5(desc_str.encode()).hexdigest()
            if chiave in cache:
                r = dict(cache[chiave])
                r["fonte"] = "ollama_cache"
                mappa[desc_str] = r
                print(f"  [{i:>4}/{len(descrizioni_uniche)}] {'Cache':<20} {r['categoria']:<32} <- {desc_str[:60]}")
                continue

            # Prima prova JSON diretto (veloce, nessuna chiamata LLM)
            r = classifica_con_json(desc_str, esempi)

            if r:
                fonte_label = f"JSON [{r['confidenza']}]"
                contatori["json_alta" if r["confidenza"] == "alta" else "json_media"] += 1

            elif args.no_ollama or agent is None:
                r = {"nome_merchant": desc_str, "categoria": "Altro",
                     "confidenza": "bassa", "fonte": "nessuno"}
                fonte_label = "Nessun match"
                contatori["errore"] += 1

            else:
                # L'agente decide autonomamente: lookup_json → classify_llm
                r = classifica_con_agente(desc_str, agent)
                fonte_label = f"Agente [{r.get('fonte','?')}]"
                contatori["errore" if r["fonte"] == "errore" else "ollama"] += 1
                # Salva in cache
                cache[chiave] = {k: v for k, v in r.items() if k != "fonte"}
                time.sleep(0.1)

            mappa[desc_str] = r
            print(f"  [{i:>4}/{len(descrizioni_uniche)}] {fonte_label:<20} {r['categoria']:<32} <- {desc_str[:60]}")



    def arricchisci(desc):
        if pd.isna(desc):
            return pd.Series({"nome_merchant": "", "categoria": "Altro", "confidenza": "bassa", "fonte": "vuoto"})
        return pd.Series(mappa.get(str(desc), {"nome_merchant": str(desc), "categoria": "Altro", "confidenza": "bassa", "fonte": "nessuno"}))

    print("\nAssemblo il file finale...")
    df[["nome_merchant", "categoria", "confidenza", "fonte"]] = df[args.colonna].apply(arricchisci)

    df.to_csv(args.output, index=False, sep=";", encoding="utf-8-sig")

    print(f"\nFile salvato: '{args.output}'")
    print(f"   Colonne nel file di output: {list(df.columns)}")
    print(f"   Movimenti totali:           {len(df)}")
    print(f"   Descrizioni uniche:         {len(descrizioni_uniche)}")
    print(f"   Match JSON alta:            {contatori['json_alta']}")
    print(f"   Match JSON media:           {contatori['json_media']}")
    print(f"   Classificati da Ollama:     {contatori['ollama']}")
    print(f"   Non classificati:           {contatori['errore']}")
    print(f"   Copertura totale:           {(len(descrizioni_uniche) - contatori['errore']) / len(descrizioni_uniche) * 100:.1f}%")


if __name__ == "__main__":
    main()
