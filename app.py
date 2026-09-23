import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Configurazione della pagina
st.set_page_config(page_title="Quant Finance Suite", layout="wide")

# --- FUNZIONE CARICAMENTO DATI ---
@st.cache_data
def carica_dati(tickers):
    df = yf.download(tickers, period="25y")['Close'].ffill().bfill()
    return df

st.title("⚡ Quant Finance Suite")
st.markdown("Piattaforma Integrata per l'Analisi e la Gestione Quantitativa del Portafoglio")

# --- STRUTTURA A SCHEDE (TABS) ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚡ Rotazione Momentum", 
    "⚖️ Ribilanciamento Portafoglio", 
    "📊 Rischio & Correlazione (In Sviluppo)", 
    "📈 Simulatore PAC (In Sviluppo)", 
    "🔍 Market Scanner (In Sviluppo)"
])

# ==============================================================================
# TAB 1: ROTAZIONE MOMENTUM
# ==============================================================================
with tab1:
    st.sidebar.header("⚙️ Configurazione Momentum")

    periodo_mesi = st.sidebar.slider(
        "Finestra temporale Momentum (Mesi):", 
        min_value=1, 
        max_value=300, 
        value=3,
        help="Seleziona la finestra temporale da 1 mese fino a 25 anni (300 mesi)"
    )
    lookback_giorni = periodo_mesi * 21  

    st.sidebar.subheader("Paniere Strumenti")
    preset_tickers = {
        "Azioni Globali (SWDA.MI)": "SWDA.MI",
        "Oro (GLD)": "GLD",
        "Bitcoin (BTC-USD)": "BTC-USD",
        "Obbligazioni Globali (AGGH.MI)": "AGGH.MI",
        "S&P 500 (CSSPX.MI)": "CSSPX.MI",
        "Tech / Nasdaq (EQQQ.MI)": "EQQQ.MI"
    }

    scelti = st.sidebar.multiselect(
        "Seleziona o rimuovi strumenti dal paniere:",
        options=list(preset_tickers.keys()),
        default=["Azioni Globali (SWDA.MI)", "Oro (GLD)", "Bitcoin (BTC-USD)", "Obbligazioni Globali (AGGH.MI)"]
    )

    custom_ticker = st.sidebar.text_input("Aggiungi Ticker personalizzato (es. NVDA, AAPL, XLU):", "")

    tickers_dict = {k: preset_tickers[k] for k in scelti}
    if custom_ticker.strip():
        tickers_dict[custom_ticker.upper()] = custom_ticker.upper()

    tickers_list = list(tickers_dict.values())

    if len(tickers_list) < 2:
        st.warning("Seleziona almeno 2 strumenti nella barra laterale per calcolare la rotazione.")
    else:
        dati = carica_dati(tickers_list)

        effettivi_giorni = min(lookback_giorni, len(dati) - 1)
        prezzo_oggi = dati.iloc[-1]
        prezzo_passato = dati.iloc[-effettivi_giorni]
        momentum = ((prezzo_oggi / prezzo_passato) - 1) * 100

        df_mom = pd.DataFrame({
            "Ticker": momentum.index,
            "Rendimento Momentum (%)": momentum.values
        }).sort_values(by="Rendimento Momentum (%)", ascending=False).reset_index(drop=True)

        inverso_dict = {v: k for k, v in tickers_dict.items()}
        df_mom["Asset"] = df_mom["Ticker"].map(lambda x: inverso_dict.get(x, x))

        vincitore = df_mom.iloc[0]

        col1, col2 = st.columns([1.2, 1.8])

        with col1:
            st.subheader("📌 Segnali Operativi Oggi")
            subcol1, subcol2 = st.columns(2)
            
            with subcol1:
                if vincitore["Rendimento Momentum (%)"] > 0:
                    st.success(
                        f"**🟢 COMPRA / TIENI**\n\n"
                        f"### {vincitore['Asset']}\n\n"
                        f"*(Momentum: +{vincitore['Rendimento Momentum (%)']:.2f}%)*"
                    )
                else:
                    st.info(
                        f"**🟢 COMPRA / TIENI**\n\n"
                        f"### 💵 Liquidità / Cash\n\n"
                        f"*(Protezione attiva)*"
                    )

            with subcol2:
                da_vendere = df_mom.iloc[1:] if vincitore["Rendimento Momentum (%)"] > 0 else df_mom
                elenco_vendi = "\n".join([f"• **{row['Asset']}** ({row['Rendimento Momentum (%)']:+.2f}%)" for _, row in da_vendere.iterrows()])
                st.error(
                    f"**🔴 VENDI / EVITA**\n\n"
                    f"{elenco_vendi}"
                )

            st.subheader(f"🏆 Classifica Forza Relativa ({periodo_mesi} Mesi)")
            st.dataframe(df_mom[["Asset", "Rendimento Momentum (%)"]].style.format({"Rendimento Momentum (%)": "{:+.2f}%"}), use_container_width=True)

        with col2:
            st.subheader("📈 Grafico Forza Relativa Normalizzata (Base 100)")
            dati_norm = (dati / dati.iloc[-effettivi_giorni]) * 100
            
            fig = go.Figure()
            for t in tickers_list:
                nome = inverso_dict.get(t, t)
                fig.add_trace(go.Scatter(
                    x=dati_norm.index[-effettivi_giorni:], 
                    y=dati_norm[t].iloc[-effettivi_giorni:], 
                    mode='lines', 
                    name=nome
                ))

            fig.update_layout(
                xaxis_title="Data", 
                yaxis_title="Rendimento Relativo (Base 100)", 
                height=480, 
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig, use_container_width=True)


# ==============================================================================
# TAB 2: RIBILANCIAMENTO PORTAFOGLIO
# ==============================================================================
with tab2:
    st.header("⚖️ Calcolatore Ribilanciamento Portafoglio")
    st.markdown("Inserisci il valore attuale del tuo portafoglio e i tuoi target ideali per calcolare le operazioni da eseguire.")

    # --- SEZIONE CARICAMENTO/SALVATAGGIO CSV ---
    col_csv1, col_csv2 = st.columns([1.5, 1])

    # Dati di default in caso di primo avvio senza file
    dati_iniziali = pd.DataFrame([
        {"Asset": "Azioni Globali (SWDA.MI)", "Valore Attuale (€)": 5000.0, "Target (%)": 40.0},
        {"Asset": "Obbligazioni Globali (AGGH.MI)", "Valore Attuale (€)": 3000.0, "Target (%)": 30.0},
        {"Asset": "Oro (GLD)", "Valore Attuale (€)": 1000.0, "Target (%)": 15.0},
        {"Asset": "Bitcoin (BTC-USD)", "Valore Attuale (€)": 1000.0, "Target (%)": 15.0},
    ])

    with col_csv1:
        uploaded_file = st.file_uploader("📂 Carica il tuo portafoglio salvato (.CSV)", type=["csv"])

    if uploaded_file is not None:
        try:
            dati_caricati = pd.read_csv(uploaded_file)
            colonne_richieste = {"Asset", "Valore Attuale (€)", "Target (%)"}
            if colonne_richieste.issubset(dati_caricati.columns):
                dati_iniziali = dati_caricati
                st.success("✅ Portafoglio caricato con successo!")
            else:
                st.error("⚠️ Il file CSV non contiene le colonne corrette: Asset, Valore Attuale (€), Target (%)")
        except Exception as e:
            st.error(f"⚠️ Errore nella lettura del file CSV: {e}")

    col_reb1, col_reb2 = st.columns([1.3, 1.7])

    with col_reb1:
        st.subheader("1. Modifica Valori e % Target")
        
        nuova_liquidita = st.number_input("Nuova Liquidità da aggiungere (€):", min_value=0.0, value=0.0, step=100.0)

        edited_df = st.data_editor(
            dati_iniziali,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "Valore Attuale (€)": st.column_config.NumberColumn(format="%.2f €"),
                "Target (%)": st.column_config.NumberColumn(format="%.1f %%", min_value=0.0, max_value=100.0)
            }
        )

        # Pulsante per scaricare i dati correnti in CSV
        csv_data = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Scarica/Salva Portafoglio in CSV",
            data=csv_data,
            file_name="mio_portafoglio.csv",
            mime="text/csv",
            help="Clicca qui per scaricare un file con la tua configurazione attuale. Potrai ricaricarlo la prossima volta!"
        )

        somma_target = edited_df["Target (%)"].sum()
        if abs(somma_target - 100.0) > 0.1:
            st.warning(f"⚠️ La somma delle % Target deve fare 100%. Attualmente è **{somma_target:.1f}%**.")

    with col_reb2:
        st.subheader("2. Piano di Ribilanciamento")

        valore_portafoglio_attuale = edited_df["Valore Attuale (€)"].sum()
        valore_portafoglio_totale = valore_portafoglio_attuale + nuova_liquidita

        st.metric(
            label="Valore Portafoglio Totale (con nuova liquidità)", 
            value=f"{valore_portafoglio_totale:,.2f} €",
            delta=f"+{nuova_liquidita:,.2f} € liquidità" if nuova_liquidita > 0 else None
        )

        df_calc = edited_df.copy()
        df_calc["Target (€)"] = (df_calc["Target (%)"] / 100.0) * valore_portafoglio_totale
        df_calc["Aggiustamento (€)"] = df_calc["Target (€)"] - df_calc["Valore Attuale (€)"]
        df_calc["Attuale (%)"] = (df_calc["Valore Attuale (€)"] / valore_portafoglio_attuale * 100.0) if valore_portafoglio_attuale > 0 else 0.0

        def definisci_azione(val):
            if val > 1.0:
                return f"🟢 COMPRA {val:,.2f} €"
            elif val < -1.0:
                return f"🔴 VENDI {abs(val):,.2f} €"
            else:
                return "⚪ MANTIENI"

        df_calc["Azione Consigliata"] = df_calc["Aggiustamento (€)"].apply(definisci_azione)

        st.dataframe(
            df_calc[["Asset", "Valore Attuale (€)", "Attuale (%)", "Target (%)", "Target (€)", "Azione Consigliata"]],
            use_container_width=True,
            column_config={
                "Valore Attuale (€)": st.column_config.NumberColumn(format="%.2f €"),
                "Attuale (%)": st.column_config.NumberColumn(format="%.1f %%"),
                "Target (%)": st.column_config.NumberColumn(format="%.1f %%"),
                "Target (€)": st.column_config.NumberColumn(format="%.2f €"),
            }
        )

        fig_reb = go.Figure()
        fig_reb.add_trace(go.Bar(x=df_calc["Asset"], y=df_calc["Attuale (%)"], name="Attuale (%)", marker_color="royalblue"))
        fig_reb.add_trace(go.Bar(x=df_calc["Asset"], y=df_calc["Target (%)"], name="Target (%)", marker_color="mediumseagreen"))
        fig_reb.update_layout(barmode='group', title="Confronto Allocazione: Attuale vs Target (%)", height=320, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_reb, use_container_width=True)


# ==============================================================================
# TAB 3, 4, 5: PLACEHOLDER PER PROGETTI FUTURI
# ==============================================================================
with tab3:
    st.header("📊 Matrice di Correlazione e Analisi del Rischio")
    st.info("Questa funzionalità verrà sviluppata nello Step successivo!")

with tab4:
    st.header("📈 Simulatore PAC & Monte Carlo")
    st.info("Questa funzionalità verrà sviluppata nello Step successivo!")

with tab5:
    st.header("🔍 Market Scanner")
    st.info("Questa funzionalità verrà sviluppata nello Step successivo!")
