import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configurazione pagina
st.set_page_config(
    page_title="Portfolio Tracker & Analyzer - CSV Edition",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Titolo principale
st.title("📈 Portfolio Tracker & Analyzer - CSV Edition")
st.markdown("Carica i tuoi file CSV per analizzare la performance degli indici")
st.markdown("---")

# Inizializza session state
if 'dati_caricati' not in st.session_state:
    st.session_state.dati_caricati = {}
if 'ultima_analisi' not in st.session_state:
    st.session_state.ultima_analisi = None

# Sidebar per caricamento file
st.sidebar.header("📂 Caricamento File CSV")
st.sidebar.markdown("**Formato richiesto:**")
st.sidebar.markdown("- Colonna 1: Date (formato: YYYY-MM-DD)")
st.sidebar.markdown("- Colonna 2: Prezzo/Valore dell'indice")

# File uploader
uploaded_files = st.sidebar.file_uploader(
    "Carica i tuoi file CSV",
    accept_multiple_files=True,
    type=['csv'],
    help="Puoi caricare più file contemporaneamente"
)

def pulisci_nome_colonna(nome):
    """Pulisce il nome della colonna rimuovendo caratteri speciali"""
    return nome.strip().replace('\n', ' ').replace('\r', '')

def carica_csv(file):
    """Carica e valida un file CSV"""
    try:
        # Leggi il CSV
        df = pd.read_csv(file)
        
        # Pulisci i nomi delle colonne
        df.columns = [pulisci_nome_colonna(col) for col in df.columns]
        
        # Verifica che abbia almeno 2 colonne
        if len(df.columns) < 2:
            return None, "Il file deve avere almeno 2 colonne (Data e Prezzo)"
        
        # Assegna nomi standard alle colonne
        df.columns = ['Date', 'Price'] + list(df.columns[2:])
        
        # Converti la colonna Date
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Converti la colonna Price in numerico
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
        # Rimuovi righe con valori mancanti
        df = df.dropna(subset=['Date', 'Price'])
        
        # Ordina per data
        df = df.sort_values('Date').reset_index(drop=True)
        
        if len(df) < 2:
            return None, "Il file deve contenere almeno 2 righe valide"
        
        return df, None
        
    except Exception as e:
        return None, f"Errore nel caricamento: {str(e)}"

# Caricamento e validazione dei file
if uploaded_files:
    st.header("📊 File Caricati")
    
    nuovi_dati = {}
    errori = []
    
    for file in uploaded_files:
        nome_file = file.name.replace('.csv', '')
        df, errore = carica_csv(file)
        
        if errore:
            errori.append(f"**{nome_file}**: {errore}")
        else:
            nuovi_dati[nome_file] = df
            
    # Mostra errori se presenti
    if errori:
        st.error("Errori nel caricamento:")
        for errore in errori:
            st.markdown(f"- {errore}")
    
    # Aggiorna session state
    st.session_state.dati_caricati.update(nuovi_dati)
    
    # Mostra summary dei file caricati
    if st.session_state.dati_caricati:
        st.success(f"✅ {len(st.session_state.dati_caricati)} file caricati con successo!")
        
        # Tabella riassuntiva
        summary_data = []
        for nome, df in st.session_state.dati_caricati.items():
            summary_data.append({
                'Indice': nome,
                'Numero Righe': len(df),
                'Data Inizio': df['Date'].min().strftime('%Y-%m-%d'),
                'Data Fine': df['Date'].max().strftime('%Y-%m-%d'),
                'Prezzo Minimo': f"{df['Price'].min():.2f}",
                'Prezzo Massimo': f"{df['Price'].max():.2f}"
            })
        
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(summary_df, use_container_width=True)

# Funzioni per calcolare performance
def calcola_performance(prezzo_inizio, prezzo_fine):
    """Calcola la performance percentuale"""
    if pd.isna(prezzo_inizio) or pd.isna(prezzo_fine) or prezzo_inizio == 0:
        return np.nan
    return ((prezzo_fine - prezzo_inizio) / prezzo_inizio) * 100

def calcola_rendimento_annualizzato(prezzo_inizio, prezzo_fine, anni):
    """Calcola il rendimento medio annuo"""
    if pd.isna(prezzo_inizio) or pd.isna(prezzo_fine) or prezzo_inizio == 0 or anni <= 0:
        return np.nan
    return (((prezzo_fine / prezzo_inizio) ** (1/anni)) - 1) * 100

def calcola_volatilita(prezzi):
    """Calcola la volatilità annualizzata"""
    if len(prezzi) < 2:
        return np.nan
    rendimenti = prezzi.pct_change().dropna()
    return rendimenti.std() * np.sqrt(252) * 100  # Assumendo 252 giorni di trading

def get_prezzo_per_periodo(df, giorni_fa):
    """Ottiene il prezzo più vicino a X giorni fa"""
    data_target = datetime.now() - timedelta(days=giorni_fa)
    df_copy = df.copy()
    df_copy['diff'] = abs((df_copy['Date'] - data_target).dt.days)
    idx = df_copy['diff'].idxmin()
    return df_copy.loc[idx, 'Price'], df_copy.loc[idx, 'Date']

# Analisi Performance
if st.session_state.dati_caricati:
    st.header("📈 Analisi Performance")
    
    # Selezione indici da analizzare
    indici_disponibili = list(st.session_state.dati_caricati.keys())
    indici_selezionati = st.multiselect(
        "Seleziona gli indici da analizzare:",
        indici_disponibili,
        default=indici_disponibili
    )
    
    if indici_selezionati:
        # Calcola performance
        risultati = []
        
        for nome_indice in indici_selezionati:
            df = st.session_state.dati_caricati[nome_indice]
            prezzo_attuale = df['Price'].iloc[-1]
            data_attuale = df['Date'].iloc[-1]
            
            riga = {"Indice": nome_indice}
            
            # Performance per diversi periodi
            periodi = {
                "1M": 30,
                "3M": 90,
                "6M": 180,
                "1A": 365,
                "3A": 1095,
                "5A": 1825
            }
            
            for periodo_nome, giorni in periodi.items():
                try:
                    prezzo_inizio, data_inizio = get_prezzo_per_periodo(df, giorni)
                    performance = calcola_performance(prezzo_inizio, prezzo_attuale)
                    riga[f"Performance {periodo_nome}"] = f"{performance:.2f}%" if not pd.isna(performance) else "N/A"
                except:
                    riga[f"Performance {periodo_nome}"] = "N/A"
            
            # Rendimenti annualizzati
            try:
                prezzo_5a, _ = get_prezzo_per_periodo(df, 1825)
                rend_5a = calcola_rendimento_annualizzato(prezzo_5a, prezzo_attuale, 5)
                riga["Rend. Medio 5A (%)"] = f"{rend_5a:.2f}%" if not pd.isna(rend_5a) else "N/A"
            except:
                riga["Rend. Medio 5A (%)"] = "N/A"
            
            # Volatilità annualizzata
            try:
                volatilita = calcola_volatilita(df['Price'])
                riga["Volatilità (%)"] = f"{volatilita:.2f}%" if not pd.isna(volatilita) else "N/A"
            except:
                riga["Volatilità (%)"] = "N/A"
            
            # Informazioni aggiuntive
            riga["Prezzo Attuale"] = f"{prezzo_attuale:.2f}"
            riga["Data Ultimo"] = data_attuale.strftime('%Y-%m-%d')
            
            risultati.append(riga)
        
        # Mostra tabella risultati
        df_risultati = pd.DataFrame(risultati)
        st.subheader("📊 Tabella Performance")
        st.dataframe(df_risultati, use_container_width=True, height=400)
        
        # Salva risultati in session state
        st.session_state.ultima_analisi = df_risultati
        
        # Grafici
        st.subheader("📈 Grafici Performance")
        
        # Seleziona tipo di grafico
        col1, col2 = st.columns(2)
        with col1:
            tipo_grafico = st.selectbox(
                "Tipo di grafico:",
                ["Serie Storica", "Performance 1 Anno", "Performance YTD", "Confronto Periodi"]
            )
        
        with col2:
            normalizza = st.checkbox("Normalizza a 100", value=True, help="Normalizza tutti gli indici a 100 al punto di partenza")
        
        if tipo_grafico == "Serie Storica":
            # Grafico serie storica
            fig = go.Figure()
            
            for nome_indice in indici_selezionati:
                df = st.session_state.dati_caricati[nome_indice]
                
                if normalizza:
                    # Normalizza a 100
                    prezzi_norm = (df['Price'] / df['Price'].iloc[0]) * 100
                    fig.add_trace(go.Scatter(
                        x=df['Date'],
                        y=prezzi_norm,
                        mode='lines',
                        name=nome_indice,
                        hovertemplate=f'{nome_indice}<br>Data: %{{x}}<br>Valore: %{{y:.2f}}<extra></extra>'
                    ))
                else:
                    fig.add_trace(go.Scatter(
                        x=df['Date'],
                        y=df['Price'],
                        mode='lines',
                        name=nome_indice,
                        hovertemplate=f'{nome_indice}<br>Data: %{{x}}<br>Prezzo: %{{y:.2f}}<extra></extra>'
                    ))
            
            fig.update_layout(
                title="Serie Storica degli Indici",
                xaxis_title="Data",
                yaxis_title="Valore Normalizzato (Base 100)" if normalizza else "Prezzo",
                height=600,
                hovermode='x unified'
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        elif tipo_grafico == "Performance 1 Anno":
            # Estrai performance 1 anno per il grafico
            perf_data = []
            for _, row in df_risultati.iterrows():
                perf_str = row.get("Performance 1A", "N/A")
                if perf_str != "N/A":
                    perf_val = float(perf_str.replace("%", ""))
                    perf_data.append({"Indice": row["Indice"], "Performance": perf_val})
            
            if perf_data:
                perf_df = pd.DataFrame(perf_data)
                perf_df = perf_df.sort_values("Performance", ascending=True)
                
                fig = px.bar(
                    perf_df,
                    x="Performance",
                    y="Indice",
                    orientation="h",
                    title="Performance 1 Anno (%)",
                    color="Performance",
                    color_continuous_scale="RdYlGn"
                )
                
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
        
        # Statistiche riassuntive
        st.subheader("📊 Statistiche Riassuntive")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Indici Analizzati", len(indici_selezionati))
        
        with col2:
            # Conta performance positive 1 anno
            perf_positive = 0
            for _, row in df_risultati.iterrows():
                perf_str = row.get("Performance 1A", "N/A")
                if perf_str != "N/A" and float(perf_str.replace("%", "")) > 0:
                    perf_positive += 1
            st.metric("Performance 1A Positive", f"{perf_positive}/{len(indici_selezionati)}")
        
        with col3:
            # Media performance 1 anno
            perf_values = []
            for _, row in df_risultati.iterrows():
                perf_str = row.get("Performance 1A", "N/A")
                if perf_str != "N/A":
                    perf_values.append(float(perf_str.replace("%", "")))
            
            if perf_values:
                media_perf = np.mean(perf_values)
                st.metric("Media Performance 1A", f"{media_perf:.2f}%")
            else:
                st.metric("Media Performance 1A", "N/A")
        
        with col4:
            st.metric("Ultimo Aggiornamento", datetime.now().strftime("%d/%m/%Y %H:%M"))
        
        # Download risultati
        if st.button("📥 Scarica Risultati CSV"):
            csv = df_risultati.to_csv(index=False)
            st.download_button(
                label="Scarica CSV",
                data=csv,
                file_name=f"analisi_performance_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv"
            )

# Gestione file caricati
if st.session_state.dati_caricati:
    st.sidebar.markdown("---")
    st.sidebar.header("🗂️ File Caricati")
    
    for nome in list(st.session_state.dati_caricati.keys()):
        col1, col2 = st.sidebar.columns([3, 1])
        with col1:
            st.sidebar.text(nome)
        with col2:
            if st.sidebar.button("🗑️", key=f"delete_{nome}", help="Elimina file"):
                del st.session_state.dati_caricati[nome]
                st.experimental_rerun()
    
    if st.sidebar.button("🗑️ Elimina Tutti"):
        st.session_state.dati_caricati = {}
        st.session_state.ultima_analisi = None
        st.experimental_rerun()

else:
    st.info("👆 Carica i tuoi file CSV dalla sidebar per iniziare l'analisi!")

# Footer
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #888;'>
        📈 Portfolio Tracker & Analyzer - CSV Edition | Powered by Streamlit
    </div>
    """, 
    unsafe_allow_html=True
)
