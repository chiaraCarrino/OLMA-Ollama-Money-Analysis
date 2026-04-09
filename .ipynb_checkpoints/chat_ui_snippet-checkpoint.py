"""
chat_ui_snippet.py
Incolla questo blocco IN FONDO alla pagina di analisi (es. 1_Analisi_Entrate_e_Uscite.py),
dopo tutti i grafici esistenti.

Prerequisiti:
  - st.session_state["df"] contiene il dataframe arricchito (build_working_df già eseguito)
  - chat_agent.py è nella stessa cartella (o nel PYTHONPATH)
"""

import streamlit as st
from chat_agent import build_chat_agent, ask_agent

# ─────────────────────────────────────────────
# SEZIONE CHAT — incolla dopo i tuoi grafici
# ─────────────────────────────────────────────

st.markdown("---")
st.markdown("### 💬 Chiedi ai tuoi dati")
st.caption(
    "Fai domande in linguaggio naturale sui tuoi movimenti. "
    "Esempi: *Quanto ho speso in pizza nel 2025?* · "
    "*Qual è la mia categoria di spesa più alta?* · "
    "*Media mensile ristoranti?*"
)

# Recupera il dataframe dalla sessione
df_chat = st.session_state.get("df")
if df_chat is None:
    st.warning("Nessun dato caricato. Torna alla home e carica un file.")
    st.stop()

# Costruisce l'agente UNA VOLTA e lo conserva in sessione
if "chat_agent" not in st.session_state:
    with st.spinner("Inizializzo l'agente..."):
        st.session_state["chat_agent"]    = build_chat_agent(df_chat)
        st.session_state["chat_history"]  = []   # lista di dict {role, content}

agent   = st.session_state["chat_agent"]
history = st.session_state["chat_history"]

# ── Mostra la history ──────────────────────────────────────────────────────
for msg in history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Input utente ───────────────────────────────────────────────────────────
domanda = st.chat_input("Scrivi una domanda sui tuoi movimenti...")

if domanda:
    # Mostra messaggio utente
    with st.chat_message("user"):
        st.markdown(domanda)
    history.append({"role": "user", "content": domanda})

    # Risposta agente
    with st.chat_message("assistant"):
        with st.spinner("Sto analizzando..."):
            risposta = ask_agent(agent, domanda)
        st.markdown(risposta)
    history.append({"role": "assistant", "content": risposta})

    # Aggiorna la history in sessione
    st.session_state["chat_history"] = history
