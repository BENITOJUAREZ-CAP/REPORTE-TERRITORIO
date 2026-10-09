from datetime import date
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración inicial de la página
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
# 1. Cargar nombres del Personal de Bienestar
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_personal():
  # Intento 1: Leer mediante la URL del CSV publicado en la web
  try:
    df_publico = pd.read_csv(PUBLISHED_CSV_URL)
    if df_publico.shape[1] >= 2:
      col_nombres = df_publico.iloc[:, 1]
    else:
      col_nombres = df_publico.iloc[:, 0]

    nombres = sorted(
        col_nombres.dropna().astype(str).str.strip().unique().tolist()
    )
    if len(nombres) > 0:
      return nombres
  except Exception:
    pass

  # Intento 2: Conexión mediante la API de Google Sheets
  try:
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
    if len(nombres) > 0:
      return nombres
  except Exception:
    pass

  # Intento 3: Lista base de respaldo
  return [
      "GRANADOS ROBLES AARON MOISES",
      "ROJAS SANTIAGO ALAN",
      "ROMERO CEBALLOS ALFREDO ESSAU",
      "AMAURI VARGAS LLANOS",
      "ALVARADO CRUZ ARSENIA",
      "GALICIA DECTOR CAROLINA",
      "GODINEZ CORTES CITLALLI ARAIS",
      "RICO CONTRERAS CLAUDINE",
      "GUERRERO RIOS DIEGO EMILIO",
      "MEDRANO CERDA EDNA DEL CARMEN",
      "MORA ROMERO ELIZABETH",
      "ROMERO PADILLA ELIZABETH",
      "VAZQUEZ VIDALS ESTELA",
      "AGUILAR LUCAS GABRIELA",
      "HERRERA GUERRERO GENOVEVA",
      "VILCHIS FUENTES HILDA",
      "PAREDES ALONSO HILDA GUADALUPE",
      "JAIME MARTINEZ GARCIA",
      "BRAVO MORENO JAZMIN",
      "ARZATE CORDOVA JESUS",
      "OCEGUERA GAYOSSO JOEL",
      "CORTES RUBIN JOSE ALEJANDRO",
      "BOTELLO CERDA JUANA",
  ]


lista_personal = cargar_personal()

# ---------------------------------------------------------
# 2. Cargar Concentrado de Reportes
# ---------------------------------------------------------
try:
  df_concentrado = conn.read(
      spreadsheet=SPREADSHEET_URL,
      worksheet="CONCENTRADO_DE_REPORTES_DIARIOS",
      ttl="0s",
  )
except Exception:
  df_concentrado = pd.DataFrame(
      columns=[
          "Fecha",
          "Personal de Bienestar",
          "Visitas Realizadas",
          "Periódicos Entregados",
          "Visitas Efectivas",
          "Visitas Servidores de la Salud",
          "Observaciones",
      ]
  )

# ---------------------------------------------------------
# Pestañas de la aplicación
# ---------------------------------------------------------
tab_form, tab_tabla = st.tabs(["📝 Capturar Reporte", "📋 Concentrado General"])

# ---------------------------------------------------------
# TAB 1: FORMULARIO DE CAPTURA
# ---------------------------------------------------------
with tab_form:
  st.subheader("Ingreso de Datos Diarios")

  with st.form("form_territorio", clear_on_submit=True):
    col_a, col_b = st.columns(2)

    with col_a:
      fecha = st.date_input("Fecha de captura", value=date.today())
      personal = st.selectbox("Personal de Bienestar", options=lista_personal
