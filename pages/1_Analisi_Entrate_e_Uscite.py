"""
1_Analisi_Entrate_e_Uscite.py — Dashboard analisi movimenti bancari
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
from translations import t, months_dict, months_short_list
from chat_agent import ask_agent#build_chat_agent, ask_agent
##from chat_agent import build_graph, ask_agent
# ─────────────────────────────────────────────
# CONFIG PAGINA
# ─────────────────────────────────────────────

st.set_page_config(
    page_title="Analisi Movimenti",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# SELETTORE LINGUA (sidebar)
# ─────────────────────────────────────────────

st.sidebar.selectbox(
    t("lang_label"),
    options=["it", "en"],
    index=0 if st.session_state.get("lang", "it") == "it" else 1,
    key="lang",
)

# ─────────────────────────────────────────────
# STILE
# ─────────────────────────────────────────────

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=DM+Sans:wght@300;400;500&display=swap');

    h1, h2, h3 { font-family: 'DM Serif Display', serif; }

    .metric-card {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.2rem 1.5rem;
        color: white;
    }
    .metric-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: rgba(255,255,255,0.5);
        margin-bottom: 0.3rem;
    }
    .metric-value {
        font-size: 1.8rem;
        font-weight: 500;
        color: #e2e8f0;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: rgba(255,255,255,0.4);
        margin-top: 0.2rem;
    }
    .stDataFrame { border-radius: 12px; }

    .section-header {
        display: flex;
        align-items: flex-start;
        gap: 0.9rem;
        margin: 2.2rem 0 1.2rem;
        padding-bottom: 0.9rem;
        border-bottom: 1.5px solid #e8e6e0;
    }
    .section-header-icon {
        font-size: 1.6rem;
        line-height: 1;
        flex-shrink: 0;
        margin-top: 0.1rem;
    }
    .section-header-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.25rem;
        color: #1a1a2e;
        margin: 0 0 0.15rem;
        line-height: 1.2;
    }
    .section-header-desc {
        font-size: 0.82rem;
        color: #888;
        margin: 0;
        line-height: 1.4;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        border: 1.5px solid #e8e6e0 !important;
        border-radius: 16px !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
        padding: 0.8rem 1rem 1.2rem !important;
        margin: 0.8rem 0 !important;
    }
    div[data-testid="stHorizontalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] {
        background: transparent !important;
        border: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GUARDIA: file caricato?
# ─────────────────────────────────────────────

if "df" not in st.session_state:
    st.warning(t("no_file_warning"))
    st.stop()

# ─────────────────────────────────────────────
# RECUPERA DATI DA SESSION STATE
# ─────────────────────────────────────────────

df           = st.session_state["df"]
col_data     = st.session_state["col_data"]
col_importo  = st.session_state["col_importo"]
col_desc     = st.session_state["col_desc"]
col_merchant = st.session_state["col_merchant"]
col_cat      = st.session_state["col_cat"]
PALETTE      = st.session_state["PALETTE"]
format_euro  = st.session_state["format_euro"]

# ─────────────────────────────────────────────
# COSTANTI
# ─────────────────────────────────────────────

PALETTE = [
    "#2563eb","#7c3aed","#db2777","#ea580c","#16a34a",
    "#0891b2","#ca8a04","#dc2626","#9333ea","#059669",
    "#d97706","#0284c7","#be185d","#65a30d","#7c2d12",
    "#1d4ed8","#6d28d9","#be123c","#c2410c"
]
BG2   = "#ffffff"
TEXT  = "#1a1a2e"
TEXT2 = "#1a1a2e"
GRID  = "#e2e8f0"

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color=TEXT, size=11),
    margin=dict(t=48, b=16, l=16, r=16),
)

def format_euro(val):
    return f"€ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ─────────────────────────────────────────────
# HELPER UI
# ─────────────────────────────────────────────

def section_header(icon: str, title: str, desc: str = ""):
    desc_html = f'<p class="section-header-desc">{desc}</p>' if desc else ""
    st.markdown(f"""
    <div class="section-header">
      <div class="section-header-icon">{icon}</div>
      <div>
        <p class="section-header-title">{title}</p>
        {desc_html}
      </div>
    </div>
    """, unsafe_allow_html=True)

def kpi(col, label, value, sub=""):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        {'<div class="metric-sub">' + sub + '</div>' if sub else ''}
    </div>
    """, unsafe_allow_html=True)

def add_vline_above(fig, x, color, dash, label, label_position="top"):
    fig.add_shape(
        type="line", x0=x, x1=x, y0=0, y1=1,
        xref="x", yref="paper",
        line=dict(color=color, width=1.5, dash=dash),
        layer="above",
    )
    fig.add_annotation(
        x=x,
        y=1 if label_position == "top" else 0,
        xref="x", yref="paper",
        text=label,
        showarrow=False,
        font=dict(color=color, size=12),
        bgcolor="rgba(255,255,255,0.75)",
        borderpad=3,
        xanchor="left" if x >= 0 else "right",
        yanchor="bottom" if label_position == "top" else "top",
    )

# ─────────────────────────────────────────────
# SIDEBAR FILTRI
# ─────────────────────────────────────────────

date_min = df["_data"].min()
date_max = df["_data"].max()
if pd.notna(date_min) and pd.notna(date_max):
    date_range = st.sidebar.date_input(
        t("sidebar_period"),
        value=(date_min.date(), date_max.date()),
        min_value=date_min.date(),
        max_value=date_max.date()
    )
    if len(date_range) == 2:
        df = df[(df["_data"].dt.date >= date_range[0]) & (df["_data"].dt.date <= date_range[1])]

tipo_movimento = st.sidebar.radio(
    t("sidebar_show"),
    [t("sidebar_all"), t("sidebar_expenses"), t("sidebar_income")],
    index=0
)
if tipo_movimento == t("sidebar_expenses"):
    df = df[df["_uscita"].notna()]
elif tipo_movimento == t("sidebar_income"):
    df = df[df["_entrata"].notna()]

st.sidebar.markdown("---")
st.sidebar.markdown(f"**{len(df)}** {t('sidebar_filtered')}")

# ─────────────────────────────────────────────
# HEADER PAGINA
# ─────────────────────────────────────────────

st.markdown(f"<h1 style='font-family:DM Serif Display,serif;color:#1a1a2e;margin-bottom:0'>{t('analysis_title')}</h1>", unsafe_allow_html=True)
if pd.notna(date_min) and pd.notna(date_max):
    st.markdown(f"<p style='color:#64748b;margin-top:0.2rem'>{date_min.strftime('%d %b %Y')} → {date_max.strftime('%d %b %Y')}</p>", unsafe_allow_html=True)
st.markdown("---")

# ─────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────

totale_uscite  = df["_uscita"].sum()
totale_entrate = df["_entrata"].sum()
saldo_netto    = totale_entrate - totale_uscite
n_movimenti    = len(df)
n_categorie    = df["categoria"].nunique()
spesa_media    = df["_uscita"].mean()

c1, c2, c3, c4, c5 = st.columns(5)
kpi(c1, t("kpi_expenses"),   format_euro(totale_uscite),  f"{n_movimenti} {t('kpi_transactions')}")
kpi(c2, t("kpi_income"),     format_euro(totale_entrate), "")
kpi(c3, t("kpi_balance"),    format_euro(saldo_netto),    t("kpi_income_expense"))
kpi(c4, t("kpi_avg"),        format_euro(spesa_media) if pd.notna(spesa_media) else "—", t("kpi_per_expense"))
kpi(c5, t("kpi_categories"), str(n_categorie), t("kpi_active"))

st.markdown("---")

# ─────────────────────────────────────────────
# SEZIONE 1 — Spese per categoria
# ─────────────────────────────────────────────

with st.container(border=True):
    section_header("🏷️", t("sec_cat_title"), t("sec_cat_desc"))

    col_l, col_r = st.columns([1, 1])

    with col_l:
        df_cat = df.groupby("categoria")["_uscita"].sum().dropna().reset_index()
        df_cat = df_cat[df_cat["_uscita"] > 0].sort_values("_uscita", ascending=False)

        fig_donut = go.Figure(go.Pie(
            labels=df_cat["categoria"],
            values=df_cat["_uscita"],
            hole=0.55,
            marker_colors=PALETTE[:len(df_cat)],
            textinfo="percent+label",
            textfont_size=11,
            hovertemplate="<b>%{label}</b><br>€ %{value:,.2f}<br>%{percent}<extra></extra>"
        ))
        fig_donut.update_layout(
            **PLOTLY_BASE,
            title=t("chart_expense_dist"),
            showlegend=False,
            height=380,
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_r:
        df_bar = df_cat.head(10).sort_values("_uscita")
        fig_bar = go.Figure(go.Bar(
            x=df_bar["_uscita"],
            y=df_bar["categoria"],
            orientation="h",
            marker_color=PALETTE[:len(df_bar)],
            text=[format_euro(v) for v in df_bar["_uscita"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x:,.2f} €<extra></extra>"
        ))
        fig_bar.update_layout(
            **PLOTLY_BASE,
            title=t("chart_top_cat"),
            height=380,
            xaxis=dict(showgrid=True, gridcolor=GRID),
            yaxis=dict(showgrid=False),
            #margin=dict(t=40, b=10, l=10, r=80)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

# ─────────────────────────────────────────────
# SEZIONE 2 — Andamento temporale
# ─────────────────────────────────────────────

with st.container(border=True):
    section_header("📈", t("sec_time_title"), t("sec_time_desc"))

    mesi_nomi = months_dict()

    anni_disponibili = sorted(df["_anno"].dropna().unique().astype(int).tolist(), reverse=True)
    f1, f2, f3 = st.columns([1, 1, 2])
    with f1:
        anno_sel = st.selectbox(t("chart_year"), anni_disponibili, index=0)
    with f2:
        mese_options = [t("chart_all_months")] + [f"{v} ({k:02d})" for k, v in mesi_nomi.items()]
        mese_sel_label = st.selectbox(t("chart_month"), mese_options, index=0)
        mese_sel = None if mese_sel_label == t("chart_all_months") else int(mese_sel_label.split("(")[1].replace(")", ""))
    with f3:
        granularita = st.radio(
            t("chart_granularity"),
            [t("chart_monthly"), t("chart_weekly"), t("chart_daily")],
            horizontal=True, index=0,
            help=t("chart_granularity_hint")
        )

    df_filtered = df[df["_anno"] == anno_sel].copy()
    if mese_sel:
        df_filtered = df_filtered[df_filtered["_mese_num"] == mese_sel]

    if granularita == t("chart_monthly"):
        df_filtered["_periodo"] = df_filtered["_data"].dt.to_period("M").astype(str)
    elif granularita == t("chart_weekly"):
        df_filtered["_periodo"] = df_filtered["_data"].dt.to_period("W").apply(lambda x: x.start_time.strftime("%Y-%m-%d"))
    else:
        df_filtered["_periodo"] = df_filtered["_data"].dt.strftime("%Y-%m-%d")

    df_tempo = df_filtered.groupby("_periodo").agg(
        uscite=("_uscita", "sum"),
        entrate=("_entrata", "sum")
    ).reset_index().sort_values("_periodo")

    max_uscite  = df_tempo["uscite"].max()
    max_entrate = df_tempo["entrate"].max()
    colori_uscite  = [f"rgba(83,74,183,{0.35 + 0.65*(v/max_uscite):.2f})"   if max_uscite  > 0 else "rgba(83,74,183,0.5)"  for v in df_tempo["uscite"]]
    colori_entrate = [f"rgba(255,102,0,{0.35 + 0.65*(v/max_entrate):.2f})"  if max_entrate > 0 else "rgba(255,102,0,0.5)"  for v in df_tempo["entrate"]]

    fig_tempo = go.Figure()
    fig_tempo.add_trace(go.Bar(
        x=df_tempo["_periodo"], y=df_tempo["uscite"],
        name=t("chart_expenses_label"),
        marker_color=colori_uscite,
        text=df_tempo["uscite"].apply(lambda v: f"€ {v:,.0f}"),
        textposition="inside",
        textfont=dict(color="white", size=11),
        hovertemplate="%{x}<br>" + t("chart_expenses_label") + ": € %{y:,.2f}<extra></extra>",
    ))
    fig_tempo.add_trace(go.Bar(
        x=df_tempo["_periodo"], y=df_tempo["entrate"],
        name=t("chart_income_label"),
        marker_color=colori_entrate,
        text=df_tempo["entrate"].apply(lambda v: f"€ {v:,.0f}"),
        textposition="inside",
        textfont=dict(color="white", size=11),
        hovertemplate="%{x}<br>" + t("chart_income_label") + ": € %{y:,.2f}<extra></extra>",
    ))

    mese_label = f" / {mesi_nomi[mese_sel]}" if mese_sel else ""
    fig_tempo.update_layout(
        **PLOTLY_BASE,
        barmode="group",
        title=f"{t('chart_expenses_label')} — {anno_sel}{mese_label} ({granularita})",
        yaxis_title="€",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=350,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=GRID),
        clickmode="event+select",
    )

    evento = st.plotly_chart(fig_tempo, use_container_width=True, on_select="rerun", key="chart_tempo")

    # Dettaglio al click
    periodo_selezionato = None
    if evento and evento.get("selection") and evento["selection"].get("points"):
        periodo_selezionato = evento["selection"]["points"][0].get("x")

    if periodo_selezionato:
        periodo_click = pd.to_datetime(str(periodo_selezionato)[:10])

        if granularita == t("chart_monthly"):
            mask = (
                (df_filtered["_data"].dt.year  == periodo_click.year) &
                (df_filtered["_data"].dt.month == periodo_click.month)
            )
            periodo_label = periodo_click.strftime("%Y-%m")

        elif granularita == t("chart_weekly"):
            periodi_dt = pd.to_datetime(pd.Series(df_filtered["_periodo"].unique()))
            diff = (periodi_dt - periodo_click).abs()
            periodo_più_vicino = periodi_dt.iloc[diff.argmin()]
            settimana_fine = periodo_più_vicino + pd.Timedelta(days=6)
            mask = (df_filtered["_data"] >= periodo_più_vicino) & (df_filtered["_data"] <= settimana_fine)
            periodo_label = periodo_più_vicino.strftime("%Y-%m-%d")

        else:
            periodi_dt = pd.to_datetime(pd.Series(df_filtered["_periodo"].unique()))
            diff = (periodi_dt - periodo_click).abs()
            periodo_più_vicino = periodi_dt.iloc[diff.argmin()]
            mask = df_filtered["_data"].dt.date == periodo_più_vicino.date()
            periodo_label = periodo_più_vicino.strftime("%Y-%m-%d")

        st.markdown(f"### {t('detail_click_title')} **{periodo_label}**")
        df_dettaglio = df_filtered[mask].copy()

        if df_dettaglio.empty:
            st.warning(f"{t('detail_no_data')}: {periodo_label}")
        else:
            m1, m2, m3 = st.columns(3)
            tot_usc = df_dettaglio["_uscita"].sum()
            tot_ent = df_dettaglio["_entrata"].sum()
            m1.metric(t("detail_expenses"), format_euro(tot_usc))
            m2.metric(t("detail_income"),   format_euro(tot_ent))
            m3.metric(t("detail_balance"),  format_euro(tot_ent - tot_usc))

            cols_display = []
            for c, label in [
                ("_data",         t("col_date")),
                ("nome_merchant", t("col_merchant_display")),
                ("categoria",     t("col_category_display")),
                ("_importo",      t("col_amount_display")),
                (col_desc,        t("col_notes_display")),
            ]:
                if c in df_dettaglio.columns:
                    cols_display.append((c, label))

            df_show = df_dettaglio[[c for c, _ in cols_display]].copy()
            df_show.columns = [l for _, l in cols_display]
            df_show[t("col_date")]         = pd.to_datetime(df_show[t("col_date")]).dt.strftime("%d/%m/%Y %H:%M")
            df_show[t("col_amount_display")] = df_show[t("col_amount_display")].apply(lambda v: format_euro(v) if pd.notna(v) else "—")
            df_show = df_show.sort_values(t("col_date")).reset_index(drop=True)
            st.dataframe(df_show, use_container_width=True, hide_index=True)
    else:
        st.caption(t("detail_hint"))

# ─────────────────────────────────────────────
# SEZIONE 3 — Spese per categoria nel tempo
# ─────────────────────────────────────────────

with st.container(border=True):
    section_header("📊", t("sec_cat_time_title"), t("sec_cat_time_desc"))

    top_n = st.slider(t("chart_n_categories"), min_value=3, max_value=min(12, n_categorie), value=min(6, n_categorie))

    top_categorie = df.groupby("categoria")["_uscita"].sum().nlargest(top_n).index.tolist()
    df_heatmap = df[df["categoria"].isin(top_categorie)].copy()
    df_heatmap["_mese_str"] = df_heatmap["_data"].dt.to_period("M").astype(str)

    pivot = df_heatmap.pivot_table(
        index="categoria", columns="_mese_str", values="_uscita", aggfunc="sum"
    ).fillna(0)

    fig_heat = px.imshow(
        pivot,
        color_continuous_scale="Blues",
        aspect="auto",
        labels=dict(x=t("chart_month"), y=t("col_categoria"), color="€"),
        title=t("chart_heatmap_title").format(n=top_n)
    )
    fig_heat.update_layout(**PLOTLY_BASE, height=350)
    st.plotly_chart(fig_heat, use_container_width=True)

# ─────────────────────────────────────────────
# SEZIONE 4 — Top merchant
# ─────────────────────────────────────────────

with st.container(border=True):
    section_header("🏪", t("sec_merchant_title"), t("sec_merchant_desc"))

    n_merchant = st.slider(t("chart_n_merchant"), min_value=5, max_value=30, value=15)

    df_merch = df[df["_uscita"].notna()].groupby("nome_merchant").agg(
        totale=("_uscita", "sum"),
        n_transazioni=("_uscita", "count"),
        media=("_uscita", "mean"),
        categoria=("categoria", "first")
    ).reset_index().sort_values("totale", ascending=False).head(n_merchant)

    cat_colors = {cat: PALETTE[i % len(PALETTE)] for i, cat in enumerate(df["categoria"].unique())}
    df_merch["colore"] = df_merch["categoria"].map(cat_colors)

    fig_merch = go.Figure(go.Bar(
        x=df_merch["nome_merchant"],
        y=df_merch["totale"],
        marker_color=df_merch["colore"],
        customdata=df_merch[["n_transazioni", "media", "categoria"]],
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Totale: € %{y:,.2f}<br>"
            f"{t('kpi_transactions')}: %{{customdata[0]}}<br>"
            "Media: € %{customdata[1]:,.2f}<br>"
            f"{t('col_category_display')}: %{{customdata[2]}}<extra></extra>"
        )
    ))
    fig_merch.update_layout(
        **PLOTLY_BASE,
        title=t("chart_top_merchant").format(n=n_merchant),
        xaxis_tickangle=-35,
        yaxis_title="€",
        height=420,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=GRID),
        #margin=dict(t=50, b=100, l=20, r=20),
    )
    st.plotly_chart(fig_merch, use_container_width=True)

# ─────────────────────────────────────────────
# SEZIONE 5 — Risparmio effettivo
# ─────────────────────────────────────────────

with st.container(border=True):
    section_header("💰", t("sec_savings_title"), t("sec_savings_desc"))

    df_mese_eff = (
        df.groupby("_mese_str")
        .agg(entrate=("_entrata", "sum"), uscite=("_uscita", "sum"))
        .reset_index()
        .sort_values("_mese_str")
    )
    df_mese_eff["risparmio"]   = df_mese_eff["entrate"] - df_mese_eff["uscite"]
    df_mese_eff["cumulato"]    = df_mese_eff["risparmio"].cumsum()
    df_mese_eff["colore_risp"] = df_mese_eff["risparmio"].apply(lambda x: "#1D9E75" if x >= 0 else "#E24B4A")

    totale_risp   = df_mese_eff["risparmio"].sum()
    media_mensile = df_mese_eff["risparmio"].mean()
    n_anni        = df[df["_entrata"].notna()]["_anno"].nunique() or 1
    media_annuale = totale_risp / n_anni

    k1, k2, k3 = st.columns(3)
    k1.metric(t("savings_total"),       f"€ {totale_risp:,.0f}")
    k2.metric(t("savings_monthly_avg"), f"€ {media_mensile:,.0f}")
    k3.metric(t("savings_yearly_avg"),  f"€ {media_annuale:,.0f}")

    fig_eff = go.Figure()
    fig_eff.add_trace(go.Bar(
        x=df_mese_eff["_mese_str"],
        y=df_mese_eff["risparmio"],
        name=t("chart_avg_savings"),
        marker_color=df_mese_eff["colore_risp"].tolist(),
        text=[f"€ {v:,.0f}" for v in df_mese_eff["risparmio"]],
        textposition="outside",
        textfont=dict(size=10),
        hovertemplate="<b>%{x}</b><br>" + t("chart_avg_savings") + ": %{text}<br>" + t("kpi_income") + ": €%{customdata[0]:,.0f}<br>" + t("kpi_expenses") + ": €%{customdata[1]:,.0f}<extra></extra>",
        customdata=df_mese_eff[["entrate", "uscite"]].values,
        yaxis="y",
    ))

    media_mobile = df_mese_eff["risparmio"].rolling(3, min_periods=1).mean()
    fig_eff.add_trace(go.Scatter(
        x=df_mese_eff["_mese_str"],
        y=media_mobile,
        name=t("chart_rolling"),
        mode="lines",
        line=dict(color="#FFBB33", width=1.5, dash="dot"),
        hovertemplate=t("chart_rolling") + ": €%{y:,.0f}<extra></extra>",
        yaxis="y",
    ))

    fig_eff.add_trace(go.Scatter(
        x=df_mese_eff["_mese_str"],
        y=df_mese_eff["cumulato"],
        name=t("chart_cumulative"),
        mode="lines+markers",
        line=dict(color="#7F77DD", width=2),
        marker=dict(size=6, color="#7F77DD"),
        hovertemplate=t("chart_cumulative") + ": €%{y:,.0f}<extra></extra>",
        yaxis="y2",
    ))

    fig_eff.add_hline(y=0, line_color=TEXT2, line_width=1)
    fig_eff.update_layout(
        **PLOTLY_BASE,
        title=t("chart_savings_title"),
        height=370,
        barmode="overlay",
        xaxis=dict(showgrid=False, tickfont=dict(size=11), tickangle=-45),
        yaxis=dict(showgrid=True, gridcolor=GRID, title="Risparmio (€)"),
        yaxis2=dict(
            overlaying="y", side="right", showgrid=False,
            tickfont=dict(color="#7F77DD", size=11),
            title="Cumulato (€)", titlefont=dict(color="#7F77DD"),
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02,
            xanchor="right", x=1, font=dict(size=10)
        ),
    )
        
    st.plotly_chart(fig_eff, use_container_width=True)

    # Barre per anno + heatmap
    col_anno, col_heat = st.columns([1, 2])

    with col_anno:
        df_anno_eff = (
            df.groupby("_anno")
            .agg(entrate=("_entrata", "sum"), uscite=("_uscita", "sum"))
            .reset_index()
        )
        df_anno_eff["risparmio_annuo"] = df_anno_eff["entrate"] - df_anno_eff["uscite"]
        df_anno_eff["media_mensile"]   = df_anno_eff.apply(
            lambda r: r["risparmio_annuo"] / max(df[df["_anno"] == r["_anno"]]["_mese_str"].nunique(), 1), axis=1
        )
        df_anno_eff["colore"] = df_anno_eff["risparmio_annuo"].apply(lambda x: "#1D9E75" if x >= 0 else "#E24B4A")

        fig_anno_eff = go.Figure(go.Bar(
            x=df_anno_eff["_anno"].astype(str),
            y=df_anno_eff["risparmio_annuo"],
            marker_color=df_anno_eff["colore"].tolist(),
            text=[f"€ {v:,.0f}" for v in df_anno_eff["risparmio_annuo"]],
            textposition="outside",
            textfont=dict(size=12),
            customdata=df_anno_eff["media_mensile"].values,
            hovertemplate="<b>%{x}</b><br>" + t("chart_savings_year") + ": %{text}<br>" + t("savings_monthly_avg") + ": €%{customdata:,.0f}<extra></extra>",
        ))
        fig_anno_eff.add_hline(y=0, line_color=TEXT2, line_width=1)
        fig_anno_eff.update_layout(
            **PLOTLY_BASE,
            title=t("chart_savings_year"),
            height=300,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor=GRID, range=[0, df_anno_eff["risparmio_annuo"].max() * 1.25]),
        )
        st.plotly_chart(fig_anno_eff, use_container_width=True)

    with col_heat:
        df_heat_data = df.groupby(["_anno", "_mese_num"]).apply(
            lambda g: g["_entrata"].sum() - g["_uscita"].sum()
        ).reset_index(name="risparmio")

        pivot_heat = df_heat_data.pivot(index="_mese_num", columns="_anno", values="risparmio")
        mesi_short = months_short_list()
        pivot_heat.index = [mesi_short[i-1] for i in pivot_heat.index]

        fig_heat2 = go.Figure(go.Heatmap(
            z=pivot_heat.values,
            x=[str(a) for a in pivot_heat.columns],
            y=pivot_heat.index,
            colorscale=[[0.0, "#E24B4A"], [0.5, "#F1EFE8"], [1.0, "#1D9E75"]],
            zmid=0,
            text=[[f"€ {v:,.0f}" if not (v != v) else "" for v in row] for row in pivot_heat.values],
            texttemplate="%{text}",
            textfont=dict(size=10),
            hovertemplate="<b>%{y} %{x}</b><br>" + t("sec_savings_title") + ": €%{z:,.0f}<extra></extra>",
            showscale=True,
            colorbar=dict(thickness=12, tickfont=dict(size=10)),
        ))
        fig_heat2.update_layout(
            **PLOTLY_BASE,
            title=t("chart_heatmap_savings"),
            height=270,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False, autorange="reversed"),
        )
        st.plotly_chart(fig_heat2, use_container_width=True)

    # Media mensile per anno
    st.markdown(t("savings_table_title"))

    df_media_anno = (
        df.groupby(["_anno", "_mese_str"])
        .apply(lambda g: pd.Series({
            "risparmio": g["_entrata"].sum() - g["_uscita"].sum(),
            "uscite":    g["_uscita"].sum(),
        }))
        .reset_index()
        .groupby("_anno")
        .agg(
            media_risparmio=("risparmio", "mean"),
            media_uscite=("uscite", "mean"),
        )
        .reset_index()
    )

    media_globale_risp = df_media_anno["media_risparmio"].mean()
    media_globale_usc  = df_media_anno["media_uscite"].mean()

    fig_avg = go.Figure()
    fig_avg.add_trace(go.Bar(
        x=-df_media_anno["media_uscite"],
        y=df_media_anno["_anno"].astype(str),
        orientation="h",
        name=t("chart_avg_expenses"),
        marker_color="#E24B4A",
        text=[f"−€ {v:,.0f}" for v in df_media_anno["media_uscite"]],
        textposition="inside",
        textfont=dict(size=11, color="white"),
        hovertemplate="<b>%{y}</b><br>" + t("chart_avg_expenses") + ": €%{customdata:,.0f}/mese<extra></extra>",
        customdata=df_media_anno["media_uscite"].values,
        width=0.4
    ))
    fig_avg.add_trace(go.Bar(
        x=df_media_anno["media_risparmio"],
        y=df_media_anno["_anno"].astype(str),
        orientation="h",
        name=t("chart_avg_savings"),
        marker_color=[("#1D9E75" if v >= 0 else "#FFA500") for v in df_media_anno["media_risparmio"]],
        text=[f"€ {v:,.0f}" for v in df_media_anno["media_risparmio"]],
        textposition="inside",
        textfont=dict(size=11, color="white"),
        hovertemplate="<b>%{y}</b><br>" + t("chart_avg_savings") + ": €%{text}/mese<extra></extra>",
        width=0.4
    ))

    fig_avg.add_shape(type="line", x0=0, x1=0, y0=0, y1=1, xref="x", yref="paper", line=dict(color=TEXT2, width=1), layer="above")
    add_vline_above(fig_avg, x=media_globale_risp,  color="#1D9E75", dash="dot", label=f"{t('chart_med_savings')} €{media_globale_risp:,.0f}",  label_position="top")
    add_vline_above(fig_avg, x=-media_globale_usc,  color="#E24B4A", dash="dot", label=f"{t('chart_med_expenses')} €{media_globale_usc:,.0f}", label_position="bottom")

    fig_avg.update_layout(
        **PLOTLY_BASE,
        title=t("chart_avg_title"),
        barmode="relative",
        height=max(220, len(df_media_anno) * 80 + 80),
        xaxis=dict(showgrid=True, gridcolor=GRID, tickformat=",.0f", tickprefix="€ ", zeroline=True),
        yaxis=dict(showgrid=False, autorange="reversed"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=11)),
    )
    st.plotly_chart(fig_avg, use_container_width=True)

    # Tabella riassuntiva
    df_table = (
        df.groupby(["_anno", "_mese_str"])
        .apply(lambda g: g["_entrata"].sum() - g["_uscita"].sum())
        .reset_index(name="risparmio")
        .groupby("_anno")
        .agg(
            media_mensile=("risparmio", "mean"),
            mesi_attivi=("risparmio", "count"),
            totale=("risparmio", "sum"),
        )
        .reset_index()
    )
    st.dataframe(
        df_table.rename(columns={
            "_anno":         t("table_year"),
            "media_mensile": t("table_monthly_avg"),
            "totale":        t("table_total"),
            "mesi_attivi":   t("table_active_months"),
        }).style.format({
            t("table_monthly_avg"): "{:,.0f}",
            t("table_total"):       "{:,.0f}",
        }),
        use_container_width=True,
        hide_index=True,
    )

# ─────────────────────────────────────────────
# SEZIONE 6 — Dettaglio movimenti
# ─────────────────────────────────────────────

with st.container(border=True):
    section_header("🔍", t("sec_detail_title"), t("sec_detail_desc"))

    cols_mostra = [col_data, col_importo, "nome_merchant", "categoria", col_desc, "confidenza", "fonte"]
    cols_mostra = [c for c in cols_mostra if c in df.columns]
    df_view = df[cols_mostra].copy()

    sc1, sc2 = st.columns([3, 1])
    with sc1:
        cerca = st.text_input(t("search_label"), "")
    with sc2:
        colonna_cerca = st.selectbox(t("search_col"), [t("search_all_cols")] + cols_mostra)

    if cerca:
        if colonna_cerca == t("search_all_cols"):
            mask = df_view.apply(lambda row: row.astype(str).str.contains(cerca, case=False).any(), axis=1)
        else:
            mask = df_view[colonna_cerca].astype(str).str.contains(cerca, case=False)
        df_view = df_view[mask]

    st.dataframe(
        df_view.sort_values(col_data, ascending=False) if col_data in df_view.columns else df_view,
        use_container_width=True,
        height=400
    )
    st.caption(f"{len(df_view)} {t('movements_shown')}")

# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────

st.markdown("---")
col_exp1, col_exp2, _ = st.columns([1, 1, 3])

with col_exp1:
    csv_out = df[cols_mostra].to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        t("export_csv"),
        data=csv_out.encode("utf-8-sig"),
        file_name="movimenti_filtrati.csv",
        mime="text/csv"
    )

with col_exp2:
    try:
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df[cols_mostra].to_excel(writer, index=False, sheet_name="Movimenti")
            df_cat.to_excel(writer, index=False, sheet_name="Riepilogo categorie")
        st.download_button(
            t("export_excel"),
            data=buffer.getvalue(),
            file_name="movimenti_analisi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except ImportError:
        st.caption(t("export_openpyxl"))



with st.container(border=True):
    section_header("💬", t("chat_detail_title"), t("chat_detail_desc"))



    # ── Pagina chat ────────────────────────────────────────────────────────────
    
    df_chat = df  
    
    if df_chat is None:
        st.warning(t("chat_error"))
        st.stop()
    
    # Non serve più build_chat_agent — inizializziamo solo la history
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    
    history = st.session_state["chat_history"]
    
    # ── Mostra la history ──────────────────────────────────────────────────────
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    
    # ── Input utente ───────────────────────────────────────────────────────────
    domanda = st.chat_input(t("chat_question_load"))
    
    if domanda:
        with st.chat_message("user"):
            st.markdown(domanda)
        history.append({"role": "user", "content": domanda})
    
        with st.chat_message("assistant"):
            with st.spinner(t("chat_elaboration")):
                risposta = ask_agent(domanda, df_chat)  # ← ordine parametri cambiato
            st.markdown(risposta)
    
        history.append({"role": "assistant", "content": risposta})
        st.session_state["chat_history"] = history
