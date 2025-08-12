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

# Dizionario degli indici principali
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
    "STOXX Europe 600": "^STOXX",
    "IBEX 35": "^IBEX",
    "AEX": "^AEX",
    "SMI": "^SSMI",
    
    # Indici Azionari Asia-Pacifico
    "Nikkei 225": "^N225",
    "Hang Seng": "^HSI",
    "ASX 200": "^AXJO",
    "Kospi": "^KS11",
    
    # Indici MSCI Globali
    "MSCI World": "URTH",
    "MSCI ACWI": "ACWI",
    "MSCI EM": "EEM",
    "MSCI Europe": "IEV",
    
    # Indici Obbligazionari USA
    "US 10Y Treasury": "^TNX",
    "US 2Y Treasury": "^IRX",
    "US 30Y Treasury": "^TYX",
    "TLT (20+ Year Treasury)": "TLT",
    "AGG (Total Bond Market)": "AGG",
    "LQD (Investment Grade)": "LQD",
    "HYG (High Yield)": "HYG",
    "TIPS (Inflation Protected)": "SCHP",
    
    # Indici Obbligazionari Europei
    "EAG (Euro Aggregate Bond)": "AGGH",
    "IGLS (UK Gilts)": "IGLS",
    "IGLL (UK Gilts)": "IGLL",
    "IGLH (UK Gilts)": "IGLH",
    "INXG (UK Gilts)": "INXG",
    
    # Materie Prime e Alternative
    "VIX (Volatilità)": "^VIX",
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Oil (WTI)": "CL=F",
    "Oil (Brent)": "BZ=F",
    "Natural Gas": "NG=F",
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X"
}

# Funzione per calcolare la performance
def calcola_performance(prezzi_inizio, prezzi_fine):
    """Calcola la performance percentuale tra due prezzi"""
    if pd.isna(prezzi_inizio) or pd.isna(prezzi_fine) or prezzi_inizio == 0:
        return np.nan
    return ((prezzi_fine - prezzi_inizio) / prezzi_inizio) * 100

# Funzione per calcolare rendimento annualizzato
def calcola_rendimento_annualizzato(prezzi_inizio, prezzi_fine, anni):
    """Calcola il rendimento medio annuo"""
    if pd.isna(prezzi_inizio) or pd.isna(prezzi_fine) or prezzi_inizio == 0 or anni <= 0:
        return np.nan
    return (((prezzi_fine / prezzi_inizio) ** (1/anni)) - 1) * 100

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
                      if not any(x in k for x in ["Treasury", "Bond", "AGG", "LQD", "HYG", "TIPS", "EAG", "IGLS", "IGLL", "IGLH", "INXG", "Gilt"])]

if mostra_obbligazionari:
    indici_filtrati = [k for k in indici_filtrati 
                      if any(x in k for x in ["Treasury", "Bond", "AGG", "LQD", "HYG", "TIPS", "EAG", "IGLS", "IGLL", "IGLH", "INXG", "Gilt"])]

if mostra_europei:
    indici_filtrati = [k for k in indici_filtrati 
                      if any(x in k for x in ["FTSE", "DAX", "CAC", "Euro", "STOXX", "IBEX", "AEX", "SMI", "EAG", "IGLS", "IGLL", "IGLH", "INXG", "Gilt", "UK", "EUR"])]

if mostra_americani:
    indici_filtrati = [k for k in indici_filtrati 
                      if any(x in k for x in ["S&P", "NASDAQ", "Dow", "Russell", "US ", "AGG", "TLT", "LQD", "HYG", "TIPS", "USD"])]

# Selezione finale degli indici
indici_selezionati = st.multiselect(
    "Seleziona gli indici da analizzare:",
    indici_filtrati,
    default=indici_filtrati[:10] if len(indici_filtrati) >= 10 else indici_filtrati
)

if indici_selezionati:
    # Definizione dei periodi
    periodi = {
        "1M": "1mo",
        "3M": "3mo", 
        "6M": "6mo",
        "1A": "1y",
        "3A": "3y",
        "5A": "5y",
        "10A": "10y"
    }
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Lista per i risultati
    risultati = []
    
    # Download e calcolo per ogni indice
    for i, nome_indice in enumerate(indici_selezionati):
        ticker = INDICI_PRINCIPALI[nome_indice]
        status_text.text(f"Elaborazione: {nome_indice} ({i+1}/{len(indici_selezionati)})")
        
        # Inizializza riga risultato
        riga = {"Indice": nome_indice}
        
        try:
            # Download dati per 10 anni (periodo più lungo)
            data = yf.download(ticker, period="10y", progress=False)
            
            if data.empty or 'Close' not in data.columns:
                # Se fallisce, riempi con N/A
                for periodo in periodi.keys():
                    riga[f"Performance {periodo}"] = "N/A"
                riga["Rend. Medio 5A (%)"] = "N/A"
                riga["Rend. Medio 10A (%)"] = "N/A"
                risultati.append(riga)
                continue
            
            prezzi = data['Close'].dropna()
            prezzo_attuale = prezzi.iloc[-1] if len(prezzi) > 0 else np.nan
            
            # Calcola performance per ogni periodo
            for periodo_nome, periodo_yf in periodi.items():
                try:
                    # Scarica dati per il periodo specifico
                    data_periodo = yf.download(ticker, period=periodo_yf, progress=False)
                    if not data_periodo.empty and 'Close' in data_periodo.columns:
                        prezzi_periodo = data_periodo['Close'].dropna()
                        if len(prezzi_periodo) >= 2:
                            prezzo_inizio = prezzi_periodo.iloc[0]
                            performance = calcola_performance(prezzo_inizio, prezzo_attuale)
                            riga[f"Performance {periodo_nome}"] = f"{performance:.2f}%" if not pd.isna(performance) else "N/A"
                        else:
                            riga[f"Performance {periodo_nome}"] = "N/A"
                    else:
                        riga[f"Performance {periodo_nome}"] = "N/A"
                except:
                    riga[f"Performance {periodo_nome}"] = "N/A"
            
            # Calcola rendimenti medi annualizzati
            # 5 anni
            try:
                data_5y = yf.download(ticker, period="5y", progress=False)
                if not data_5y.empty and 'Close' in data_5y.columns:
                    prezzi_5y = data_5y['Close'].dropna()
                    if len(prezzi_5y) >= 2:
                        prezzo_inizio_5y = prezzi_5y.iloc[0]
                        rend_5y = calcola_rendimento_annualizzato(prezzo_inizio_5y, prezzo_attuale, 5)
                        riga["Rend. Medio 5A (%)"] = f"{rend_5y:.2f}%" if not pd.isna(rend_5y) else "N/A"
                    else:
                        riga["Rend. Medio 5A (%)"] = "N/A"
                else:
                    riga["Rend. Medio 5A (%)"] = "N/A"
            except:
                riga["Rend. Medio 5A (%)"] = "N/A"
            
            # 10 anni
            try:
                if len(prezzi) >= 2:
                    prezzo_inizio_10y = prezzi.iloc[0]
                    # Calcola anni effettivi dai dati
                    anni_effettivi = (prezzi.index[-1] - prezzi.index[0]).days / 365.25
                    if anni_effettivi > 0:
                        rend_10y = calcola_rendimento_annualizzato(prezzo_inizio_10y, prezzo_attuale, anni_effettivi)
                        riga["Rend. Medio 10A (%)"] = f"{rend_10y:.2f}%" if not pd.isna(rend_10y) else "N/A"
                    else:
                        riga["Rend. Medio 10A (%)"] = "N/A"
                else:
                    riga["Rend. Medio 10A (%)"] = "N/A"
            except:
                riga["Rend. Medio 10A (%)"] = "N/A"
                
        except Exception as e:
            # In caso di errore, riempi con N/A
            for periodo in periodi.keys():
                riga[f"Performance {periodo}"] = "N/A"
            riga["Rend. Medio 5A (%)"] = "N/A"
            riga["Rend. Medio 10A (%)"] = "N/A"
        
        risultati.append(riga)
        progress_bar.progress((i + 1) / len(indici_selezionati))
    
    # Pulisci progress bar
    progress_bar.empty()
    status_text.empty()
    
    # Crea DataFrame finale
    df_risultati = pd.DataFrame(risultati)
    
    # Mostra tabella
    st.subheader("📈 Tabella Performance")
    st.dataframe(
        df_risultati,
        use_container_width=True,
        height=600
    )
    
    # Statistiche riassuntive
    st.subheader("📊 Statistiche")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        indici_caricati = len([r for r in risultati if r["Performance 1A"] != "N/A"])
        st.metric("Indici Caricati", f"{indici_caricati}/{len(indici_selezionati)}")
    
    with col2:
        # Conta performance positive 1 anno
        perf_1a_positive = len([r for r in risultati 
                               if r["Performance 1A"] != "N/A" and 
                               float(r["Performance 1A"].replace("%", "")) > 0])
        st.metric("Performance 1A Positive", f"{perf_1a_positive}/{indici_caricati}")
    
    with col3:
        # Data ultimo aggiornamento
        st.metric("Ultimo Aggiornamento", datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    # Opzione per scaricare i dati
    if st.button("📥 Scarica Tabella CSV"):
        csv = df_risultati.to_csv(index=False)
        st.download_button(
            label="Scarica CSV",
            data=csv,
            file_name=f"performance_indici_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

else:
    st.info("Seleziona almeno un indice per visualizzare le performance.")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        📈 Portfolio Tracker & Analyzer | Powered by Streamlit & yfinance
    </div>
    """, 
    unsafe_allow_html=True
)
