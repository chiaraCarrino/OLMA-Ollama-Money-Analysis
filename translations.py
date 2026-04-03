"""
translations.py — Dizionario traduzioni IT/EN
"""

TRANSLATIONS = {
    "it": {
        # App generale
        "app_title": "Ollama Money Analysis",
        "app_subtitle": "Analizza le tue spese in pochi secondi",
        "lang_label": "🌐 Lingua",

        # Demo
        "demo_title": "🧪 Prova con un file di esempio",
        "demo_subtitle": "Non hai un CSV a portata di mano? Carica uno dei nostri file demo per esplorare tutte le funzionalità dell'app.",
        "demo_clean_label": "📋 File pulito",
        "demo_clean_desc": "5 colonne già pronte: data, importo, merchant, categoria, descrizione",
        "demo_dirty_label": "🧹 File sporco",
        "demo_dirty_desc": "Solo 3 colonne: data, importo e un'unica colonna descrizione grezza (richiede arricchimento)",
        "btn_demo_clean": "Carica file pulito →",
        "btn_demo_dirty": "Carica file sporco →",

        # Step home
        "step1": "Carica il file CSV",
        "step2": "Rilevamento colonne obbligatorie",
        "step3": "Conferma o correggi l'assegnazione delle colonne",
        "step4": "Avvia l'analisi",
        "step_enrich": "Arricchimento con Ollama",

        # Upload
        "upload_label": "Trascina qui il tuo file o clicca per sfogliare",
        "no_file": "Nessun file caricato. Usa il selettore qui sopra.",
        "file_loaded": "righe",
        "file_cols": "colonne",
        "file_sep": "separatore",
        "read_error": "Errore nella lettura",

        # Colonne
        "col_not_found": "non trovata",
        "all_found": "✅ Tutte le colonne obbligatorie rilevate automaticamente.",
        "missing_cols": "Mancanti",
        "missing_hint": "Esegui l'arricchimento o assegnale manualmente.",
        "not_assigned": "— non assegnata —",
        "assign_still": "Assegna ancora",
        "col_data": "Data",
        "col_importo": "Importo",
        "col_merchant": "Merchant",
        "col_categoria": "Categoria",
        "col_descrizione": "Descrizione",

        # Arricchimento
        "enrich_warn": "Le colonne <b>categoria</b> e/o <b>merchant</b> non sono presenti. Usa <code>Ollama</code> per classificarle, oppure assegnale manualmente al passo 3 se esistono già con un nome diverso.",
        "enrich_path": "Percorso `categorie_spese.json`",
        "enrich_ollama": "Usa Ollama come fallback (richiede server locale)",
        "btn_enrich": "▶ Esegui arricchimento",
        "btn_stop": "⏹ Interrompi",
        "enrich_stopping": "⏹ Interruzione richiesta…",
        "enrich_file_missing": "File non trovato",
        "enrich_done_msg": "Arricchimento già eseguito in questa sessione.",
        "enrich_stopped": "Interrotto a {idx}/{tot}. Le righe già classificate sono state salvate, le altre saranno \"Altro\".",
        "enrich_completed": "Completato: <b>{ok}/{tot}</b> descrizioni classificate.",
        "enrich_error": "Errore",

        # Avvia analisi
        "ready_warn": "⚠️ Assegna tutte le colonne obbligatorie prima di procedere.",
        "btn_start": "🚀 Avvia analisi →",

        # Sidebar analisi
        "sidebar_period": "Periodo",
        "sidebar_show": "Mostra",
        "sidebar_all": "Tutto",
        "sidebar_expenses": "Solo uscite",
        "sidebar_income": "Solo entrate",
        "sidebar_filtered": "movimenti filtrati",

        # Analisi — header
        "analysis_title": "💳 Analisi Movimenti",
        "no_file_warning": "⚠️ Nessun file caricato. Torna alla Home e carica un CSV.",

        # KPI
        "kpi_expenses": "Totale Uscite",
        "kpi_income": "Totale Entrate",
        "kpi_balance": "Saldo Netto",
        "kpi_avg": "Spesa Media",
        "kpi_categories": "Categorie",
        "kpi_transactions": "movimenti",
        "kpi_per_expense": "per uscita",
        "kpi_active": "attive nel periodo",
        "kpi_income_expense": "entrate − uscite",

        # Sezioni
        "sec_cat_title": "Spese per categoria",
        "sec_cat_desc": "Distribuzione delle uscite suddivise per categoria nel periodo selezionato.",
        "sec_time_title": "Andamento temporale — Entrate e Uscite",
        "sec_time_desc": "Confronto mensile, settimanale o giornaliero tra entrate e uscite. Clicca su una barra per il dettaglio.",
        "sec_cat_time_title": "Spese per categoria nel tempo",
        "sec_cat_time_desc": "Evoluzione della spesa per ciascuna categoria mese dopo mese.",
        "sec_merchant_title": "Top merchant per spesa",
        "sec_merchant_desc": "I negozi e servizi su cui hai speso di più nel periodo.",
        "sec_savings_title": "Risparmio effettivo",
        "sec_savings_desc": "Differenza tra entrate e uscite: quanto hai realmente messo da parte ogni mese.",
        "sec_detail_title": "Dettaglio movimenti",
        "sec_detail_desc": "Elenco completo delle transazioni con filtri per ricerca e categoria.",

        # Grafici
        "chart_expense_dist": "Distribuzione uscite",
        "chart_top_cat": "Top categorie per spesa",
        "chart_granularity": "Granularità",
        "chart_monthly": "Mensile",
        "chart_weekly": "Settimanale",
        "chart_daily": "Giornaliero",
        "chart_granularity_hint": "Se selezioni un mese specifico la granularità passa automaticamente a Giornaliero",
        "chart_year": "Anno",
        "chart_month": "Mese",
        "chart_all_months": "Tutti i mesi",
        "chart_expenses_label": "Uscite",
        "chart_income_label": "Entrate",
        "chart_top_merchant": "Top {n} merchant per spesa totale",
        "chart_n_merchant": "Numero di merchant",
        "chart_n_categories": "Numero di categorie da mostrare",
        "chart_heatmap_title": "Heatmap spese mensili — top {n} categorie",
        "chart_savings_title": "Risparmio effettivo mensile (entrate − uscite)",
        "chart_savings_year": "Risparmio per anno",
        "chart_heatmap_savings": "Heatmap risparmio (mese × anno)",
        "chart_avg_title": "Media mensile per anno — risparmio vs uscite",
        "chart_avg_savings": "Risparmio medio/mese",
        "chart_avg_expenses": "Uscite medie/mese",
        "chart_rolling": "Media mobile 3m",
        "chart_cumulative": "Cumulato",
        "chart_med_savings": "Med. risp.",
        "chart_med_expenses": "Med. usc.",

        # Mesi
        "months": {
            1: "Gennaio", 2: "Febbraio", 3: "Marzo", 4: "Aprile",
            5: "Maggio", 6: "Giugno", 7: "Luglio", 8: "Agosto",
            9: "Settembre", 10: "Ottobre", 11: "Novembre", 12: "Dicembre"
        },
        "months_short": ["Gen","Feb","Mar","Apr","Mag","Giu","Lug","Ago","Set","Ott","Nov","Dic"],

        # KPI risparmio
        "savings_total": "Risparmio totale",
        "savings_monthly_avg": "Media mensile",
        "savings_yearly_avg": "Media annuale",
        "savings_table_title": "#### Media mensile per anno",

        # Tabella risparmio
        "table_year": "Anno",
        "table_monthly_avg": "Media mensile di Risparmio (€)",
        "table_total": "Totale annuo (€)",
        "table_active_months": "Mesi registrati",

        # Dettaglio click grafico
        "detail_click_title": "🔍 Dettaglio spese —",
        "detail_no_data": "Nessuna transazione trovata per",
        "detail_expenses": "Uscite",
        "detail_income": "Entrate",
        "detail_balance": "Saldo",
        "detail_hint": "💡 Clicca su una barra del grafico per vedere le spese del periodo.",
        "col_date": "Data",
        "col_merchant_display": "Merchant",
        "col_category_display": "Categoria",
        "col_amount_display": "Importo (€)",
        "col_notes_display": "Note",

        # Tabella movimenti
        "search_label": "🔍 Cerca",
        "search_col": "In quale colonna",
        "search_all_cols": "Tutte",
        "movements_shown": "movimenti mostrati",

        # Export
        "export_csv": "⬇️ Scarica CSV filtrato",
        "export_excel": "⬇️ Scarica Excel",
        "export_openpyxl": "Installa openpyxl per l'export Excel: `pip install openpyxl`",
    },

    "en": {
        # App generale
        "app_title": "Bank Transactions",
        "app_subtitle": "Analyze your expenses in seconds",
        "lang_label": "🌐 Language",

        # Demo
        "demo_title": "🧪 Try with a sample file",
        "demo_subtitle": "Don't have a CSV handy? Load one of our demo files to explore all the app features.",
        "demo_clean_label": "📋 Clean file",
        "demo_clean_desc": "5 ready-to-use columns: date, amount, merchant, category, description",
        "demo_dirty_label": "🧹 Raw file",
        "demo_dirty_desc": "Only 3 columns: date, amount and a single raw description column (requires enrichment)",
        "btn_demo_clean": "Load clean file →",
        "btn_demo_dirty": "Load raw file →",

        # Step home
        "step1": "Upload CSV file",
        "step2": "Required columns detection",
        "step3": "Confirm or correct column mapping",
        "step4": "Start analysis",
        "step_enrich": "Enrichment with Ollama",

        # Upload
        "upload_label": "Drag your file here or click to browse",
        "no_file": "No file loaded. Use the selector above.",
        "file_loaded": "rows",
        "file_cols": "columns",
        "file_sep": "separator",
        "read_error": "Read error",

        # Colonne
        "col_not_found": "not found",
        "all_found": "✅ All required columns detected automatically.",
        "missing_cols": "Missing",
        "missing_hint": "Run enrichment or assign them manually.",
        "not_assigned": "— not assigned —",
        "assign_still": "Still to assign",
        "col_data": "Date",
        "col_importo": "Amount",
        "col_merchant": "Merchant",
        "col_categoria": "Category",
        "col_descrizione": "Description",

        # Arricchimento
        "enrich_warn": "Columns <b>category</b> and/or <b>merchant</b> are missing. Use <code>Ollama</code> to classify them, or assign them manually in step 3 if they already exist under a different name.",
        "enrich_path": "Path to `categorie_spese.json`",
        "enrich_ollama": "Use Ollama as fallback (requires local server)",
        "btn_enrich": "▶ Run enrichment",
        "btn_stop": "⏹ Stop",
        "enrich_stopping": "⏹ Stop requested…",
        "enrich_file_missing": "File not found",
        "enrich_done_msg": "Enrichment already completed in this session.",
        "enrich_stopped": "Stopped at {idx}/{tot}. Already classified rows were saved, others will be \"Other\".",
        "enrich_completed": "Completed: <b>{ok}/{tot}</b> descriptions classified.",
        "enrich_error": "Error",

        # Avvia analisi
        "ready_warn": "⚠️ Please assign all required columns before proceeding.",
        "btn_start": "🚀 Start analysis →",

        # Sidebar analisi
        "sidebar_period": "Period",
        "sidebar_show": "Show",
        "sidebar_all": "All",
        "sidebar_expenses": "Expenses only",
        "sidebar_income": "Income only",
        "sidebar_filtered": "transactions filtered",

        # Analisi — header
        "analysis_title": "💳 Transaction Analysis",
        "no_file_warning": "⚠️ No file loaded. Go back to Home and upload a CSV.",

        # KPI
        "kpi_expenses": "Total Expenses",
        "kpi_income": "Total Income",
        "kpi_balance": "Net Balance",
        "kpi_avg": "Avg Expense",
        "kpi_categories": "Categories",
        "kpi_transactions": "transactions",
        "kpi_per_expense": "per expense",
        "kpi_active": "active in period",
        "kpi_income_expense": "income − expenses",

        # Sezioni
        "sec_cat_title": "Spending by category",
        "sec_cat_desc": "Distribution of expenses by category in the selected period.",
        "sec_time_title": "Income & Expenses over time",
        "sec_time_desc": "Monthly, weekly or daily comparison of income and expenses. Click a bar for details.",
        "sec_cat_time_title": "Spending by category over time",
        "sec_cat_time_desc": "Evolution of spending per category month by month.",
        "sec_merchant_title": "Top merchants by spend",
        "sec_merchant_desc": "The shops and services where you spent the most.",
        "sec_savings_title": "Actual savings",
        "sec_savings_desc": "Difference between income and expenses: how much you actually saved each month.",
        "sec_detail_title": "Transaction detail",
        "sec_detail_desc": "Full list of transactions with search and category filters.",

        # Grafici
        "chart_expense_dist": "Expense distribution",
        "chart_top_cat": "Top categories by spend",
        "chart_granularity": "Granularity",
        "chart_monthly": "Monthly",
        "chart_weekly": "Weekly",
        "chart_daily": "Daily",
        "chart_granularity_hint": "Selecting a specific month will automatically switch to Daily granularity",
        "chart_year": "Year",
        "chart_month": "Month",
        "chart_all_months": "All months",
        "chart_expenses_label": "Expenses",
        "chart_income_label": "Income",
        "chart_top_merchant": "Top {n} merchants by total spend",
        "chart_n_merchant": "Number of merchants",
        "chart_n_categories": "Number of categories to show",
        "chart_heatmap_title": "Monthly spend heatmap — top {n} categories",
        "chart_savings_title": "Monthly savings (income − expenses)",
        "chart_savings_year": "Savings per year",
        "chart_heatmap_savings": "Savings heatmap (month × year)",
        "chart_avg_title": "Monthly average per year — savings vs expenses",
        "chart_avg_savings": "Avg savings/month",
        "chart_avg_expenses": "Avg expenses/month",
        "chart_rolling": "3m rolling avg",
        "chart_cumulative": "Cumulative",
        "chart_med_savings": "Avg sav.",
        "chart_med_expenses": "Avg exp.",

        # Mesi
        "months": {
            1: "January", 2: "February", 3: "March", 4: "April",
            5: "May", 6: "June", 7: "July", 8: "August",
            9: "September", 10: "October", 11: "November", 12: "December"
        },
        "months_short": ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"],

        # KPI risparmio
        "savings_total": "Total savings",
        "savings_monthly_avg": "Monthly average",
        "savings_yearly_avg": "Yearly average",
        "savings_table_title": "#### Monthly average per year",

        # Tabella risparmio
        "table_year": "Year",
        "table_monthly_avg": "Monthly Savings Average (€)",
        "table_total": "Annual Total (€)",
        "table_active_months": "Recorded months",

        # Dettaglio click grafico
        "detail_click_title": "🔍 Transaction detail —",
        "detail_no_data": "No transactions found for",
        "detail_expenses": "Expenses",
        "detail_income": "Income",
        "detail_balance": "Balance",
        "detail_hint": "💡 Click on a bar to see transactions for that period.",
        "col_date": "Date",
        "col_merchant_display": "Merchant",
        "col_category_display": "Category",
        "col_amount_display": "Amount (€)",
        "col_notes_display": "Notes",

        # Tabella movimenti
        "search_label": "🔍 Search",
        "search_col": "In which column",
        "search_all_cols": "All",
        "movements_shown": "transactions shown",

        # Export
        "export_csv": "⬇️ Download filtered CSV",
        "export_excel": "⬇️ Download Excel",
        "export_openpyxl": "Install openpyxl for Excel export: `pip install openpyxl`",
    }
}


def t(key: str, **kwargs) -> str:
    """
    Ritorna la stringa tradotta per la lingua corrente in session_state.
    Supporta interpolazione: t("enrich_stopped", idx=5, tot=100)
    """
    import streamlit as st
    lang = st.session_state.get("lang", "it")
    val = TRANSLATIONS.get(lang, TRANSLATIONS["it"]).get(key, key)
    if kwargs and isinstance(val, str):
        try:
            val = val.format(**kwargs)
        except (KeyError, ValueError):
            pass
    return val


def months_dict() -> dict:
    """Ritorna il dizionario dei mesi nella lingua corrente."""
    import streamlit as st
    lang = st.session_state.get("lang", "it")
    return TRANSLATIONS.get(lang, TRANSLATIONS["it"]).get("months", {})


def months_short_list() -> list:
    """Ritorna la lista dei mesi brevi nella lingua corrente."""
    import streamlit as st
    lang = st.session_state.get("lang", "it")
    return TRANSLATIONS.get(lang, TRANSLATIONS["it"]).get("months_short", [])
