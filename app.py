import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# Configurazione della pagina
st.set_page_config(page_title="Quant Momentum App", layout="wide")
st.title("⚡ Quant Rotation Dashboard")
st.markdown("Analisi di Forza Relativa e Rotazione Quantitativa del Capitale")

# --- SIDEBAR: PARAMETRI PERSONALIZZABILI ---
st.sidebar.header("⚙️ Configurazione Strategia")

periodo_mesi = st.sidebar.slider("Finestra temporale Momentum (Mesi):", min_value=1, max_value=12, value=3)
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
    st.warning("Seleziona almeno 2 strumenti per calcolare la rotazione.")
    st.stop()

# --- SCARICAMENTO DATI ---
@st.cache_data
def carica_dati(tickers):
    df = yf.download(tickers, period="3y")['Close'].ffill().bfill()
    return df

dati = carica_dati(tickers_list)

# --- CALCOLO MOMENTUM E SEGNALE ATTUALE ---
prezzo_oggi = dati.iloc[-1]
prezzo_passato = dati.iloc[-min(lookback_giorni, len(dati)-1)]
momentum = ((prezzo_oggi / prezzo_passato) - 1) * 100

df_mom = pd.DataFrame({
    "Ticker": momentum.index,
    "Rendimento Momentum (%)": momentum.values
}).sort_values(by="Rendimento Momentum (%)", ascending=False).reset_index(drop=True)

inverso_dict = {v: k for k, v in tickers_dict.items()}
df_mom["Asset"] = df_mom["Ticker"].map(lambda x: inverso_dict.get(x, x))

vincitore = df_mom.iloc[0]

# --- DISPLAY SEGNALE ---
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("📌 Segnale Operativo Oggi")
    if vincitore["Rendimento Momentum (%)"] > 0:
        st.success(f"**COMPRA / TIENI:**\n### {vincitore['Asset']}\n(Momentum a {periodo_mesi}M: +{vincitore['Rendimento Momentum (%)']:.2f}%)")
    else:
        st.error("**SEGNALE DI PROTEZIONE:**\nTutti gli asset sono in territorio negativo. **Stai in Liquidità / Cash**.")

    st.subheader(f"🏆 Classifica Forza Relativa ({periodo_mesi} Mesi)")
    st.dataframe(df_mom[["Asset", "Rendimento Momentum (%)"]].style.format({"Rendimento Momentum (%)": "{:+.2f}%"}), use_container_width=True)

# --- GRAFICO INTERATTIVO ---
with col2:
    st.subheader("📈 Grafico Forza Relativa Normalizzata (Base 100)")
    dati_norm = (dati / dati.iloc[-lookback_giorni]) * 100
    
    fig = go.Figure()
    for t in tickers_list:
        nome = inverso_dict.get(t, t)
        fig.add_trace(go.Scatter(x=dati_norm.index[-lookback_giorni:], y=dati_norm[t].iloc[-lookback_giorni:], mode='lines', name=nome))

    fig.update_layout(xaxis_title="Data", yaxis_title="Rendimento Relativo (Base 100)", height=450, margin=dict(l=20, r=20, t=30, b=20))
    st.plotly_chart(fig, use_container_width=True)
