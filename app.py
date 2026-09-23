import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

# Configurazione della pagina
st.set_page_config(page_title="Quant Finance Suite", layout="wide")

# --- FUNZIONE CARICAMENTO DATI ---
@st.cache_data
def carica_dati(tickers):
    df = yf.download(tickers, period="25y")['Close'].ffill().bfill()
    return df

# --- PANIERE STRUMENTI PREDEFINITI (CONDIVISO) ---
preset_tickers = {
    "Azioni Globali (SWDA.MI)": "SWDA.MI",
    "Oro (GLD)": "GLD",
    "Bitcoin (BTC-USD)": "BTC-USD",
    "Obbligazioni Globali (AGGH.MI)": "AGGH.MI",
    "S&P 500 (CSSPX.MI)": "CSSPX.MI",
    "Tech / Nasdaq (EQQQ.MI)": "EQQQ.MI"
}

st.title("⚡ Quant Finance Suite")
st.markdown("Piattaforma Integrata per l'Analisi e la Gestione Quantitativa del Portafoglio")

# --- STRUTTURA A SCHEDE (TABS) ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "⚡ Rotazione Momentum", 
    "⚖️ Ribilanciamento Portafoglio", 
    "📊 Rischio & Correlazione", 
    "📈 Simulatore PAC & Backtest", 
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

    st.sidebar.subheader("Paniere Strumenti Momentum")
    scelti = st.sidebar.multiselect(
        "Seleziona o rimuovi strumenti dal paniere:",
        options=list(preset_tickers.keys()),
        default=["Azioni Globali (SWDA.MI)", "Oro (GLD)", "Bitcoin (BTC-USD)", "Obbligazioni Globali (AGGH.MI)"]
    )

    custom_ticker = st.sidebar.text_input("Aggiungi Ticker personalizzato (es. NVDA, AAPL, XLU):", "")

    tickers_dict = {k: preset_tickers[k] for k in scelti if k in preset_tickers}
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

    col_csv1, col_csv2 = st.columns([1.5, 1])

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

        csv_data = edited_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Scarica/Salva Portafoglio in CSV",
            data=csv_data,
            file_name="mio_portafoglio.csv",
            mime="text/csv",
            help="Scarica un file CSV con la tua configurazione per ricaricarlo la prossima volta."
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
# TAB 3: RISCHIO & CORRELAZIONE
# ==============================================================================
with tab3:
    st.header("📊 Analisi Rischio & Matrice di Correlazione")
    st.markdown("Valuta la diversificazione del portafoglio, la volatilità storica e le metriche di rischio degli strumenti.")

    st.sidebar.subheader("⚙️ Configurazione Rischio")
    anni_rischio = st.sidebar.slider("Periodo Storico Analisi (Anni):", min_value=1, max_value=20, value=5)
    rf_rate = st.sidebar.number_input("Tasso Risk-Free Annuo / BTP (%)", min_value=0.0, max_value=10.0, value=2.5, step=0.1) / 100.0

    scelti_risk = st.sidebar.multiselect(
        "Strumenti da analizzare:",
        options=list(preset_tickers.keys()),
        default=["Azioni Globali (SWDA.MI)", "Oro (GLD)", "Bitcoin (BTC-USD)", "Obbligazioni Globali (AGGH.MI)", "Tech / Nasdaq (EQQQ.MI)"],
        key="risk_multiselect"
    )

    tickers_risk_dict = {k: preset_tickers[k] for k in scelti_risk if k in preset_tickers}
    tickers_risk_list = list(tickers_risk_dict.values())

    if len(tickers_risk_list) < 2:
        st.warning("Seleziona almeno 2 strumenti nella barra laterale per calcolare correlazione e rischio.")
    else:
        dati_risk_full = carica_dati(tickers_risk_list)
        giorni_filtro = anni_rischio * 252
        dati_risk = dati_risk_full.iloc[-giorni_filtro:]

        rendimenti = dati_risk.pct_change().dropna()

        inv_map_risk = {v: k for k, v in tickers_risk_dict.items()}
        rendimenti.columns = [inv_map_risk.get(col, col) for col in rendimenti.columns]
        dati_risk.columns = [inv_map_risk.get(col, col) for col in dati_risk.columns]

        matrice_corr = rendimenti.corr()

        col_risk1, col_risk2 = st.columns([1.3, 1.7])

        with col_risk1:
            st.subheader("🔥 Matrice di Correlazione")
            
            fig_corr = go.Figure(data=go.Heatmap(
                z=matrice_corr.values,
                x=matrice_corr.columns,
                y=matrice_corr.index,
                colorscale="RdBu",
                zmin=-1, zmax=1,
                text=np.round(matrice_corr.values, 2),
                texttemplate="%{text}",
                textfont={"size": 11}
            ))
            fig_corr.update_layout(height=420, margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig_corr, use_container_width=True)

        with col_risk2:
            st.subheader("📈 Metriche di Rischio e Rendimento")

            num_giorni_tot = (dati_risk.index[-1] - dati_risk.index[0]).days
            cagr = ((dati_risk.iloc[-1] / dati_risk.iloc[0]) ** (365.25 / num_giorni_tot)) - 1
            volatilità = rendimenti.std() * np.sqrt(252)
            sharpe = (cagr - rf_rate) / volatilità

            cum_returns = (1 + rendimenti).cumprod()
            peak = cum_returns.cummax()
            drawdown = (cum_returns - peak) / peak
            max_dd = drawdown.min()

            df_metrics = pd.DataFrame({
                "CAGR (% Anno)": cagr * 100,
                "Volatilità (% Anno)": volatilità * 100,
                "Sharpe Ratio": sharpe,
                "Max Drawdown (%)": max_dd * 100
            }).sort_values(by="Sharpe Ratio", ascending=False)

            st.dataframe(
                df_metrics.style.format({
                    "CAGR (% Anno)": "{:+.2f}%",
                    "Volatilità (% Anno)": "{:.2f}%",
                    "Sharpe Ratio": "{:.2f}",
                    "Max Drawdown (%)": "{:+.2f}%"
                }),
                use_container_width=True
            )

            st.info(
                "💡 **Guida Rapida all'Interpretazione:**\n"
                "- **Correlazione (< 0.3):** Valori bassi indicano buona diversificazione.\n"
                "- **Sharpe Ratio (> 1.0):** Valore eccellente; la remunerazione del rischio è elevata.\n"
                "- **Max Drawdown:** Indica la massima perdita teorica sofferta dal punto più alto."
            )


# ==============================================================================
# TAB 4: SIMULATORE PAC & BACKTEST
# ==============================================================================
with tab4:
    st.header("📈 Simulatore PAC & Backtest Storico")
    st.markdown("Simula la crescita storica di un Piano di Accumulo (PAC) con quota iniziale e versamenti mensili sui tuoi strumenti.")

    st.sidebar.subheader("⚙️ Configurazione PAC")
    capitale_iniziale = st.sidebar.number_input("Capitale Iniziale (€):", min_value=0.0, value=2000.0, step=500.0)
    quota_mensile = st.sidebar.number_input("Versamento Mensile (€):", min_value=0.0, value=200.0, step=50.0)
    anni_pac = st.sidebar.slider("Durata PAC (Anni):", min_value=1, max_value=20, value=5)

    asset_pac_scelto = st.sidebar.selectbox(
        "Strumento per il PAC:",
        options=list(preset_tickers.keys()),
        index=0
    )

    ticker_pac = preset_tickers[asset_pac_scelto]
    dati_pac_full = carica_dati([ticker_pac])

    giorni_pac = anni_pac * 252
    dati_pac = dati_pac_full.iloc[-giorni_pac:][ticker_pac].dropna()

    if len(dati_pac) < 30:
        st.error("Dati storici insufficienti per il periodo selezionato.")
    else:
        df_pac = pd.DataFrame({'Prezzo': dati_pac})
        df_pac['Mese'] = df_pac.index.to_period('M')

        # Primo giorno lavorativo di ciascun mese per piazzare il versamento
        primi_giorni_mese = df_pac.groupby('Mese').head(1).index

        quote_possedute = 0.0
        capitale_versato = 0.0
        
        quote_series = []
        capitale_series = []

        for date, price in dati_pac.items():
            if date == dati_pac.index[0]:
                if capitale_iniziale > 0:
                    quote_possedute += capitale_iniziale / price
                    capitale_versato += capitale_iniziale
            elif date in primi_giorni_mese and quota_mensile > 0:
                quote_possedute += quota_mensile / price
                capitale_versato += quota_mensile

            quote_series.append(quote_possedute)
            capitale_series.append(capitale_versato)

        df_sim = pd.DataFrame({
            'Prezzo': dati_pac.values,
            'Quote': quote_series,
            'Capitale Investito': capitale_series
        }, index=dati_pac.index)

        df_sim['Valore Portafoglio'] = df_sim['Prezzo'] * df_sim['Quote']
        df_sim['Profitto (€)'] = df_sim['Valore Portafoglio'] - df_sim['Capitale Investito']

        cap_totale = df_sim['Capitale Investito'].iloc[-1]
        valore_finale = df_sim['Valore Portafoglio'].iloc[-1]
        profitto_totale = valore_finale - cap_totale
        rendimento_perc = (profitto_totale / cap_totale * 100) if cap_totale > 0 else 0.0

        num_anni_effettivi = (df_sim.index[-1] - df_sim.index[0]).days / 365.25
        cagr_pac = (((valore_finale / cap_totale) ** (1 / num_anni_effettivi)) - 1) * 100 if cap_totale > 0 else 0.0

        # Schede Metriche
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Capitale Investito Totale", f"{cap_totale:,.2f} €")
        col_m2.metric("Valore Finale Accumulato", f"{valore_finale:,.2f} €")
        col_m3.metric("Profitto Netto (€)", f"{profitto_totale:+,.2f} €", delta=f"{rendimento_perc:+.2f}%")
        col_m4.metric("CAGR Effettivo Indicativo", f"{cagr_pac:.2f}%")

        # Grafico Crescita PAC
        fig_pac = go.Figure()
        fig_pac.add_trace(go.Scatter(
            x=df_sim.index, 
            y=df_sim['Valore Portafoglio'], 
            mode='lines', 
            name='Valore Portafoglio (€)', 
            line=dict(color='mediumseagreen', width=2.5)
        ))
        fig_pac.add_trace(go.Scatter(
            x=df_sim.index, 
            y=df_sim['Capitale Investito'], 
            mode='lines', 
            name='Capitale Investito (€)', 
            line=dict(color='gray', dash='dash', width=2)
        ))

        fig_pac.update_layout(
            title=f"Evoluzione del PAC su {asset_pac_scelto} ({anni_pac} Anni Storici)",
            xaxis_title="Data",
            yaxis_title="Valore (€)",
            height=480,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        st.plotly_chart(fig_pac, use_container_width=True)


# ==============================================================================
# TAB 5: PLACEHOLDER PER MARKET SCANNER
# ==============================================================================
with tab5:
    st.header("🔍 Market Scanner")
    st.info("Questa funzionalità verrà sviluppata nello Step successivo!")
