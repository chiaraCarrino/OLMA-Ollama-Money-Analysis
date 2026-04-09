# ─────────────────────────────────────────────
# PATCH enrich.py — sostituisci/aggiungi queste sezioni
# Le parti non elencate restano identiche
# ─────────────────────────────────────────────

# 1) Aggiungi questo import in cima, dopo gli altri import
# ────────────────────────────────────────────────────────
from agent_classify import build_agent, classifica_con_agente


# 2) Nella funzione main(), sostituisci il blocco
#    "for i, desc in enumerate(descrizioni_uniche, 1):"
#    con questo:
# ────────────────────────────────────────────────────────

    # Costruisci l'agente UNA VOLTA sola (non ad ogni riga)
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


# 3) In home.py, nel blocco "run_enrich", sostituisci la riga:
#
#       mappa[desc_str] = enrich_mod.classifica_con_ollama(desc_str, cache)
#
#    con:
#
#       if not hasattr(st.session_state, "_agent"):
#           st.session_state["_agent"] = agent_classify.build_agent(esempi)
#       mappa[desc_str] = agent_classify.classifica_con_agente(
#           desc_str, st.session_state["_agent"]
#       )
#
#    e aggiungi in cima a home.py:
#       import agent_classify
#
# Tutto il resto di home.py (build_working_df, st.switch_page, ecc.) rimane identico.
