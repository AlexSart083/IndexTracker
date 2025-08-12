import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
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

# Dizionario degli indici principali (aggiornato con ticker corretti)
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
    "MSCI World": "URTH",  # ETF iShares MSCI World
    "MSCI ACWI": "ACWI",   # ETF iShares MSCI ACWI
    "MSCI EM": "EEM",      # ETF iShares MSCI Emerging Markets
    "MSCI Europe": "IEV",  # ETF iShares MSCI Europe
    
    # Indici Obbligazionari USA
    "US 10Y Treasury": "^TNX",
    "US 2Y Treasury": "^IRX",
    "US 30Y Treasury": "^TYX",
    "TLT (20+ Year Treasury)": "TLT",  # ETF Treasury a lungo termine
    "AGG (Total Bond Market)": "AGG",  # ETF Aggregate Bond
    "LQD (Investment Grade)": "LQD",   # ETF Corporate Bond IG
    "HYG (High Yield)": "HYG",        # ETF High Yield Corporate
    "TIPS (Inflation Protected)": "SCHP", # ETF Treasury Inflation-Protected
    
    # Indici Obbligazionari Europei
    "German 10Y Bund": "^TNX",        # Placeholder - useremo ETF
    "EAG (Euro Aggregate Bond)": "AGGH", # Correzione ticker
    "IGLS (UK Gilts)": "IGLS",           # ETF UK Gilts 1-5Y
    "IGLL (UK Gilts)": "IGLL",           # ETF UK Gilts 3-7Y
    "IGLH (UK Gilts)": "IGLH",           # ETF UK Gilts 7-15Y
    "INXG (UK Gilts)": "INXG",           # ETF UK Gilts 15Y+
    
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

# Selezione periodo
periodo = st.sidebar.selectbox(
    "📅 Seleziona Periodo",
    ["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "MAX"]
)

# Mapping periodi per yfinance
periodo_mapping = {
    "1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", 
    "2Y": "2y", "5Y": "5y", "10Y": "10y", "MAX": "max"
}

# Tab principale
tab1, tab2, tab3 = st.tabs(["📊 Dashboard Indici", "💼 Creatore Portfolio", "📈 Analisi Performance"])

with tab1:
    st.header("Dashboard Indici Principali")
    
    # Selezione indici da visualizzare
    indici_selezionati = st.multiselect(
        "Seleziona gli indici da visualizzare:",
        list(INDICI_PRINCIPALI.keys()),
        default=["STOXX Europe 600", "MSCI World", "FTSE MIB", "EAG (Euro Aggregate Bond)"]
    )
    
    # Categorie per filtraggio
    col_filter1, col_filter2, col_filter3 = st.columns(3)
    with col_filter1:
        mostra_azionari = st.checkbox("Solo Azionari", value=False)
    with col_filter2:
        mostra_obbligazionari = st.checkbox("Solo Obbligazionari", value=False)
    with col_filter3:
        mostra_europei = st.checkbox("Solo Europei", value=False)
    
    # Filtro categorie
    if mostra_azionari:
        categorie_azionarie = [k for k in INDICI_PRINCIPALI.keys() 
                             if not any(x in k for x in ["Treasury", "Bond", "AGG", "LQD", "HYG", "TIPS", "EAG", "IGLS", "IGLL", "IGLH", "INXG", "Gilt"])]
        indici_selezionati = [idx for idx in indici_selezionati if idx in categorie_azionarie]
    
    if mostra_obbligazionari:
        categorie_obbligazionarie = [k for k in INDICI_PRINCIPALI.keys() 
                                   if any(x in k for x in ["Treasury", "Bond", "AGG", "LQD", "HYG", "TIPS", "EAG", "IGLS", "IGLL", "IGLH", "INXG", "Gilt"])]
        indici_selezionati = [idx for idx in indici_selezionati if idx in categorie_obbligazionarie]
    
    if mostra_europei:
        categorie_europee = [k for k in INDICI_PRINCIPALI.keys() 
                           if any(x in k for x in ["FTSE", "DAX", "CAC", "Euro", "STOXX", "IBEX", "AEX", "SMI", "EAG", "IGLS", "IGLL", "IGLH", "INXG", "Gilt", "UK", "German", "EUR"])]
        indici_selezionati = [idx for idx in indici_selezionati if idx in categorie_europee]
    
    if indici_selezionati:
        # Download dati
        with st.spinner("Caricamento dati..."):
            dati_indici = {}
            errori_download = []
            
            for nome_indice in indici_selezionati:
                ticker = INDICI_PRINCIPALI[nome_indice]
                try:
                    data = yf.download(ticker, period=periodo_mapping[periodo], progress=False)
                    if not data.empty and 'Close' in data.columns:
                        dati_indici[nome_indice] = data
                    else:
                        errori_download.append(f"{nome_indice} ({ticker}): Nessun dato disponibile")
                except Exception as e:
                    errori_download.append(f"{nome_indice} ({ticker}): {str(e)}")
            
            # Mostra errori se presenti
            if errori_download:
                with st.expander("⚠️ Errori nel caricamento dati", expanded=False):
                    for errore in errori_download:
                        st.warning(errore)
        
        if dati_indici:
            # Grafici degli indici
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.subheader("Andamento Prezzi")
                fig = go.Figure()
                
                for nome_indice, data in dati_indici.items():
                    fig.add_trace(go.Scatter(
                        x=data.index,
                        y=data['Close'],
                        mode='lines',
                        name=nome_indice,
                        line=dict(width=2)
                    ))
                
                fig.update_layout(
                    title="Andamento Prezzi degli Indici",
                    xaxis_title="Data",
                    yaxis_title="Prezzo",
                    height=500,
                    hovermode='x unified'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("Performance Periodo")
                performance_data = []
                
                for nome_indice, data in dati_indici.items():
                    if len(data) > 1:
                        # Assicuriamoci di ottenere valori scalari
                        inizio = float(data['Close'].iloc[0])
                        fine = float(data['Close'].iloc[-1])
                        performance = ((fine - inizio) / inizio) * 100
                        
                        performance_data.append({
                            "Indice": nome_indice,
                            "Performance (%)": round(performance, 2),  # Valore numerico
                            "Prezzo Attuale": round(fine, 2),
                            "Var. Assoluta": round(fine - inizio, 2)
                        })
                
                if performance_data:
                    df_performance = pd.DataFrame(performance_data)
                    
                    # Debug: verifica i tipi di dati
                    # st.write("Debug - Tipi di dati:", df_performance.dtypes)
                    
                    st.dataframe(df_performance, use_container_width=True)
                    
                    # Grafico performance - assicuriamoci che i dati siano corretti
                    try:
                        fig_perf = px.bar(
                            df_performance, 
                            x="Indice", 
                            y="Performance (%)",
                            title="Performance per Indice",
                            color="Performance (%)",
                            color_continuous_scale="RdYlGn"
                        )
                        fig_perf.update_layout(height=300, xaxis_tickangle=45)
                        st.plotly_chart(fig_perf, use_container_width=True)
                    except Exception as e:
                        st.error(f"Errore nella creazione del grafico: {str(e)}")
                        # Fallback: grafico semplice
                        fig_simple = go.Figure(data=[
                            go.Bar(x=df_performance["Indice"], y=df_performance["Performance (%)"])
                        ])
                        fig_simple.update_layout(title="Performance per Indice", height=300)
                        st.plotly_chart(fig_simple, use_container_width=True)
        else:
            st.warning("Nessun dato disponibile per gli indici selezionati.")

with tab2:
    st.header("💼 Creatore Portfolio")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Configurazione Portfolio")
        
        # Selezione indici per il portfolio
        indici_portfolio = st.multiselect(
            "Seleziona indici per il portfolio:",
            list(INDICI_PRINCIPALI.keys()),
            default=["STOXX Europe 600", "EAG (Euro Aggregate Bond)"]
        )
        
        # Suggerimenti allocazione predefiniti
        st.markdown("**💡 Suggerimenti Allocazione:**")
        col_sugg1, col_sugg2, col_sugg3 = st.columns(3)
        with col_sugg1:
            if st.button("🛡️ Conservativo"):
                st.info("30% Azionario, 70% Obbligazionario")
        with col_sugg2:
            if st.button("⚖️ Bilanciato"):
                st.info("60% Azionario, 40% Obbligazionario")
        with col_sugg3:
            if st.button("🚀 Aggressivo"):
                st.info("80% Azionario, 20% Obbligazionario")
        
        # Preset portfolio europei
        st.markdown("**🇪🇺 Portfolio Europei Preimpostati:**")
        col_eu1, col_eu2 = st.columns(2)
        with col_eu1:
            if st.button("Europa Bilanciato"):
                st.session_state.preset_portfolio = {
                    "STOXX Europe 600": 50,
                    "EAG (Euro Aggregate Bond)": 30,
                    "IGLL (UK Gilts)": 20
                }
        with col_eu2:
            if st.button("Europa + Globale"):
                st.session_state.preset_portfolio = {
                    "STOXX Europe 600": 40,
                    "MSCI World": 20,
                    "EAG (Euro Aggregate Bond)": 30,
                    "HYG (High Yield)": 10
                }
        
        if indici_portfolio:
            st.subheader("Allocazione Pesi (%)")
            pesi = {}
            peso_totale = 0
            
            for indice in indici_portfolio:
                peso = st.slider(
                    f"{indice}",
                    min_value=0,
                    max_value=100,
                    value=100//len(indici_portfolio),
                    step=5,
                    key=f"peso_{indice}"
                )
                pesi[indice] = peso / 100
                peso_totale += peso
            
            # Validazione pesi
            if peso_totale != 100:
                st.warning(f"⚠️ I pesi devono sommare a 100%. Attualmente: {peso_totale}%")
            else:
                st.success("✅ Allocazione validata!")
            
            # Investimento iniziale
            investimento = st.number_input(
                "Investimento iniziale (€):",
                min_value=100,
                max_value=1000000,
                value=10000,
                step=100
            )
    
    with col2:
        if indici_portfolio and peso_totale == 100:
            st.subheader("Analisi Portfolio")
            
            # Download dati portfolio
            with st.spinner("Creazione portfolio..."):
                dati_portfolio = {}
                errori_portfolio = []
                
                for indice in indici_portfolio:
                    ticker = INDICI_PRINCIPALI[indice]
                    try:
                        data = yf.download(ticker, period=periodo_mapping[periodo], progress=False)
                        if not data.empty and 'Close' in data.columns:
                            dati_portfolio[indice] = data['Close']
                        else:
                            errori_portfolio.append(f"{indice}: Nessun dato disponibile")
                    except Exception as e:
                        errori_portfolio.append(f"{indice}: {str(e)}")
                
                if errori_portfolio:
                    st.warning("Alcuni indici non sono stati caricati:")
                    for errore in errori_portfolio:
                        st.write(f"• {errore}")
            
            if dati_portfolio:
                # Normalizzazione e calcolo portfolio
                df_portfolio = pd.DataFrame(dati_portfolio)
                df_portfolio = df_portfolio.dropna()
                
                if len(df_portfolio) > 0:
                    # Normalizzazione a base 100
                    df_norm = df_portfolio / df_portfolio.iloc[0] * 100
                    
                    # Calcolo valore portfolio
                    portfolio_value = sum(df_norm[indice] * pesi[indice] for indice in dati_portfolio.keys())
                    
                    # Valore in euro
                    portfolio_euro = portfolio_value * (investimento / 100)
                    
                    # Grafici
                    fig_portfolio = make_subplots(
                        rows=2, cols=2,
                        subplot_titles=("Valore Portfolio (€)", "Performance Normalizzata", 
                                      "Allocazione", "Volatilità"),
                        specs=[[{"secondary_y": False}, {"secondary_y": False}],
                               [{"type": "pie"}, {"secondary_y": False}]]
                    )
                    
                    # Valore portfolio
                    fig_portfolio.add_trace(
                        go.Scatter(x=df_portfolio.index, y=portfolio_euro, 
                                  name="Portfolio", line=dict(width=3, color="blue")),
                        row=1, col=1
                    )
                    
                    # Performance normalizzata
                    for indice in dati_portfolio.keys():
                        fig_portfolio.add_trace(
                            go.Scatter(x=df_norm.index, y=df_norm[indice], name=indice),
                            row=1, col=2
                        )
                    
                    # Pie chart allocazione
                    fig_portfolio.add_trace(
                        go.Pie(labels=list(pesi.keys()), values=list(pesi.values()), name="Allocazione"),
                        row=2, col=1
                    )
                    
                    # Volatilità
                    returns = df_portfolio.pct_change().dropna()
                    if len(returns) > 0:
                        volatility = returns.std() * np.sqrt(252) * 100  # Annualizzata
                        
                        fig_portfolio.add_trace(
                            go.Bar(x=list(volatility.index), y=volatility.values, name="Volatilità"),
                            row=2, col=2
                        )
                    
                    fig_portfolio.update_layout(height=600, showlegend=True)
                    st.plotly_chart(fig_portfolio, use_container_width=True)
                    
                    # Metriche portfolio
                    st.subheader("📊 Metriche Portfolio")
                    
                    performance_portfolio = ((portfolio_euro.iloc[-1] - investimento) / investimento) * 100
                    rendimento_annualizzato = (((portfolio_euro.iloc[-1] / investimento) ** (365 / len(portfolio_euro))) - 1) * 100
                    
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    
                    with col_m1:
                        st.metric("Valore Attuale", f"€{portfolio_euro.iloc[-1]:,.2f}", 
                                 f"{performance_portfolio:+.2f}%")
                    
                    with col_m2:
                        st.metric("Rendimento Tot.", f"{performance_portfolio:.2f}%")
                    
                    with col_m3:
                        st.metric("Rendimento Ann.", f"{rendimento_annualizzato:.2f}%")
                    
                    with col_m4:
                        portfolio_vol = (portfolio_euro.pct_change().std() * np.sqrt(252)) * 100
                        st.metric("Volatilità Ann.", f"{portfolio_vol:.2f}%")
                else:
                    st.error("Nessun dato valido trovato per il portfolio.")

with tab3:
    st.header("📈 Analisi Performance Avanzata")
    
    # Selezione indici per confronto
    indici_confronto = st.multiselect(
        "Seleziona indici per l'analisi comparativa:",
        list(INDICI_PRINCIPALI.keys()),
        default=["STOXX Europe 600", "S&P 500", "MSCI World", "EAG (Euro Aggregate Bond)"]
    )
    
    # Analisi per categorie migliorata
    col_cat1, col_cat2 = st.columns(2)
    with col_cat1:
        st.subheader("📈 Asset Class Analysis")
        if indici_confronto:
            azionari = [idx for idx in indici_confronto if not any(x in idx for x in ["Treasury", "Bond", "AGG", "LQD", "HYG", "TIPS", "EAG", "IGLS", "IGLL", "IGLH", "INXG", "Gilt"])]
            obbligazionari = [idx for idx in indici_confronto if any(x in idx for x in ["Treasury", "Bond", "AGG", "LQD", "HYG", "TIPS", "EAG", "IGLS", "IGLL", "IGLH", "INXG", "Gilt"])]
            
            if azionari:
                st.write("**📊 Azionari:**")
                for az in azionari[:5]:
                    st.write(f"• {az}")
            
            if obbligazionari:
                st.write("**🏛️ Obbligazionari:**")
                for obb in obbligazionari[:5]:
                    st.write(f"• {obb}")
    
    with col_cat2:
        st.subheader("🌍 Geographic Diversification")
        if indici_confronto:
            usa = [idx for idx in indici_confronto if any(x in idx for x in ["S&P", "NASDAQ", "Dow", "Russell", "US ", "AGG", "TLT", "LQD", "HYG"])]
            europa = [idx for idx in indici_confronto if any(x in idx for x in ["FTSE", "DAX", "CAC", "Euro", "STOXX", "IBEX", "AEX", "SMI", "EAG", "IGLS", "IGLL", "IGLH", "INXG", "UK", "German"])]
            globali = [idx for idx in indici_confronto if any(x in idx for x in ["MSCI World", "MSCI ACWI", "MSCI EM", "MSCI Europe"])]
            asia = [idx for idx in indici_confronto if any(x in idx for x in ["Nikkei", "Hang Seng", "ASX", "Kospi"])]
            
            regions = [
                ("🇺🇸 USA", len(usa)),
                ("🇪🇺 Europa", len(europa)),
                ("🌍 Globali", len(globali)),
                ("🌏 Asia", len(asia))
            ]
            
            for region, count in regions:
                if count > 0:
                    st.write(f"**{region}:** {count} indici")
    
    if indici_confronto:
        # Download dati
        with st.spinner("Analisi in corso..."):
            dati_analisi = {}
            for indice in indici_confronto:
                ticker = INDICI_PRINCIPALI[indice]
                try:
                    data = yf.download(ticker, period="2y", progress=False)
                    if not data.empty and 'Close' in data.columns:
                        dati_analisi[indice] = data['Close']
                except:
                    pass
        
        if dati_analisi:
            df_analisi = pd.DataFrame(dati_analisi).dropna()
            
            if len(df_analisi) > 1:
                returns = df_analisi.pct_change().dropna()
                
                # Metriche avanzate
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Matrice di Correlazione")
                    if len(returns) > 0:
                        corr_matrix = returns.corr()
                        fig_corr = px.imshow(
                            corr_matrix, 
                            text_auto=True, 
                            aspect="auto",
                            color_continuous_scale="RdBu"
                        )
                        fig_corr.update_layout(height=400)
                        st.plotly_chart(fig_corr, use_container_width=True)
                
                with col2:
                    st.subheader("Rischio vs Rendimento")
                    
                    metrics_data = []
                    for indice in indici_confronto:
                        if indice in returns.columns:
                            ret = returns[indice]
                            rendimento_medio = ret.mean() * 252 * 100  # Annualizzato
                            volatilita = ret.std() * np.sqrt(252) * 100  # Annualizzata
                            sharpe = rendimento_medio / volatilita if volatilita != 0 else 0
                            
                            metrics_data.append({
                                "Indice": indice,
                                "Rendimento (%)": round(rendimento_medio, 2),
                                "Volatilità (%)": round(volatilita, 2),
                                "Sharpe Ratio": round(sharpe, 2)
                            })
                    
                    if metrics_data:
                        df_metrics = pd.DataFrame(metrics_data)
                        
                        fig_scatter = px.scatter(
                            df_metrics, 
                            x="Volatilità (%)", 
                            y="Rendimento (%)",
                            text="Indice",
                            title="Frontiera Efficiente"
                        )
                        fig_scatter.update_traces(textposition="top center")
                        fig_scatter.update_layout(height=400)
                        st.plotly_chart(fig_scatter, use_container_width=True)
                        
                        # Tabella metriche
                        st.subheader("📊 Metriche Dettagliate")
                        st.dataframe(df_metrics, use_container_width=True)

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
