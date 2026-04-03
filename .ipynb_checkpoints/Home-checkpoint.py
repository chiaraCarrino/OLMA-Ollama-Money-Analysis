"""
home.py — Pagina principale: upload, rilevamento colonne, enrich opzionale
"""

import streamlit as st
import pandas as pd
import csv
import io
import os
from translations import t
from PIL import Image

# ─────────────────────────────────────────────
# CONFIG PAGINA
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="OLMA",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)
# Titolo visivo con immagine
# Percorso assoluto relativo allo script


image = Image.open("images/olma_piccola.png")  # sostituisci con il percorso della tua immagine
# Ridimensiona ad alta risoluzione per l'header
# LARGHEZZA GRANDE per non sgranare (es. 1200 px)
# L'altezza si scala proporzionalmente
width = 500
height = int((width / image.width) * image.height)
image = image.resize((width, height), Image.LANCZOS)  # LANCZOS = qualità migliore

# Mostra immagine senza stretching
st.image(image, use_container_width=False)
# ─────────────────────────────────────────────
# SELETTORE LINGUA — prima di tutto
# ─────────────────────────────────────────────

col_lang = st.columns([6, 1])[1]
with col_lang:
    st.selectbox(
        "🌐",
        options=["it", "en"],
        index=0 if st.session_state.get("lang", "it") == "it" else 1,
        key="lang",
        label_visibility="collapsed",
    )

# ─────────────────────────────────────────────
# STILE
# ─────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #f8f7f4;
}
h1, h2, h3 { font-family: 'DM Serif Display', serif; }

.main .block-container { max-width: 900px; padding: 2.5rem 2rem; }

.step-badge {
    display: inline-flex; align-items: center; justify-content: center;
    width: 28px; height: 28px; border-radius: 50%;
    background: #1a1a2e; color: #fff;
    font-size: 0.75rem; font-weight: 600;
    margin-right: 0.6rem; flex-shrink: 0;
}
.step-row {
    display: flex; align-items: center;
    font-size: 1rem; font-weight: 500; color: #1a1a2e;
    margin-bottom: 1.2rem;
}

.col-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 0.8rem; margin: 1rem 0 1.4rem;
}
.col-card { background:#fff; border:1.5px solid #e2e0da; border-radius:12px; padding:0.8rem 1rem; }
.col-card.found   { border-color:#16a34a; background:#f0fdf4; }
.col-card.missing { border-color:#dc2626; background:#fef2f2; }
.col-card-label { font-size:0.68rem; text-transform:uppercase; letter-spacing:.08em; color:#888; margin-bottom:0.2rem; }
.col-card-value { font-size:0.95rem; font-weight:500; color:#1a1a2e; }
.col-card-icon  { font-size:1.1rem; float:right; margin-top:-0.1rem; }

.alert-ok   { background:#f0fdf4; border:1.5px solid #16a34a; border-radius:12px; padding:1rem 1.2rem; color:#15803d; display:flex; align-items:center; gap:.7rem; margin:1rem 0; }
.alert-warn { background:#fefce8; border:1.5px solid #ca8a04; border-radius:12px; padding:1rem 1.2rem; color:#92400e; display:flex; align-items:center; gap:.7rem; margin:1rem 0; }
.alert-err  { background:#fef2f2; border:1.5px solid #dc2626; border-radius:12px; padding:1rem 1.2rem; color:#991b1b; display:flex; align-items:center; gap:.7rem; margin:1rem 0; }

.divider { border:none; border-top:1.5px solid #e8e6e0; margin:1.8rem 0; }

.stButton > button {
    background:#1a1a2e !important; color:#fff !important;
    border:none !important; border-radius:10px !important;
    padding:0.65rem 1.8rem !important;
    font-family:'DM Sans',sans-serif !important;
    font-weight:500 !important; font-size:0.95rem !important;
    transition:opacity .15s;
}
.stButton > button:hover { opacity:0.82; }

div[data-baseweb="select"] > div {
    border-radius:8px !important; border-color:#d1cfc9 !important; background:#fff !important;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# COSTANTI
# ─────────────────────────────────────────────

REQUIRED_FIELDS = {
    "data":        {"label": t("col_data"),        "icon": "📅", "aliases": ["date", "data", "giorno", "data valuta", "data operazione", "date (yyyy-mm-dd as utc)"]},
    "importo":     {"label": t("col_importo"),     "icon": "💶", "aliases": ["txn amount", "importo", "amount", "valore", "dare", "avere", "euro", "eur", "importo €", "txn amount (funding card)"]},
    "merchant":    {"label": t("col_merchant"),    "icon": "🏪", "aliases": ["merchant", "nome_merchant", "esercente", "negozio", "fornitore", "nome merchant"]},
    "categoria":   {"label": t("col_categoria"),   "icon": "🏷️", "aliases": ["categoria", "category", "cat", "tipo", "type", "classificazione", "label"]},
    "descrizione": {"label": t("col_descrizione"), "icon": "📝", "aliases": ["descrizione", "notes", "nota", "note", "detail", "descrizione operazione", "causale"]},
}

PALETTE = [
    "#2563eb","#7c3aed","#db2777","#ea580c","#16a34a",
    "#0891b2","#ca8a04","#dc2626","#9333ea","#059669",
]

def format_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ─────────────────────────────────────────────
# UTILITÀ
# ─────────────────────────────────────────────

def detect_separator(raw_bytes: bytes) -> str:
    sample = raw_bytes[:4096].decode("utf-8-sig", errors="ignore")
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        return dialect.delimiter
    except csv.Error:
        counts = {s: sample.count(s) for s in [",", ";", "\t", "|"]}
        return max(counts, key=counts.get)


def _is_numeric(s: str) -> bool:
    try:
        float(s.replace(",", ".").replace(" ", ""))
        return True
    except ValueError:
        return False


def find_header_row(raw_bytes: bytes, sep: str) -> int:
    text  = raw_bytes.decode("utf-8-sig", errors="ignore")
    lines = text.splitlines()
    for i, line in enumerate(lines[:20]):
        parts = line.split(sep)
        if len(parts) < 2:
            continue
        text_cells = sum(
            1 for p in parts
            if p.strip().strip('"') and not _is_numeric(p.strip().strip('"'))
        )
        if text_cells >= max(2, len(parts) * 0.5):
            return i
    return 0


def load_csv(raw_bytes: bytes, sep: str) -> pd.DataFrame:
    header_row = find_header_row(raw_bytes, sep)
    text = raw_bytes.decode("utf-8-sig", errors="ignore")
    df = pd.read_csv(
        io.StringIO(text),
        sep=sep,
        skiprows=header_row,
        encoding_errors="replace",
        on_bad_lines="skip",
        engine="python",
    )
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, ~df.columns.str.match(r"^Unnamed")]
    df.columns = df.columns.str.strip()
    df = df.loc[:, df.isnull().mean() < 0.9]
    df = df.dropna(how="all")
    return df


def detect_columns(df: pd.DataFrame) -> dict:
    cols_lower = {c.lower().strip(): c for c in df.columns}
    result = {}
    for field, info in REQUIRED_FIELDS.items():
        found = None
        for alias in info["aliases"]:
            alias_l = alias.lower()
            if alias_l in cols_lower:
                found = cols_lower[alias_l]
                break
            for cl, corig in cols_lower.items():
                if alias_l in cl or cl in alias_l:
                    found = corig
                    break
            if found:
                break
        result[field] = found
    return result


def parse_data(series):
    parsed = pd.to_datetime(series, format="%Y-%m-%d", errors="coerce", utc=True)
    if parsed.isna().all():
        parsed = pd.to_datetime(series, dayfirst=True, errors="coerce")
    if parsed.dt.tz is not None:
        parsed = parsed.dt.tz_localize(None)
    return parsed


def parse_importo(s):
    try:
        s = str(s).strip().replace(" ", "").replace("€", "").replace("$", "")
        if "," in s and "." in s:
            if s.index(".") < s.index(","):
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            s = s.replace(",", ".")
        return float(s)
    except Exception:
        return None


def build_working_df(df_raw: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    df = df_raw.copy()
    canonical = {
        mapping["data"]:        "data",
        mapping["importo"]:     "importo",
        mapping["merchant"]:    "nome_merchant",
        mapping["categoria"]:   "categoria",
        mapping["descrizione"]: "descrizione",
    }
    rename_map = {orig: canon for orig, canon in canonical.items() if orig and orig != canon}
    if rename_map:
        df = df.rename(columns=rename_map)

    df["_data"]      = parse_data(df["data"])
    df["_importo"]   = df["importo"].apply(parse_importo)
    df["_anno"]      = df["_data"].dt.year
    df["_mese_num"]  = df["_data"].dt.month
    df["_mese_str"]  = df["_data"].dt.to_period("M").astype(str)
    df["_mese_nome"] = df["_data"].dt.strftime("%b %Y")
    df["_giorno"]    = df["_data"].dt.date
    df["_settimana"] = df["_data"].dt.isocalendar().week.astype(int)
    df["_uscita"]    = df["_importo"].apply(lambda x: abs(x) if pd.notna(x) and x < 0 else None)
    df["_entrata"]   = df["_importo"].apply(lambda x: x     if pd.notna(x) and x > 0 else None)
    return df

# ─────────────────────────────────────────────
# STATO SESSIONE
# ─────────────────────────────────────────────

def reset_session():
    for k in ["df_raw", "df", "mapping", "enrich_done", "sep",
              "raw_bytes", "enrich_stop", "enrich_running"]:
        st.session_state.pop(k, None)

# ─────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────

st.markdown(f"""
<div style="margin-bottom:0.2rem">
  <span style="font-family:'DM Serif Display',serif;font-size:2.2rem;color:#1a1a2e;">
    💳 {t("app_title")}
  </span>
</div>
<p style="color:#888;margin-top:0;margin-bottom:2rem;font-size:0.95rem;">
  {t("app_subtitle")}
</p>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FILE DI DEMO
# ─────────────────────────────────────────────

DEMO_FILES = {
    "pulito": {
        "path": "esempio_pulito.csv",
        "label": t("demo_clean_label"),
        "desc":  t("demo_clean_desc"),
        "sep":   ",",
    },
    "sporco": {
        "path": "esempio_sporco.csv",
        "label": t("demo_dirty_label"),
        "desc":  t("demo_dirty_desc"),
        "sep":   ";",
    },
}

st.markdown(f"""
<div style="background:#fff;border:1.5px solid #e2e0da;border-radius:16px;
            padding:1.4rem 1.6rem;margin-bottom:1.8rem;">
  <div style="font-family:'DM Serif Display',serif;font-size:1.1rem;
              color:#1a1a2e;margin-bottom:.5rem;">
    {t("demo_title")}
  </div>
  <p style="color:#888;font-size:0.88rem;margin:0 0 1rem;">
    {t("demo_subtitle")}
  </p>
""", unsafe_allow_html=True)

demo_col1, demo_col2 = st.columns(2)

def load_demo(key: str):
    info = DEMO_FILES[key]
    try:
        with open(info["path"], "rb") as f:
            raw_bytes = f.read()
        df_raw = load_csv(raw_bytes, info["sep"])
        reset_session()
        st.session_state["df_raw"]    = df_raw
        st.session_state["sep"]       = info["sep"]
        st.session_state["demo_mode"] = key
    except FileNotFoundError:
        st.error(f"{t('enrich_file_missing')}: {info['path']}")

with demo_col1:
    info = DEMO_FILES["pulito"]
    st.markdown(f"""
    <div style="background:#f0fdf4;border:1.5px solid #16a34a;border-radius:12px;
                padding:.9rem 1rem;margin-bottom:.5rem;">
      <b>{info['label']}</b><br>
      <span style="font-size:0.82rem;color:#555;">{info['desc']}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button(t("btn_demo_clean"), key="btn_demo_pulito", use_container_width=True):
        load_demo("pulito")
        st.rerun()

with demo_col2:
    info = DEMO_FILES["sporco"]
    st.markdown(f"""
    <div style="background:#fefce8;border:1.5px solid #ca8a04;border-radius:12px;
                padding:.9rem 1rem;margin-bottom:.5rem;">
      <b>{info['label']}</b><br>
      <span style="font-size:0.82rem;color:#555;">{info['desc']}</span>
    </div>
    """, unsafe_allow_html=True)
    if st.button(t("btn_demo_dirty"), key="btn_demo_sporco", use_container_width=True):
        load_demo("sporco")
        st.rerun()

st.markdown("</div>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 1 — UPLOAD
# ─────────────────────────────────────────────

st.markdown(f'<div class="step-row"><span class="step-badge">1</span>{t("step1")}</div>', unsafe_allow_html=True)

uploaded = st.file_uploader(
    label=t("upload_label"),
    type=["csv"],
    label_visibility="collapsed",
    on_change=reset_session,
    key="file_uploader",
)

if uploaded is not None and "df_raw" not in st.session_state:
    raw_bytes = uploaded.read()
    sep = detect_separator(raw_bytes)
    try:
        df_raw = load_csv(raw_bytes, sep)
        st.session_state["df_raw"] = df_raw
        st.session_state["sep"]    = sep
    except Exception as e:
        st.markdown(f'<div class="alert-err">❌ {t("read_error")}: <code>{e}</code></div>', unsafe_allow_html=True)
        st.stop()

if "df_raw" not in st.session_state:
    st.markdown(f"""
    <div style="background:#fff;border:1.5px solid #e2e0da;border-radius:16px;
                padding:2.5rem 2rem;text-align:center;margin-top:1rem;">
        <div style="font-size:2.5rem;margin-bottom:.6rem">📂</div>
        <p style="color:#888;margin:0;font-size:0.95rem">
            {t("no_file")}
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

df_raw = st.session_state["df_raw"]
sep    = st.session_state.get("sep", ";")

st.markdown(f"""
<div class="alert-ok">
  ✅ <b>{len(df_raw)}</b> {t("file_loaded")} &nbsp;·&nbsp;
  <b>{len(df_raw.columns)}</b> {t("file_cols")} &nbsp;·&nbsp;
  {t("file_sep")}: <code>{sep!r}</code>
</div>
""", unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 2 — RILEVAMENTO COLONNE
# ─────────────────────────────────────────────

st.markdown(f'<div class="step-row"><span class="step-badge">2</span>{t("step2")}</div>', unsafe_allow_html=True)

auto_mapping   = detect_columns(df_raw)
missing_fields = [f for f, col in auto_mapping.items() if col is None]
all_found      = len(missing_fields) == 0

cards_html = '<div class="col-grid">'
for field, info in REQUIRED_FIELDS.items():
    col_found   = auto_mapping.get(field)
    css_class   = "found" if col_found else "missing"
    icon_status = "✅" if col_found else "❌"
    col_display = col_found if col_found else t("col_not_found")
    cards_html += f"""
    <div class="col-card {css_class}">
      <span class="col-card-icon">{icon_status}</span>
      <div class="col-card-label">{info['label']}</div>
      <div class="col-card-value">{col_display}</div>
    </div>"""
cards_html += '</div>'
st.markdown(cards_html, unsafe_allow_html=True)

if all_found:
    st.markdown(f'<div class="alert-ok">{t("all_found")}</div>', unsafe_allow_html=True)
else:
    mancanti_labels = [REQUIRED_FIELDS[f]["label"] for f in missing_fields]
    st.markdown(f'<div class="alert-warn">⚠️ {t("missing_cols")}: <b>{", ".join(mancanti_labels)}</b>. {t("missing_hint")}</div>', unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 3 — ASSEGNAZIONE MANUALE
# ─────────────────────────────────────────────

st.markdown('<div class="step-row"><span class="step-badge">3</span>Conferma o correggi l\'assegnazione delle colonne</div>', unsafe_allow_html=True)
df_raw = st.session_state["df_raw"]  # rileggi sempre
if st.session_state.get("enrich_done", False):
    st.session_state["sel_merchant"]  = "nome_merchant"
    st.session_state["sel_categoria"] = "categoria"

col_options = ["— non assegnata —"] + df_raw.columns.tolist()
#col_options    = ["— non assegnata —"] + df_raw.columns.tolist()
manual_mapping = {}
cols_ui        = st.columns(len(REQUIRED_FIELDS))

for i, (field, info) in enumerate(REQUIRED_FIELDS.items()):
    with cols_ui[i]:
        current     = auto_mapping.get(field)
        default_idx = col_options.index(current) if current in col_options else 0
        selected    = st.selectbox(
            f"{info['icon']} {info['label']}",
            options=col_options,
            index=default_idx,
            key=f"sel_{field}",
        )
        manual_mapping[field] = None if selected == "— non assegnata —" else selected

still_missing = [f for f, v in manual_mapping.items() if v is None]
if still_missing:
    st.markdown(f'<div class="alert-err">❌ Assegna ancora: <b>{", ".join(REQUIRED_FIELDS[f]["label"] for f in still_missing)}</b></div>', unsafe_allow_html=True)

    preview_cols = [v for v in manual_mapping.values() if v and v in df_raw.columns]
    st.dataframe(df_raw[preview_cols].head(5), use_container_width=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 4 — ARRICCHIMENTO (condizionale)
# ─────────────────────────────────────────────

needs_enrich = "categoria" in still_missing or "merchant" in still_missing
enrich_done  = st.session_state.get("enrich_done", False)

if needs_enrich and not enrich_done:

    st.markdown('<div class="step-row"><span class="step-badge">4</span>Arricchimento con enrich.py</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="alert-warn">
      ⚠️ Le colonne <b>categoria</b> e/o <b>merchant</b> non sono presenti.
      Usa <code>enrich.py</code> per classificarle, oppure assegnale manualmente
      al passo 3 se esistono già con un nome diverso.
    </div>
    """, unsafe_allow_html=True)

    col_ea, col_eb = st.columns([2, 1])
    with col_ea:
        esempi_path = st.text_input(
            "Percorso `categorie_spese.json`",
            value="categorie_spese.json",
            key="esempi_path",
        )
        use_ollama = st.checkbox(
            "Usa Ollama come fallback (richiede server locale)",
            value=True, key="use_ollama",
        )
    with col_eb:
        st.markdown("<br>", unsafe_allow_html=True)
        run_enrich  = st.button("▶ Esegui arricchimento", key="btn_enrich")
        stop_enrich = st.button("⏹ Interrompi",           key="btn_stop")

    if stop_enrich:
        st.session_state["enrich_stop"] = True
        st.markdown('<div class="alert-warn">⏹ Interruzione richiesta…</div>', unsafe_allow_html=True)

    # ── Arricchimento ─────────────────────────────────────────────────────

    if run_enrich:
        if not os.path.exists(esempi_path):
            st.markdown(f'<div class="alert-err">❌ File non trovato: <code>{esempi_path}</code></div>', unsafe_allow_html=True)
        else:
            st.session_state["enrich_stop"] = False

            try:
                import importlib.util, shelve

                #spec = importlib.util.spec_from_file_location("enrich", "enrich.py")
                #
                _enrich_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "enrich.py")
                spec = importlib.util.spec_from_file_location("enrich", _enrich_path)
                enrich_mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(enrich_mod)

                esempi          = enrich_mod.carica_esempi(esempi_path)
                col_desc_enrich = manual_mapping.get("descrizione") or df_raw.columns[0]
                descrizioni_uniche = df_raw[col_desc_enrich].dropna().unique()
                n_tot           = len(descrizioni_uniche)

                mappa        = {}
                progress_bar = st.progress(0, text="Avvio…")
                status_box   = st.empty()
                stopped      = False

                with shelve.open(enrich_mod.CACHE_FILE) as cache:
                    for idx, desc in enumerate(descrizioni_uniche):

                        # ── check stop ──
                        if st.session_state.get("enrich_stop", False):
                            stopped = True
                            break

                        desc_str = str(desc)
                        r = enrich_mod.classifica_con_json(desc_str, esempi)
                        if r:
                            mappa[desc_str] = r
                        elif not use_ollama:
                            mappa[desc_str] = {
                                "nome_merchant": desc_str, "categoria": "Altro",
                                "confidenza": "bassa", "fonte": "nessuno",
                            }
                        else:
                            mappa[desc_str] = enrich_mod.classifica_con_ollama(desc_str, cache)

                        pct   = (idx + 1) / n_tot
                        cat   = mappa[desc_str].get("categoria", "?")
                        fonte = mappa[desc_str].get("fonte", "?")
                        progress_bar.progress(pct, text=f"{idx + 1} / {n_tot} — {desc_str[:50]}")
                        status_box.caption(f"→ **{cat}** &nbsp; · &nbsp; fonte: `{fonte}`")

                progress_bar.empty()
                status_box.empty()

                # Applica la mappa a tutto il df (righe non processate → "Altro")
                def arricchisci(desc):
                    if pd.isna(desc):
                        return pd.Series({"nome_merchant": "", "categoria": "Altro",
                                          "confidenza": "bassa", "fonte": "vuoto"})
                    return pd.Series(mappa.get(
                        str(desc),
                        {"nome_merchant": str(desc), "categoria": "Altro",
                         "confidenza": "bassa", "fonte": "nessuno"},
                    ))

                df_enriched = df_raw.copy()
                df_enriched[["nome_merchant", "categoria", "confidenza", "fonte"]] = \
                    df_enriched[col_desc_enrich].apply(arricchisci)

                st.session_state["df_raw"]      = df_enriched
                st.session_state["enrich_done"] = True

                n_ok = sum(
                    1 for v in mappa.values()
                    if v.get("fonte", "nessuno") not in ("nessuno", "errore", "vuoto")
                )

                if stopped:
                    st.markdown(f'<div class="alert-warn">⏹ Interrotto a {idx + 1}/{n_tot}. Le righe già classificate sono state salvate, le altre saranno "Altro".</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="alert-ok">✅ Completato: <b>{n_ok}/{n_tot}</b> descrizioni classificate.</div>', unsafe_allow_html=True)

                st.rerun()

            except Exception as e:
                st.markdown(f'<div class="alert-err">❌ Errore: <code>{e}</code></div>', unsafe_allow_html=True)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

elif needs_enrich and enrich_done:
    st.markdown('<div class="alert-ok">✅ Arricchimento già eseguito in questa sessione.</div>', unsafe_allow_html=True)
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ─────────────────────────────────────────────
# STEP 5 — AVVIA ANALISI
# ─────────────────────────────────────────────

step_num = 5 if needs_enrich else 4
st.markdown(f'<div class="step-row"><span class="step-badge">{step_num}</span>Avvia l\'analisi</div>', unsafe_allow_html=True)

ready = len(still_missing) == 0

if not ready:
    st.markdown('<div class="alert-warn">⚠️ Assegna tutte le colonne obbligatorie prima di procedere.</div>', unsafe_allow_html=True)
else:
    preview_cols = [v for v in manual_mapping.values() if v and v in df_raw.columns]
    st.dataframe(df_raw[preview_cols].head(8), use_container_width=True)

    if st.button("🚀 Avvia analisi →"):
        df_work = build_working_df(df_raw, manual_mapping)

        st.session_state["df"]          = df_work
        st.session_state["df_raw"]      = df_raw
        st.session_state["mapping"]     = manual_mapping
        st.session_state["PALETTE"]     = PALETTE
        st.session_state["format_euro"] = format_euro

        # Chiavi legacy — sempre nomi canonici perché build_working_df ha già rinominato
        st.session_state["col_data"]     = "data"
        st.session_state["col_importo"]  = "importo"
        st.session_state["col_desc"]     = "descrizione"
        st.session_state["col_merchant"] = "nome_merchant"
        st.session_state["col_cat"]      = "categoria"

        st.switch_page("pages/1_Analisi_Entrate_e_Uscite.py")
