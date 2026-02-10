import streamlit as st
import pandas as pd

# Configurações simples direto no código
st.set_page_config(page_title="Leitor de Odds", layout="wide")

st.title("📊 Leitor de Odds Online")
st.write("Se você está vendo isso, o servidor finalmente funcionou!")

# Simulação das suas constantes do config.py
REGION_CONFIG = {
    "us": "United States",
    "eu": "Europe",
    "uk": "United Kingdom"
}

st.sidebar.header("Configurações")
regiao = st.sidebar.selectbox("Escolha a Região", list(REGION_CONFIG.values()))

st.success(f"Monitorando odds para: {regiao}")

# Espaço para os dados
data = {
    'Bookmaker': ['Pinnacle', 'Betfair', 'Matchbook'],
    'Odd': [1.95, 2.02, 1.98]
}
df = pd.DataFrame(data)
st.table(df)
