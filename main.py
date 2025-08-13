import streamlit as st
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import time
import warnings
warnings.filterwarnings('ignore')

# Configurazione pagina
st.set_page_config(
    page_title="Portfolio Tracker - Alpha Vantage",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titolo principale
st.title("📈 Portfolio Tracker & Analyzer")
st.markdown("*Powered by Alpha Vantage API*")
st.markdown("---")

# Sidebar per configurazione
st.sidebar.header("⚙️ Configurazione API")

# Input per API Key
api_key = st.sidebar.text_input(
    "Alpha Vantage API Key:",
    type="password",
    help="Ottieni gratuitamente su: https://www.alphavantage.co/support/#api-key"
)

if not api_key:
    st.warning("⚠️ **API Key richiesta!**")
    st.info("""
    **Come ottenere l'API Key gratuita:**
    
    1. Vai su: https://www.alphavantage.co/support/#api-key
    2. Inserisci la tua email
    3. Riceverai l'API key via email
    4. Incolla la chiave nella sidebar ←
    
    **Limiti gratuiti:** 25 richieste/giorno, 5 richieste/minuto
    """)
    st.stop()

# Dizionario degli indici e azioni principali
SIMBOLI_PRINCIPALI = {
    # Azioni USA Principali
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "Google": "GOOGL",
    "Amazon": "AMZN",
    "Tesla": "TSLA",
    "Meta": "META",
    "NVIDIA": "NVDA",
    "Netflix": "NFLX",
    "Berkshire Hathaway": "BRK.A",
    "JPMorgan": "JPM",
    
    # ETF Indici USA
    "S&P 500 ETF": "SPY",
    "NASDAQ 100 ETF": "QQQ",
    "Dow Jones ETF": "DIA",
    "Russell 2000 ETF": "IWM",
    
    # ETF Settoriali
    "Technology ETF": "XLK",
    "Financial ETF": "XLF",
    "Healthcare ETF": "XLV",
    "Energy ETF": "XLE",
    "Consumer ETF": "XLY",
    
    # ETF Internazionali
    "Europe ETF": "VGK",
    "Emerging Markets": "EEM",
    "Japan ETF": "EWJ",
    "China ETF": "FXI",
    
    # ETF Obbligazionari
    "Treasury 20+ Year": "TLT",
    "Aggregate Bond": "AGG",
    "High Yield Bond": "HYG",
    "Investment Grade": "LQD",
    
    # Materie Prime
    "Gold ETF": "GLD",
    "Silver ETF": "SLV",
    "Oil ETF": "USO",
    "VIX ETF": "VXX"
}

class AlphaVantageAPI:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.last_request_time = 0
        self.min_interval = 12  # 12 secondi tra richieste per rispettare il limite
        
    def wait_if_needed(self):
        """Aspetta se necessario per rispettare i rate limits"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            wait_time = self.min_interval - elapsed
            time.sleep(wait_time)
    
    def get_daily_data(self, symbol, outputsize="compact"):
        """Scarica dati giornalieri per un simbolo"""
        self.wait_if_needed()
        
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": outputsize,  # compact = 100 giorni, full = 20+ anni
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                
                # Controlla errori API
                if "Error Message" in data:
                    return None, f"Errore API: {data['Error Message']}"
                elif "Note" in data:
                    return None, f"Rate limit: {data['Note']}"
                elif "Time Series (Daily)" not in data:
                    return None, "Formato dati non valido"
                
                # Converte in DataFrame
                time_series = data["Time Series (Daily)"]
                df = pd.DataFrame.from_dict(time_series, orient='index')
                
                # Rinomina colonne
                df.columns = ['Open', 'High', 'Low', 'Close', 'Adj_Close', 'Volume', 'Dividend', 'Split']
                
                # Converte a numerico e ordina per data
                for col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                df.index = pd.to_datetime(df.index)
                df = df.sort_index()
                
                return df, None
            else:
                return None, f"HTTP Error: {response.status_code}"
                
        except Exception as e:
            return None, f"Errore connessione: {str(e)}"
    
    def test_connection(self):
        """Testa la connessione API"""
        try:
            params = {
                "function": "TIME_SERIES_INTRADAY",
                "symbol": "AAPL",
                "interval": "5min",
                "apikey": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "Error Message" in data:
                    return False, data["Error Message"]
                elif "Note" in data:
                    return False, "Rate limit raggiunto"
                else:
                    return True, "Connessione OK"
            else:
                return False, f"HTTP {response.status_code}"
                
        except Exception as e:
            return False, str(e)

def calcola_performance(prezzi, giorni_indietro=None):
    """Calcola performance percentuale"""
    if len(prezzi) < 2:
        return np.nan
    
    prezzo_finale = prezzi.iloc[-1]
    
    if giorni_indietro is None:
        prezzo_iniziale = prezzi.iloc[0]
    else:
        if len(prezzi) > giorni_indietro:
            prezzo_iniziale = prezzi.iloc[-(giorni_indietro + 1)]
        else:
            prezzo_iniziale = prezzi.iloc[0]
    
    if prezzo_iniziale == 0 or pd.isna(prezzo_iniziale) or pd.isna(prezzo_finale):
        return np.nan
        
    return ((prezzo_finale - prezzo_iniziale) / prezzo_iniziale) * 100

def calcola_volatilita(prezzi, giorni=30):
    """Calcola volatilità annualizzata"""
    if len(prezzi) < giorni:
        return np.nan
    
    returns = prezzi.pct_change().dropna()
    if len(returns) < 2:
        return np.nan
    
    volatilita_annua = returns.std() * np.sqrt(252) * 100  # 252 giorni di trading
    return volatilita_annua

# Inizializza API
api = AlphaVantageAPI(api_key)

# Test connessione
if st.sidebar.button("🔧 Test API"):
    with st.sidebar.container():
        with st.spinner("Testing..."):
            success, message = api.test_connection()
            if success:
                st.sidebar.success(f"✅ {message}")
            else:
                st.sidebar.error(f"❌ {message}")

# Selezione simboli
st.header("📊 Analisi Performance")

# Filtri per categoria
col1, col2, col3, col4 = st.columns(4)

with col1:
    mostra_azioni = st.checkbox("Solo Azioni", value=False)
with col2:
    mostra_etf = st.checkbox("Solo ETF", value=False)
with col3:
    mostra_obbligazioni = st.checkbox("Solo Obbligazioni", value=False)
with col4:
    mostra_materie_prime = st.checkbox("Solo Materie Prime", value=False)

# Applica filtri
simboli_filtrati = list(SIMBOLI_PRINCIPALI.keys())

if mostra_azioni:
    simboli_filtrati = [k for k in simboli_filtrati 
                       if k in ["Apple", "Microsoft", "Google", "Amazon", "Tesla", "Meta", "NVIDIA", "Netflix", "Berkshire Hathaway", "JPMorgan"]]

if mostra_etf:
    simboli_filtrati = [k for k in simboli_filtrati 
                       if "ETF" in k]

if mostra_obbligazioni:
    simboli_filtrati = [k for k in simboli_filtrati 
                       if any(x in k for x in ["Treasury", "Bond", "AGG", "TLT", "HYG", "LQD"])]

if mostra_materie_prime:
    simboli_filtrati = [k for k in simboli_filtrati 
                       if any(x in k for x in ["Gold", "Silver", "Oil", "VIX"])]

# Selezione finale
simboli_selezionati = st.multiselect(
    "Seleziona simboli da analizzare:",
    simboli_filtrati,
    default=simboli_filtrati[:5] if len(simboli_filtrati) >= 5 else simboli_filtrati,
    help="⚠️ Limite API: massimo 25 simboli al giorno"
)

# Opzioni analisi
col_period1, col_period2 = st.columns(2)
with col_period1:
    periodo_analisi = st.selectbox(
        "Periodo dati:",
        ["compact", "full"],
        index=0,
        help="Compact = 100 giorni, Full = 20+ anni"
    )

with col_period2:
    mostra_volatilita = st.checkbox("Calcola Volatilità", value=True)

if simboli_selezionati and st.button("📈 Analizza Performance"):
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    risultati = []
    errori = []
    
    for i, nome_simbolo in enumerate(simboli_selezionati):
        simbolo = SIMBOLI_PRINCIPALI[nome_simbolo]
        status_text.text(f"Elaborazione: {nome_simbolo} ({simbolo}) - {i+1}/{len(simboli_selezionati)}")
        
        # Scarica dati
        data, error = api.get_daily_data(simbolo, periodo_analisi)
        
        if error:
            errori.append(f"{nome_simbolo}: {error}")
            risultati.append({
                "Simbolo": nome_simbolo,
                "Ticker": simbolo,
                "Status": "ERROR",
                "Prezzo Attuale": "N/A",
                "Perf 1M": "N/A",
                "Perf 3M": "N/A",
                "Perf 6M": "N/A",
                "Perf 1A": "N/A",
                "Volatilità": "N/A"
            })
        else:
            try:
                prezzi = data['Adj_Close'].dropna()
                
                if len(prezzi) == 0:
                    errori.append(f"{nome_simbolo}: Nessun prezzo valido")
                    continue
                
                prezzo_attuale = prezzi.iloc[-1]
                
                # Calcola performance per diversi periodi
                perf_1m = calcola_performance(prezzi, 21)   # ~1 mese
                perf_3m = calcola_performance(prezzi, 63)   # ~3 mesi
                perf_6m = calcola_performance(prezzi, 126)  # ~6 mesi
                perf_1a = calcola_performance(prezzi, 252)  # ~1 anno
                
                # Calcola volatilità
                volatilita = calcola_volatilita(prezzi) if mostra_volatilita else np.nan
                
                risultati.append({
                    "Simbolo": nome_simbolo,
                    "Ticker": simbolo,
                    "Status": "SUCCESS",
                    "Prezzo Attuale": f"${prezzo_attuale:.2f}",
                    "Perf 1M": f"{perf_1m:.2f}%" if not pd.isna(perf_1m) else "N/A",
                    "Perf 3M": f"{perf_3m:.2f}%" if not pd.isna(perf_3m) else "N/A",
                    "Perf 6M": f"{perf_6m:.2f}%" if not pd.isna(perf_6m) else "N/A",
                    "Perf 1A": f"{perf_1a:.2f}%" if not pd.isna(perf_1a) else "N/A",
                    "Volatilità": f"{volatilita:.1f}%" if not pd.isna(volatilita) else "N/A"
                })
                
            except Exception as e:
                errori.append(f"{nome_simbolo}: Errore calcolo - {str(e)}")
        
        progress_bar.progress((i + 1) / len(simboli_selezionati))
        
        # Pausa tra richieste per rispettare rate limits
        if i < len(simboli_selezionati) - 1:  # Non aspettare dopo l'ultima richiesta
            time.sleep(1)
    
    # Pulisci progress bar
    progress_bar.empty()
    status_text.empty()
    
    # Mostra risultati
    if risultati:
        st.subheader("📈 Risultati Analisi")
        
        df_risultati = pd.DataFrame(risultati)
        
        # Rimuovi colonna Status per visualizzazione se tutti sono SUCCESS
        df_display = df_risultati.copy()
        if all(r["Status"] == "SUCCESS" for r in risultati):
            df_display = df_display.drop("Status", axis=1)
        
        st.dataframe(df_display, use_container_width=True)
        
        # Statistiche
        col1, col2, col3 = st.columns(3)
        
        successi = len([r for r in risultati if r["Status"] == "SUCCESS"])
        
        with col1:
            st.metric("Simboli Analizzati", f"{successi}/{len(simboli_selezionati)}")
        
        with col2:
            # Conta performance positive 1 anno
            perf_positive = 0
            for r in risultati:
                if r["Status"] == "SUCCESS" and r["Perf 1A"] != "N/A":
                    try:
                        perf_val = float(r["Perf 1A"].replace("%", ""))
                        if perf_val > 0:
                            perf_positive += 1
                    except:
                        pass
            st.metric("Performance 1A Positive", f"{perf_positive}/{successi}")
        
        with col3:
            st.metric("Timestamp", datetime.now().strftime("%H:%M:%S"))
        
        # Download CSV
        if st.button("📥 Scarica CSV"):
            csv = df_display.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"portfolio_analysis_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )
    
    # Mostra errori se presenti
    if errori:
        st.subheader("⚠️ Errori")
        for errore in errori:
            st.error(errore)
        
        st.info("💡 **Suggerimenti per risolvere errori:**")
        st.write("""
        - **Rate limit**: Aspetta qualche minuto e riprova con meno simboli
        - **Simbolo non valido**: Verifica che il ticker esista
        - **API Key**: Controlla che sia valida e non scaduta
        - **Connessione**: Verifica la connessione internet
        """)

# Informazioni API
st.sidebar.subheader("📊 Info API")
st.sidebar.write("**Rate Limits:**")
st.sidebar.write("• 25 richieste/giorno (gratuito)")
st.sidebar.write("• 5 richieste/minuto")
st.sidebar.write("• Pausa automatica tra richieste")

st.sidebar.write("**Upgrade Premium:**")
st.sidebar.write("• 1200+ richieste/minuto")
st.sidebar.write("• Dati real-time")
st.sidebar.write("• Più funzioni")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        📈 Portfolio Tracker v3.0 | Powered by Alpha Vantage API<br>
        <a href="https://www.alphavantage.co" target="_blank">Alpha Vantage</a> | 
        <a href="https://www.alphavantage.co/support/#api-key" target="_blank">Get Free API Key</a>
    </div>
    """, 
    unsafe_allow_html=True
)
