from datetime import date
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# ---------------------------------------------------------
# Configuración inicial de la página
# ---------------------------------------------------------
st.set_page_config(
    page_title="Reporte de Territorio", page_icon="📊", layout="wide"
)

st.title("📊 Reporte Diario de Territorio")
st.write(
    "Sistema conectado en tiempo real con Google Sheets (**TERRITORIO**)."
)

# Enlaces directos a tu hoja de cálculo
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1StjBMVIkueBy9sVy5dNh1ylpG5he-51iCYeeaj_mixM/edit"
PUBLISHED_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQq16I0eaHC0-Mf4hxWnQFIHdxIO11u5CtDmcDGTJ2UZGgv6YhM-x8RJhW31n6dSKBnFEQO9doPoD1y/pub?output=csv"

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)


# ---------------------------------------------------------
# 1. Cargar nombres del Personal de Bienestar (Columna B)
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_personal():
  try:
    # 1. Intento por la conexión oficial de GSheets
    df_personal = conn.read(
        spreadsheet=SPREADSHEET_URL,
        worksheet="PERSONAL_DE_BIENESTAR",
        ttl="1m",
    )
    if df_personal.shape[1] >= 2:
      col_nombres = df_personal.iloc[:, 1]
    else:
      col_nombres = df_personal.iloc[:, 0]
    nombres = sorted(
        col_nombres.dropna().astype(str).str.strip().unique().tolist()
    )
    if nombres:
      return nombres
  except Exception:
    pass

  try:
    # 2. Intento por el CSV publicado en la web
    df_publico = pd.read_csv(PUBLISHED_CSV_URL)
    if df_publico.shape[1] >= 2:
      col_nombres = df_publico.iloc[:, 1]
    else:
