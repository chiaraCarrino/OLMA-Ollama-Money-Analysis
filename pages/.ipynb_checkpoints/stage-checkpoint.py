
.section-title {
        font-family: 'DM Serif Display', serif;
        font-size: 1.4rem;
        color: #1a1a2e;
        margin: 2rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e2e8f0;
    }


.section-card {
        background: #ffffff;
        border: 1.5px solid #e8e6e0;
        border-radius: 16px;
        padding: 1.4rem 1.6rem 1.8rem;
        margin: 1.2rem 0 0.4rem;
        box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    }

granularita = st.radio("Granularità", ["Annuale","Mensile", "Settimanale", "Giornaliero"], horizontal=True, index=0)

if granularita == "Annuale":
    df["_periodo"] = df["_data"].dt.to_period("Y").astype(str)
elif granularita == "Mensile":
    df["_periodo"] = df["_data"].dt.to_period("M").astype(str)
elif granularita == "Settimanale":
    df["_periodo"] = df["_data"].dt.to_period("W").apply(lambda x: str(x.start_time.date()))
else:
    df["_periodo"] = df["_data"].dt.date.astype(str)

df_tempo = df.groupby("_periodo").agg(
    uscite=("_uscita", "sum"),
    entrate=("_entrata", "sum")
).reset_index().sort_values("_periodo")

fig_tempo = go.Figure()
fig_tempo.add_trace(go.Bar(
    x=df_tempo["_periodo"], y=df_tempo["uscite"],
    name="Uscite", marker_color="#ef4444",
    text=df_tempo["uscite"].apply(lambda v: f"€ {v:,.0f}"),
    textposition="inside",
    textfont=dict(color="white", size=11),
    hovertemplate="%{x}<br>Uscite: € %{y:,.2f}<extra></extra>"
))
fig_tempo.add_trace(go.Bar(
    x=df_tempo["_periodo"], y=df_tempo["entrate"],
    name="Entrate", marker_color="#22c55e",
    text=df_tempo["entrate"].apply(lambda v: f"€ {v:,.0f}"),
    textposition="inside",
    textfont=dict(color="white", size=11),
    hovertemplate="%{x}<br>Entrate: € %{y:,.2f}<extra></extra>"
))
fig_tempo.update_layout(
    barmode="group",
    title=f"Entrate vs Uscite ({granularita})",
    xaxis_title="",
    yaxis_title="€",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=60, b=20, l=20, r=20),
    height=350,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="DM Sans",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="#f1f5f9")
)
st.plotly_chart(fig_tempo, use_container_width=True)



# ─────────────────────────────────────────────
# GRAFICI — RIGA 2 (andamento temporale)
# ─────────────────────────────────────────────
st.markdown("<div class='section-title'>Andamento temporale SOLO USCITE</div>", unsafe_allow_html=True)

# ── Filtri Anno / Mese ───────────────────────
anni_disponibili = sorted(df["_anno"].dropna().unique().astype(int).tolist(), reverse=True)
mesi_nomi = {1:"Gennaio",2:"Febbraio",3:"Marzo",4:"Aprile",5:"Maggio",6:"Giugno",
             7:"Luglio",8:"Agosto",9:"Settembre",10:"Ottobre",11:"Novembre",12:"Dicembre"}

f1, f2, f3 = st.columns([1, 1, 2])
with f1:
    anno_sel = st.selectbox("Anno", anni_disponibili, index=0)
with f2:
    mese_options = ["Tutti i mesi"] + [f"{v} ({k:02d})" for k, v in mesi_nomi.items()]
    mese_sel_label = st.selectbox("Mese", mese_options, index=0)
    mese_sel = None if mese_sel_label == "Tutti i mesi" else int(mese_sel_label.split("(")[1].replace(")", ""))
with f3:
    granularita = st.radio(
        "Granularità", ["Mensile", "Settimanale", "Giornaliero"],
        horizontal=True, index=0,
        help="Se selezioni un mese specifico la granularità passa automaticamente a Giornaliero"
    )

# Applica filtro
df_filtered = df[df["_anno"] == anno_sel].copy()
if mese_sel:
    df_filtered = df_filtered[df_filtered["_mese"] == mese_sel]
    granularita = "Giornaliero"  # forza giornaliero quando c'è un mese selezionato

# Periodo
if granularita == "Mensile":
    df_filtered["_periodo"] = df_filtered["_data"].dt.to_period("M").astype(str)
elif granularita == "Settimanale":
    df_filtered["_periodo"] = df_filtered["_data"].dt.to_period("W").apply(lambda x: str(x.start_time.date()))
else:
    df_filtered["_periodo"] = df_filtered["_data"].dt.date.astype(str)

df_tempo = df_filtered.groupby("_periodo").agg(
    uscite=("_uscita", "sum"),
    entrate=("_entrata", "sum")
).reset_index().sort_values("_periodo")

# ── Grafico ──────────────────────────────────
fig_tempo = go.Figure()
max_uscite = df_tempo["uscite"].max()
colori = [
    f"rgba(83,74,183,{0.35 + 0.65*(v/max_uscite):.2f})" if max_uscite > 0 else "rgba(83,74,183,0.5)"
    for v in df_tempo["uscite"]
]

fig_tempo.add_trace(go.Bar(
    x=df_tempo["_periodo"], y=df_tempo["uscite"],
    name="Uscite",
    marker_color=colori,
    text=df_tempo["uscite"].apply(lambda v: f"€ {v:,.0f}"),
    textposition="inside",
    textfont=dict(color="white", size=11),
    hovertemplate="%{x}<br>Uscite: € %{y:,.2f}<extra></extra>",
))
fig_tempo.update_layout(
    barmode="group",
    title=f"Uscite — {anno_sel}{' / ' + mesi_nomi[mese_sel] if mese_sel else ''}  ({granularita})",
    xaxis_title="",
    yaxis_title="€",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=60, b=20, l=20, r=20),
    height=350,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="DM Sans",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
    clickmode="event+select",
)

evento = st.plotly_chart(fig_tempo, use_container_width=True, on_select="rerun", key="chart_tempo")

# ── Tabella dettaglio al click ────────────────
# Costruisci _periodo su df_filtered UNA VOLTA SOLA, prima del grafico
if granularita == "Giornaliero":
    df_filtered["_periodo"] = df_filtered["_data"].dt.strftime("%Y-%m-%d")
elif granularita == "Settimanale":
    df_filtered["_periodo"] = df_filtered["_data"].dt.to_period("W").apply(
        lambda x: x.start_time.strftime("%Y-%m-%d")
    )
else:
    df_filtered["_periodo"] = df_filtered["_data"].dt.to_period("M").astype(str)

df_tempo = df_filtered.groupby("_periodo").agg(
    uscite=("_uscita", "sum")#,
    #entrate=("_entrata", "sum")
).reset_index().sort_values("_periodo")


# ── Tabella dettaglio al click ────────────────
periodo_selezionato = None
if evento and evento.get("selection") and evento["selection"].get("points"):
    periodo_selezionato = evento["selection"]["points"][0].get("x")

if periodo_selezionato:
    # Tronca al formato usato in _periodo
    if granularita == "Mensile":
        periodo_clean = str(periodo_selezionato)[:7]   # "YYYY-MM"
    else:
        periodo_clean = str(periodo_selezionato)[:10]  # "YYYY-MM-DD"

    st.markdown(f"### 🔍 Dettaglio spese — **{periodo_clean}**")

    # _periodo è già nel df_filtered con il formato corretto — match diretto
    mask = df_filtered["_periodo"] == periodo_clean
    df_dettaglio = df_filtered[mask].copy()

    if df_dettaglio.empty:
        st.warning(f"Nessuna transazione trovata per: {periodo_clean}")
        with st.expander("🔧 Debug"):
            st.write("Periodi disponibili:", df_filtered["_periodo"].unique().tolist())
            st.write(f"Cercato: '{periodo_clean}'")
    else:
        m1, m2, m3 = st.columns(3)
        tot_usc = df_dettaglio["_uscita"].sum()
        #tot_ent = df_dettaglio["_entrata"].sum()
        m1.metric("Uscite",  format_euro(tot_usc))
        #m2.metric("Entrate", format_euro(tot_ent))
        #m3.metric("Saldo",   format_euro(tot_ent - tot_usc))

        cols_display = []
        for c, label in [
            ("_data",         "Data"),
            ("nome_merchant", "Merchant"),
            ("categoria",     "Categoria"),
            ("_importo",      "Importo (€)"),
            (col_desc,        "Note"),
        ]:
            if c in df_dettaglio.columns:
                cols_display.append((c, label))

        df_show = df_dettaglio[[c for c, _ in cols_display]].copy()
        df_show.columns = [l for _, l in cols_display]
        df_show["Data"] = pd.to_datetime(df_show["Data"]).dt.strftime("%d/%m/%Y %H:%M")
        df_show["Importo (€)"] = df_show["Importo (€)"].apply(
            lambda v: format_euro(v) if pd.notna(v) else "—"
        )
        df_show = df_show.sort_values("Data").reset_index(drop=True)
        st.dataframe(df_show, use_container_width=True, hide_index=True)

else:
    st.caption("💡 Clicca su una barra del grafico per vedere le spese del periodo.")


####################################################################################à

# ─────────────────────────────────────────────
# GRAFICI — RIGA 2 (andamento temporale)
# ─────────────────────────────────────────────



# ─────────────────────────────────────────────
# GRAFICI — RIGA 2 (andamento temporale)
# ─────────────────────────────────────────────
section_card_open(
    "📈",
    "Andamento temporale — Entrate e Uscite",
    "Confronto mensile, settimanale o giornaliero tra entrate e uscite. Clicca su una barra per il dettaglio."
)

# ── Filtri Anno / Mese ───────────────────────
anni_disponibili = sorted(df["_anno"].dropna().unique().astype(int).tolist(), reverse=True)
mesi_nomi = {1:"Gennaio",2:"Febbraio",3:"Marzo",4:"Aprile",5:"Maggio",6:"Giugno",
             7:"Luglio",8:"Agosto",9:"Settembre",10:"Ottobre",11:"Novembre",12:"Dicembre"}

f1, f2, f3 = st.columns([1, 1, 2])
with f1:
    anno_sel = st.selectbox("Anno", anni_disponibili, index=0)
with f2:
    mese_options = ["Tutti i mesi"] + [f"{v} ({k:02d})" for k, v in mesi_nomi.items()]
    mese_sel_label = st.selectbox("Mese", mese_options, index=0)
    mese_sel = None if mese_sel_label == "Tutti i mesi" else int(mese_sel_label.split("(")[1].replace(")", ""))
with f3:
    granularita = st.radio(
        "Granularità", ["Mensile", "Settimanale", "Giornaliero"],
        horizontal=True, index=0,
        help="Se selezioni un mese specifico la granularità passa automaticamente a Giornaliero"
    )

# Applica filtro
df_filtered = df[df["_anno"] == anno_sel].copy()
if mese_sel:
    df_filtered = df_filtered[df_filtered["_mese_num"] == mese_sel]
    #granularita = "Giornaliero"  # forza giornaliero quando c'è un mese selezionato

# Periodo
if granularita == "Mensile":
    df_filtered["_periodo"] = df_filtered["_data"].dt.to_period("M").astype(str)
elif granularita == "Settimanale":
    df_filtered["_periodo"] = df_filtered["_data"].dt.to_period("W").apply(lambda x: x.start_time.strftime("%Y-%m-%d"))
else:
    df_filtered["_periodo"] = df_filtered["_data"].dt.strftime("%Y-%m-%d")

df_tempo = df_filtered.groupby("_periodo").agg(
    uscite=("_uscita", "sum"),
    entrate=("_entrata", "sum")
).reset_index().sort_values("_periodo")

# ── Grafico ──────────────────────────────────
fig_tempo = go.Figure()
max_uscite = df_tempo["uscite"].max()
max_entrate = df_tempo["entrate"].max()
colori_uscite = [
    f"rgba(83,74,183,{0.35 + 0.65*(v/max_uscite):.2f})" if max_uscite > 0 else "rgba(83,74,183,0.5)"
    for v in df_tempo["uscite"]

]
colori_entrate=[f"rgba(255, 102, 0,{0.35 + 0.65*(v/max_entrate):.2f})" if max_entrate > 0 else "rgba(255, 102, 0,0.5)"
    for v in df_tempo["entrate"]]

fig_tempo.add_trace(go.Bar(
    x=df_tempo["_periodo"], y=df_tempo["uscite"],
    name="Uscite",
    marker_color=colori_uscite,
    text=df_tempo["uscite"].apply(lambda v: f"€ {v:,.0f}"),
    textposition="inside",
    textfont=dict(color="white", size=11),
    hovertemplate="%{x}<br>Uscite: € %{y:,.2f}<extra></extra>",
))

fig_tempo.add_trace(go.Bar(
    x=df_tempo["_periodo"], y=df_tempo["entrate"],
    name="Entrate",
    marker_color=colori_entrate,
    text=df_tempo["entrate"].apply(lambda v: f"€ {v:,.0f}"),
    textposition="inside",
    textfont=dict(color="white", size=11),
    hovertemplate="%{x}<br>Entrate: € %{y:,.2f}<extra></extra>",
))
fig_tempo.update_layout(
    barmode="group",
    title=f"Uscite — {anno_sel}{' / ' + mesi_nomi[mese_sel] if mese_sel else ''}  ({granularita})",
    xaxis_title="",
    yaxis_title="€",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(t=60, b=20, l=20, r=20),
    height=350,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="DM Sans",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="#f1f5f9"),
    clickmode="event+select",
)

evento = st.plotly_chart(fig_tempo, use_container_width=True, on_select="rerun", key="chart_tempo")




# ── Tabella dettaglio al click ────────────────
periodo_selezionato = None
if evento and evento.get("selection") and evento["selection"].get("points"):
    periodo_selezionato = evento["selection"]["points"][0].get("x")

if periodo_selezionato:
    periodo_click = pd.to_datetime(str(periodo_selezionato)[:10])

    if granularita == "Mensile":
        mask = (
            (df_filtered["_data"].dt.year == periodo_click.year) &
            (df_filtered["_data"].dt.month == periodo_click.month)
        )
        periodo_label = periodo_click.strftime("%Y-%m")

    elif granularita == "Settimanale":
        periodi_dt = pd.to_datetime(pd.Series(df_filtered["_periodo"].unique()))
        diff = (periodi_dt - periodo_click).abs()
        periodo_più_vicino = periodi_dt.iloc[diff.argmin()]
        settimana_fine = periodo_più_vicino + pd.Timedelta(days=6)
        mask = (
            (df_filtered["_data"] >= periodo_più_vicino) &
            (df_filtered["_data"] <= settimana_fine)
        )
        periodo_label = periodo_più_vicino.strftime("%Y-%m-%d")

    else:  # Giornaliero
        periodi_dt = pd.to_datetime(pd.Series(df_filtered["_periodo"].unique()))
        diff = (periodi_dt - periodo_click).abs()
        periodo_più_vicino = periodi_dt.iloc[diff.argmin()]
        mask = df_filtered["_data"].dt.date == periodo_più_vicino.date()
        periodo_label = periodo_più_vicino.strftime("%Y-%m-%d")

    st.markdown(f"### 🔍 Dettaglio spese — **{periodo_label}**")
    df_dettaglio = df_filtered[mask].copy()

    if df_dettaglio.empty:
        st.warning(f"Nessuna transazione trovata per: {periodo_label}")
    else:
        m1, m2, m3 = st.columns(3)
        tot_usc = df_dettaglio["_uscita"].sum()
        tot_ent = df_dettaglio["_entrata"].sum()
        m1.metric("Uscite",  format_euro(tot_usc))
        m2.metric("Entrate", format_euro(tot_ent))
        m3.metric("Saldo",   format_euro(tot_ent - tot_usc))

        cols_display = []
        for c, label in [
            ("_data",         "Data"),
            ("nome_merchant", "Merchant"),
            ("categoria",     "Categoria"),
            ("_importo",      "Importo (€)"),
            (col_desc,        "Note"),
        ]:
            if c in df_dettaglio.columns:
                cols_display.append((c, label))

        df_show = df_dettaglio[[c for c, _ in cols_display]].copy()
        df_show.columns = [l for _, l in cols_display]
        df_show["Data"] = pd.to_datetime(df_show["Data"]).dt.strftime("%d/%m/%Y %H:%M")
        df_show["Importo (€)"] = df_show["Importo (€)"].apply(
            lambda v: format_euro(v) if pd.notna(v) else "—"
        )
        df_show = df_show.sort_values("Data").reset_index(drop=True)
        st.dataframe(df_show, use_container_width=True, hide_index=True)

else:
    st.caption("💡 Clicca su una barra del grafico per vedere le spese del periodo.")
section_card_close()
# ─────────────────────────────────────────────
# GRAFICI — RIGA 3 (spese per categoria nel tempo)
# ─────────────────────────────────────────────

section_card_open(
    "📊",
    "Spese per categoria nel tempo",
    "Evoluzione della spesa per ciascuna categoria mese dopo mese."
)
top_n = st.slider("Numero di categorie da mostrare", min_value=3, max_value=min(12, n_categorie), value=min(6, n_categorie))

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
    labels=dict(x="Mese", y="Categoria", color="€"),
    title=f"Heatmap spese mensili — top {top_n} categorie"
)
fig_heat.update_layout(
    height=350,
    margin=dict(t=50, b=20, l=20, r=20),
    paper_bgcolor="rgba(0,0,0,0)",
    font_family="DM Sans"
)
st.plotly_chart(fig_heat, use_container_width=True)
section_card_close()
# ─────────────────────────────────────────────
# GRAFICI — RIGA 4 (analisi per merchant)
# ─────────────────────────────────────────────

section_card_open(
    "🏪",
    "Top merchant per spesa",
    "I negozi e servizi su cui hai speso di più nel periodo."
)
n_merchant = st.slider("Numero di merchant", min_value=5, max_value=30, value=15)

df_merch = df[df["_uscita"].notna()].groupby("nome_merchant").agg(
    totale=("_uscita", "sum"),
    n_transazioni=("_uscita", "count"),
    media=("_uscita", "mean"),
    categoria=("categoria", "first")
).reset_index().sort_values("totale", ascending=False).head(n_merchant)

# Mappa categoria → colore
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
        "Transazioni: %{customdata[0]}<br>"
        "Media: € %{customdata[1]:,.2f}<br>"
        "Categoria: %{customdata[2]}<extra></extra>"
    )
))
fig_merch.update_layout(
    title=f"Top {n_merchant} merchant per spesa totale",
    xaxis_tickangle=-35,
    yaxis_title="€",
    margin=dict(t=50, b=100, l=20, r=20),
    height=420,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_family="DM Sans",
    xaxis=dict(showgrid=False),
    yaxis=dict(showgrid=True, gridcolor="#f1f5f9")
)
st.plotly_chart(fig_merch, use_container_width=True)

section_card_close()

# ─────────────────────────────────────────────
# SEZIONE: RISPARMIO EFFETTIVO (entrate - uscite)
# ─────────────────────────────────────────────
section_card_open(
    "💰",
    "Risparmio effettivo",
    "Differenza tra entrate e uscite: quanto hai realmente messo da parte ogni mese."
)
# ── Aggregazione per mese con entrate e uscite
df_mese_eff = (
    df.groupby("_mese_str")
    .agg(
        entrate=("_entrata", "sum"),
        uscite=("_uscita", "sum"),
    )
    .reset_index()
    .sort_values("_mese_str")
)

df_mese_eff["risparmio"]    = df_mese_eff["entrate"] - df_mese_eff["uscite"]
df_mese_eff["cumulato"]     = df_mese_eff["risparmio"].cumsum()
df_mese_eff["colore_risp"]  = df_mese_eff["risparmio"].apply(
    lambda x: "#1D9E75" if x >= 0 else "#E24B4A"
)

# ── KPI in evidenza
totale_risp   = df_mese_eff["risparmio"].sum()
media_mensile = df_mese_eff["risparmio"].mean()
n_anni        = df[df["_entrata"].notna()]["_anno"].nunique() or 1
media_annuale = totale_risp / n_anni

k1, k2, k3 = st.columns(3)
k1.metric("Risparmio totale",  f"€ {totale_risp:,.0f}")
k2.metric("Media mensile",     f"€ {media_mensile:,.0f}")
k3.metric("Media annuale",     f"€ {media_annuale:,.0f}")

# ── Grafico principale: barre risparmio mensile + linea cumulato
fig_eff = go.Figure()

# Barre risparmio mensile (verde/rosso)
fig_eff.add_trace(go.Bar(
    x=df_mese_eff["_mese_str"],
    y=df_mese_eff["risparmio"],
    name="Risparmio mensile",
    marker_color=df_mese_eff["colore_risp"].tolist(),
    text=[f"€ {v:,.0f}" for v in df_mese_eff["risparmio"]],
    textposition="outside",
    textfont=dict(size=10),
    hovertemplate=(
        "<b>%{x}</b><br>"
        "Risparmio: %{text}<br>"
        "Entrate: €%{customdata[0]:,.0f}<br>"
        "Uscite: €%{customdata[1]:,.0f}<extra></extra>"
    ),
    customdata=df_mese_eff[["entrate", "uscite"]].values,
    yaxis="y",
))

# Media mobile mensile (linea tratteggiata)
media_mobile = df_mese_eff["risparmio"].rolling(3, min_periods=1).mean()
fig_eff.add_trace(go.Scatter(
    x=df_mese_eff["_mese_str"],
    y=media_mobile,
    name="Media mobile 3m",
    mode="lines",
    line=dict(color="#FFBB33", width=1.5, dash="dot"),
    hovertemplate="Media 3m: €%{y:,.0f}<extra></extra>",
    yaxis="y",
))

# Linea cumulato (asse secondario)
fig_eff.add_trace(go.Scatter(
    x=df_mese_eff["_mese_str"],
    y=df_mese_eff["cumulato"],
    name="Cumulato",
    mode="lines+markers",
    line=dict(color="#7F77DD", width=2),
    marker=dict(size=6, color="#7F77DD"),
    hovertemplate="Cumulato: €%{y:,.0f}<extra></extra>",
    yaxis="y2",
))

# Linea dello zero
fig_eff.add_hline(y=0, line_color=TEXT2, line_width=1)

fig_eff.update_layout(
    **PLOTLY_BASE,
    title="Risparmio effettivo mensile (entrate − uscite)",
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

# ── Riga inferiore: barre per anno + heatmap mensile
col_anno, col_heat = st.columns([1, 2])

with col_anno:
    # Risparmio aggregato per anno
    df_anno_eff = (
        df.groupby("_anno")
        .agg(entrate=("_entrata", "sum"), uscite=("_uscita", "sum"))
        .reset_index()
    )
    df_anno_eff["risparmio_annuo"] = df_anno_eff["entrate"] - df_anno_eff["uscite"]
    df_anno_eff["media_mensile"]   = df_anno_eff.apply(
        lambda r: r["risparmio_annuo"] / max(
            df[df["_anno"] == r["_anno"]]["_mese_str"].nunique(), 1
        ), axis=1
    )
    df_anno_eff["colore"] = df_anno_eff["risparmio_annuo"].apply(
        lambda x: "#1D9E75" if x >= 0 else "#E24B4A"
    )

    fig_anno_eff = go.Figure(go.Bar(
        x=df_anno_eff["_anno"].astype(str),
        y=df_anno_eff["risparmio_annuo"],
        marker_color=df_anno_eff["colore"].tolist(),
        text=[f"€ {v:,.0f}" for v in df_anno_eff["risparmio_annuo"]],
        textposition="outside",
        textfont=dict(size=12),
        customdata=df_anno_eff["media_mensile"].values,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Risparmio annuo: %{text}<br>"
            "Media mensile: €%{customdata:,.0f}<extra></extra>"
        ),
    ))
    fig_anno_eff.add_hline(y=0, line_color=TEXT2, line_width=1)
    fig_anno_eff.update_layout(
        **PLOTLY_BASE,
        title="Risparmio per anno",
        height=300,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor=GRID, rangemode="tozero",        # parte sempre da 0
    range=[0, df_anno_eff["risparmio_annuo"].max() * 1.25],), 
        
    )
    st.plotly_chart(fig_anno_eff, use_container_width=True)

with col_heat:
    # Heatmap mese × anno — mostra a colpo d'occhio i mesi migliori/peggiori
    df_heat = df.groupby(["_anno", "_mese_num"]).apply(
        lambda g: g["_entrata"].sum() - g["_uscita"].sum()
    ).reset_index(name="risparmio")

    pivot = df_heat.pivot(index="_mese_num", columns="_anno", values="risparmio")
    nomi_mesi = ["Gen","Feb","Mar","Apr","Mag","Giu",
                 "Lug","Ago","Set","Ott","Nov","Dic"]
    pivot.index = [nomi_mesi[i-1] for i in pivot.index]

    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[str(a) for a in pivot.columns],
        y=pivot.index,
        colorscale=[
            [0.0, "#E24B4A"],   # rosso per valori negativi
            [0.5, "#F1EFE8"],   # neutro
            [1.0, "#1D9E75"],   # verde per valori positivi
        ],
        zmid=0,
        text=[[f"€ {v:,.0f}" if not (v != v) else "" for v in row]
              for row in pivot.values],
        texttemplate="%{text}",
        textfont=dict(size=10),
        hovertemplate="<b>%{y} %{x}</b><br>Risparmio: €%{z:,.0f}<extra></extra>",
        showscale=True,
        colorbar=dict(thickness=12, tickfont=dict(size=10)),
    ))
    fig_heat.update_layout(
        **PLOTLY_BASE,
        title="Heatmap risparmio (mese × anno)",
        height=270,
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=False, autorange="reversed"),
    )
    st.plotly_chart(fig_heat, use_container_width=True)


# ─────────────────────────────────────────────
# MEDIA MENSILE RISPARMIO vs USCITE PER ANNO
# ─────────────────────────────────────────────
st.markdown("#### Media mensile per anno")

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
        media_uscite=("uscite",    "mean"),
    )
    .reset_index()
)

media_globale_risp  = df_media_anno["media_risparmio"].mean()
media_globale_usc   = df_media_anno["media_uscite"].mean()

fig = go.Figure()

# Barre uscite medie (grigio/arancio, sempre negative visivamente)
fig.add_trace(go.Bar(
    x=-df_media_anno["media_uscite"],
    y=df_media_anno["_anno"].astype(str),
    orientation="h",
    name="Uscite medie/mese",
    marker_color="#E24B4A",
    text=[f"−€ {v:,.0f}" for v in df_media_anno["media_uscite"]],
    textposition="inside",
    textfont=dict(size=11, color="white"),
    hovertemplate="<b>%{y}</b><br>Uscite medie: €%{customdata:,.0f}/mese<extra></extra>",
    customdata=df_media_anno["media_uscite"].values,
    width=0.4
))

# Barre risparmio medio (verde/rosso)
fig.add_trace(go.Bar(
    x=df_media_anno["media_risparmio"],
    y=df_media_anno["_anno"].astype(str),
    orientation="h",
    name="Risparmio medio/mese",
    marker_color=[("#1D9E75" if v >= 0 else "#FFA500") for v in df_media_anno["media_risparmio"]],
    text=[f"€ {v:,.0f}" for v in df_media_anno["media_risparmio"]],
    textposition="inside",
    textfont=dict(size=11, color="white"),
    hovertemplate="<b>%{y}</b><br>Risparmio medio: €%{text}/mese<extra></extra>",
    customdata=df_media_anno["media_risparmio"].values,
    width=0.4
))

# Linee medie globali
def add_vline_above(fig, x, color, dash, label, label_position="top"):
    """
    Disegna una linea verticale SOPRA le barre (layer='above')
    con annotazione sempre visibile.
    label_position: 'top' | 'bottom'
    """
    fig.add_shape(
        type="line",
        x0=x, x1=x,
        y0=0, y1=1,
        xref="x", yref="paper",   # yref=paper → copre tutta l'altezza
        line=dict(color=color, width=1.5, dash=dash),
        layer="above",             # ← chiave: sopra le barre
    )
    fig.add_annotation(
        x=x,
        y=1 if label_position == "top" else 0,
        xref="x", yref="paper",
        text=label,
        showarrow=False,
        font=dict(color=color, size=12),
        bgcolor="rgba(255,255,255,0.75)",   # sfondo semi-trasparente
        borderpad=3,
        xanchor="left" if x >= 0 else "right",
        yanchor="bottom" if label_position == "top" else "top",
    )
 
# Linea zero
fig.add_shape(
    type="line",
    x0=0, x1=0,
    y0=0, y1=1,
    xref="x", yref="paper",
    line=dict(color=TEXT2, width=1),
    layer="above",
)
 
# Media risparmio
add_vline_above(
    fig,
    x=media_globale_risp,
    color="#1D9E75",
    dash="dot",
    label=f"Med. risp. €{media_globale_risp:,.0f}",
    label_position="top",
)
 
# Media uscite
add_vline_above(
    fig,
    x=-media_globale_usc,
    color="#E24B4A",
    dash="dot",
    label=f"Med. usc. €{media_globale_usc:,.0f}",
    label_position="bottom",
)

fig.update_layout(
    **PLOTLY_BASE,
    title="Media mensile per anno — risparmio vs uscite",
    barmode="relative",
    height=max(220, len(df_media_anno) * 80 + 80),
    xaxis=dict(
        showgrid=True, gridcolor=GRID,
        tickformat=",.0f",
        tickprefix="€ ",
        zeroline=True,
    ),
    yaxis=dict(showgrid=False, autorange="reversed"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="right", x=1, font=dict(size=11))#,
    #margin=dict(l=60, r=180),
)
st.plotly_chart(fig, use_container_width=True)
# ── Tabella riassuntiva
# Calcolo media mensile per anno
df_media_anno = (
    df.groupby(["_anno", "_mese_str"])
    .apply(lambda g: g["_entrata"].sum() - g["_uscita"].sum())
    .reset_index(name="risparmio")
    .groupby("_anno")
    .agg(
        media_mensile=("risparmio", "mean"),
        mesi_attivi=("risparmio", "count"),
        totale=("risparmio", "sum"),
        mese_migliore=("risparmio", "max"),
        mese_peggiore=("risparmio", "min"),
    )
    .reset_index()
)
df_media_anno["colore"] = df_media_anno["media_mensile"].apply(
    lambda x: "#1D9E75" if x >= 0 else "#E24B4A"
)


st.dataframe(
    df_media_anno[["_anno", "media_mensile", "totale", "mesi_attivi"]]#, "mese_migliore", "mese_peggiore"]]
    .rename(columns={
        "_anno": "Anno",
        "media_mensile": "Media mensile di Risparmio (€)",
        "totale": "Totale annuo (€)",
        "mesi_attivi": "Mesi registrati"#,
        #"mese_migliore": "Mese migliore (€)",
        #"mese_peggiore": "Mese peggiore (€)",
    })
    .style.format({
        "Media mensile (€)": "{:,.0f}",
        "Totale annuo (€)": "{:,.0f}"#,
        #"Mese migliore (€)": "{:,.0f}",
        #"Mese peggiore (€)": "{:,.0f}",
    }),
    use_container_width=True,
    hide_index=True,
)


section_card_close()

# ─────────────────────────────────────────────
# TABELLA DATI
# ─────────────────────────────────────────────

section_card_open(
    "🔍",
    "Dettaglio movimenti",
    "Elenco completo delle transazioni con filtri per ricerca e categoria."
)
# Filtro testuale
#cerca = st.text_input("🔍 Cerca nella descrizione o merchant", "")

cols_mostra = [col_data, col_importo, "nome_merchant", "categoria",col_desc, "confidenza", "fonte"]
cols_mostra = [c for c in cols_mostra if c in df.columns]

df_view = df[cols_mostra].copy()

# Ricerca con selezione colonna
sc1, sc2 = st.columns([3, 1])
with sc1:
    cerca = st.text_input("🔍 Cerca", "")
with sc2:
    colonna_cerca = st.selectbox("In quale colonna", ["Tutte"] + cols_mostra)

if cerca:
    if colonna_cerca == "Tutte":
        mask = df_view.apply(lambda row: row.astype(str).str.contains(cerca, case=False).any(), axis=1)
    else:
        mask = df_view[colonna_cerca].astype(str).str.contains(cerca, case=False)
    df_view = df_view[mask]

##### RICERCA IN TUTTLE LE COLONNE ES. bonifico viene trovato in tutte le colonne
#if cerca:
#    mask = df_view.apply(lambda row: row.astype(str).str.contains(cerca, case=False).any(), axis=1)
#    df_view = df_view[mask]

st.dataframe(
    df_view.sort_values(col_data, ascending=False) if col_data in df_view.columns else df_view,
    use_container_width=True,
    height=400
)

st.caption(f"{len(df_view)} movimenti mostrati")

# ─────────────────────────────────────────────
# EXPORT
# ─────────────────────────────────────────────

st.markdown("---")
col_exp1, col_exp2, _ = st.columns([1, 1, 3])

with col_exp1:
    csv_out = df[cols_mostra].to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "⬇️ Scarica CSV filtrato",
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
            "⬇️ Scarica Excel",
            data=buffer.getvalue(),
            file_name="movimenti_analisi.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except ImportError:
        st.caption("Installa openpyxl per l'export Excel: `pip install openpyxl`")
section_card_close()


html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }