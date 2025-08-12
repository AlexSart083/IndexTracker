import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configurazione pagina
st.set_page_config(
    page_title="Portfolio Tracker & Analyzer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titolo principale
st.title("📈 Portfolio Tracker & Analyzer")
st.markdown("---")

# Sidebar per configurazione
st.sidebar.header("⚙️ Configurazione")

# Dizionario degli indici principali - CORRETTI
INDICI_PRINCIPALI = {
    # Indici Azionari USA
    "S&P 500": "^GSPC",
    "NASDAQ": "^IXIC", 
    "Dow Jones": "^DJI",
    "Russell 2000": "^RUT",
    
    # Indici Azionari Europa
    "FTSE MIB": "FTSEMIB.MI",
    "DAX": "^GDAXI",
    "CAC 40": "^FCHI",
    "FTSE 100": "^FTSE",
    "Euro Stoxx 50": "^SX5E",
    
    # Indici Azionari Asia-Pacifico
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    
    # ETF Obbligazionari (più affidabili)
    "TLT (20+ Year Treasury)": "TLT",
    "AGG (Total Bond Market)": "AGG",
    "LQD (Investment Grade)": "LQD",
    "HYG (High Yield)": "HYG",
    
    # Materie Prime e Valute
    "VIX (Volatilità)": "^VIX",
    "Gold ETF": "GLD",
    "Oil ETF": "USO",
    "EUR/USD": "EURUSD=X"
}

@st.cache_data(ttl=300)  # Cache per 5 minuti
def download_data_safe(ticker, period="1y", max_retries=2):
    """Download dati con retry e gestione errori migliorata"""
    for attempt in range(max_retries):
        try:
            # Prova prima con yfinance standard
            data = yf.download(ticker, period=period, progress=False, 
                             prepost=False, auto_adjust=True, 
                             keepna=False, threads=True)
            
            if not data.empty and len(data) > 1:
                # Verifica che abbiamo dati significativi
                if 'Close' in data.columns:
                    close_data = data['Close'].dropna()
                    if len(close_data) > 1:
                        return data
                elif len(data.columns) == 1:  # Caso di serie singola
                    clean_data = data.dropna()
                    if len(clean_data) > 1:
                        return clean_data
            
            # Se fallisce, prova con un approccio alternativo
            if attempt == 0:
                ticker_obj = yf.Ticker(ticker)
                hist_data = ticker_obj.history(period=period)
                if not hist_data.empty and len(hist_data) > 1:
                    return hist_data
                    
        except Exception as e:
            st.warning(f"Tentativo {attempt + 1} fallito per {ticker}: {str(e)}")
            if attempt < max_retries - 1:
                continue
    
    return pd.DataFrame()

def calcola_performance_safe(data, giorni_indietro=None):
    """Calcola performance in modo più sicuro"""
    try:
        if data.empty:
            return np.nan
            
        # Determina la colonna prezzo
        if 'Close' in data.columns:
            prices = data['Close'].dropna()
        elif 'Adj Close' in data.columns:
            prices = data['Adj Close'].dropna()
        elif len(data.columns) == 1:
            prices = data.iloc[:, 0].dropna()
        else:
            return np.nan
            
        if len(prices) < 2:
            return np.nan
            
        prezzo_finale = prices.iloc[-1]
        
        if giorni_indietro is None:
            prezzo_iniziale = prices.iloc[0]
        else:
            # Prendi il prezzo di N giorni fa
            if len(prices) > giorni_indietro:
                prezzo_iniziale = prices.iloc[-giorni_indietro-1]
            else:
                prezzo_iniziale = prices.iloc[0]
        
        if prezzo_iniziale == 0 or pd.isna(prezzo_iniziale) or pd.isna(prezzo_finale):
            return np.nan
            
        return ((prezzo_finale - prezzo_iniziale) / prezzo_iniziale) * 100
        
    except Exception as e:
        return np.nan

def calcola_rendimento_annualizzato_safe(data, target_years):
    """Calcola rendimento annualizzato più sicuro"""
    try:
        if data.empty:
            return np.nan
            
        # Determina la colonna prezzo
        if 'Close' in data.columns:
            prices = data['Close'].dropna()
        elif 'Adj Close' in data.columns:
            prices = data['Adj Close'].dropna()
        elif len(data.columns) == 1:
            prices = data.iloc[:, 0].dropna()
        else:
            return np.nan
            
        if len(prices) < 2:
            return np.nan
            
        prezzo_iniziale = prices.iloc[0]
        prezzo_finale = prices.iloc[-1]
        
        # Calcola anni effettivi
        anni_effettivi = (prices.index[-1] - prices.index[0]).days / 365.25
        
        if anni_effettivi <= 0 or prezzo_iniziale <= 0:
            return np.nan
            
        rendimento_annuo = (((prezzo_finale / prezzo_iniziale) ** (1/anni_effettivi)) - 1) * 100
        return rendimento_annuo
        
    except Exception as e:
        return np.nan

# Selezione indici da visualizzare
st.header("📊 Performance degli Indici")

# Filtri per categoria
col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)

with col_filter1:
    mostra_azionari = st.checkbox("Solo Azionari", value=False)
with col_filter2:
    mostra_obbligazionari = st.checkbox("Solo Obbligazionari", value=False)
with col_filter3:
    mostra_europei = st.checkbox("Solo Europei", value=False)
with col_filter4:
    mostra_americani = st.checkbox("Solo Americani", value=False)

# Applicazione filtri
indici_filtrati = list(INDICI_PRINCIPALI.keys())

if mostra_azionari:
    indici_filtrati = [k for k in indici_filtrati 
                      if not any(x in k for x in ["Treasury", "Bond", "AGG", "LQD", "HYG", "TLT"])]

if mostra_obbligazionari:
    indici_filtrati = [k for k in indici_filtrati 
                      if any(x in k for x in ["Treasury", "Bond", "AGG", "LQD", "HYG", "TLT"])]

if mostra_europei:
    indici_filtrati = [k for k in indici_filtrati 
                      if any(x in k for x in ["FTSE", "DAX", "CAC", "Euro", "EUR"])]

if mostra_americani:
    indici_filtrati = [k for k in indici_filtrati 
                      if any(x in k for x in ["S&P", "NASDAQ", "Dow", "Russell", "AGG", "TLT", "LQD", "HYG", "USD"])]

# Selezione finale degli indici con un limite ragionevole
max_indici = min(8, len(indici_filtrati))  # Limita per evitare timeout
indici_selezionati = st.multiselect(
    "Seleziona gli indici da analizzare:",
    indici_filtrati,
    default=indici_filtrati[:max_indici]
)

# Aggiungi opzione debug
debug_mode = st.sidebar.checkbox("Modalità Debug", value=False)

if indici_selezionati:
    # Definizione dei periodi con mapping più preciso
    periodi = {
        "1M": ("1mo", 30),
        "3M": ("3mo", 90),
        "6M": ("6mo", 180),
        "1A": ("1y", 252),
        "2A": ("2y", 504),
        "5A": ("5y", 1260)
    }
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Lista per i risultati
    risultati = []
    errori_debug = []
    
    # Download e calcolo per ogni indice
    for i, nome_indice in enumerate(indici_selezionati):
        ticker = INDICI_PRINCIPALI[nome_indice]
        status_text.text(f"Elaborazione: {nome_indice} ({ticker}) - {i+1}/{len(indici_selezionati)}")
        
        # Inizializza riga risultato
        riga = {"Indice": nome_indice, "Ticker": ticker}
        debug_info = {"Indice": nome_indice, "Ticker": ticker}
        
        try:
            # Test di connessione base
            test_data = download_data_safe(ticker, period="5d")
            debug_info["Test_Data_Empty"] = test_data.empty
            debug_info["Test_Data_Length"] = len(test_data)
            
            if test_data.empty:
                # Fallback per ticker problematici
                debug_info["Error"] = "Nessun dato dal test iniziale"
                for periodo_nome in periodi.keys():
                    riga[f"Perf_{periodo_nome}"] = "N/A"
                riga["Rend_5A"] = "N/A"
                errori_debug.append(debug_info)
                risultati.append(riga)
                continue
            
            # Scarica dati per ogni periodo
            for periodo_nome, (periodo_yf, giorni) in periodi.items():
                try:
                    data_periodo = download_data_safe(ticker, period=periodo_yf)
                    
                    if not data_periodo.empty:
                        performance = calcola_performance_safe(data_periodo)
                        if not pd.isna(performance):
                            riga[f"Perf_{periodo_nome}"] = f"{performance:.2f}%"
                            debug_info[f"Success_{periodo_nome}"] = True
                        else:
                            riga[f"Perf_{periodo_nome}"] = "N/A"
                            debug_info[f"Success_{periodo_nome}"] = False
                    else:
                        riga[f"Perf_{periodo_nome}"] = "N/A"
                        debug_info[f"Success_{periodo_nome}"] = False
                        
                except Exception as e:
                    riga[f"Perf_{periodo_nome}"] = "N/A"
                    debug_info[f"Error_{periodo_nome}"] = str(e)
            
            # Calcola rendimento medio 5 anni
            try:
                data_5y = download_data_safe(ticker, period="5y")
                if not data_5y.empty:
                    rend_5y = calcola_rendimento_annualizzato_safe(data_5y, 5)
                    if not pd.isna(rend_5y):
                        riga["Rend_5A"] = f"{rend_5y:.2f}%"
                        debug_info["Success_Rend_5A"] = True
                    else:
                        riga["Rend_5A"] = "N/A"
                        debug_info["Success_Rend_5A"] = False
                else:
                    riga["Rend_5A"] = "N/A"
                    debug_info["Success_Rend_5A"] = False
            except Exception as e:
                riga["Rend_5A"] = "N/A"
                debug_info["Error_Rend_5A"] = str(e)
                
        except Exception as e:
            # Errore generale
            debug_info["General_Error"] = str(e)
            for periodo_nome in periodi.keys():
                riga[f"Perf_{periodo_nome}"] = "N/A"
            riga["Rend_5A"] = "N/A"
        
        risultati.append(riga)
        errori_debug.append(debug_info)
        progress_bar.progress((i + 1) / len(indici_selezionati))
    
    # Pulisci progress bar
    progress_bar.empty()
    status_text.empty()
    
    # Crea DataFrame finale
    df_risultati = pd.DataFrame(risultati)
    
    # Rinomina colonne per visualizzazione
    column_mapping = {
        "Perf_1M": "1 Mese",
        "Perf_3M": "3 Mesi", 
        "Perf_6M": "6 Mesi",
        "Perf_1A": "1 Anno",
        "Perf_2A": "2 Anni",
        "Perf_5A": "5 Anni",
        "Rend_5A": "Rend. Medio 5A"
    }
    
    df_display = df_risultati.rename(columns=column_mapping)
    
    # Mostra tabella
    st.subheader("📈 Tabella Performance")
    
    # Rimuovi colonna Ticker se non in debug
    if not debug_mode and "Ticker" in df_display.columns:
        df_display = df_display.drop("Ticker", axis=1)
    
    st.dataframe(
        df_display,
        use_container_width=True,
        height=400
    )
    
    # Debug info
    if debug_mode:
        st.subheader("🔍 Informazioni Debug")
        df_debug = pd.DataFrame(errori_debug)
        st.dataframe(df_debug, use_container_width=True)
    
    # Statistiche riassuntive
    st.subheader("📊 Statistiche")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        indici_caricati = len([r for r in risultati if r.get("Perf_1A", "N/A") != "N/A"])
        st.metric("Indici con Dati", f"{indici_caricati}/{len(indici_selezionati)}")
    
    with col2:
        # Conta performance positive 1 anno
        perf_1a_positive = 0
        for r in risultati:
            perf_str = r.get("Perf_1A", "N/A")
            if perf_str != "N/A":
                try:
                    perf_val = float(perf_str.replace("%", ""))
                    if perf_val > 0:
                        perf_1a_positive += 1
                except:
                    pass
        st.metric("Performance 1A Positive", f"{perf_1a_positive}/{indici_caricati}")
    
    with col3:
        st.metric("Ultimo Aggiornamento", datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    # Suggerimenti se tutti i dati sono N/A
    if indici_caricati == 0:
        st.error("⚠️ Nessun dato disponibile. Possibili cause:")
        st.write("""
        - **Connessione Internet**: Verifica la connessione
        - **Ticker non validi**: Alcuni ticker potrebbero non esistere
        - **Limiti API**: Yahoo Finance potrebbe limitare le richieste
        - **Problemi temporanei**: Riprova tra qualche minuto
        """)
        
        st.info("💡 **Suggerimenti:**")
        st.write("""
        - Prova con meno indici contemporaneamente
        - Attiva la 'Modalità Debug' per vedere dettagli errori
        - Inizia con indici principali come S&P 500 o NASDAQ
        """)
    
    # Opzione per scaricare i dati
    if st.button("📥 Scarica Tabella CSV"):
        csv = df_display.to_csv(index=False)
        st.download_button(
            label="Scarica CSV",
            data=csv,
            file_name=f"performance_indici_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

else:
    st.info("Seleziona almeno un indice per visualizzare le performance.")

# Test di connessione
if st.sidebar.button("🔧 Test Connessione"):
    with st.spinner("Test connessione a Yahoo Finance..."):
        try:
            test_ticker = "^GSPC"  # S&P 500
            test_data = yf.download(test_ticker, period="5d", progress=False)
            if not test_data.empty:
                st.sidebar.success("✅ Connessione OK!")
                st.sidebar.write(f"Test su S&P 500: {len(test_data)} giorni di dati")
            else:
                st.sidebar.error("❌ Nessun dato ricevuto")
        except Exception as e:
            st.sidebar.error(f"❌ Errore: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        📈 Portfolio Tracker & Analyzer v2.0 | Powered by Streamlit & yfinance
    </div>
    """, 
    unsafe_allow_html=True
)
