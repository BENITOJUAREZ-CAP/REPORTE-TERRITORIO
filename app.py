from datetime import date
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración inicial de la página
st.set_page_config(
    page_title="Reporte de Territorio",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Reporte Diario de Territorio")
st.write("Sistema conectado en tiempo real con Google Sheets (**TERRITORIO**).")

# URL exacta de tu hoja de cálculo
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1StjBMVIkueBy9sVy5dNh1yIpG5he-51iCYeeaj_mixM/edit"

# Nombres de las pestañas
HOJA_PERSONAL = "PERSONAL_DE_BIENESTAR"
HOJA_CONCENTRADO = "CONCENTRADO_DE_REPORTES_DIARIOS"

# Inicializar conexión
conn = st.connection("gsheets", type=GSheetsConnection)


# ---------------------------------------------------------
# 1. Cargar catálogo del Personal de Bienestar
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_personal():
    try:
        df_personal = conn.read(
            spreadsheet=SPREADSHEET_URL,
            worksheet=HOJA_PERSONAL,
            ttl="1m",
        )
        col_nombres = (
            df_personal.iloc[:, 1]
            if df_personal.shape[1] >= 2
            else df_personal.iloc[:, 0]
        )
        nombres = sorted(
            col_nombres.dropna().astype(str).str.strip().unique().tolist()
        )
        nombres = [
            n
            for n in nombres
            if n
            not in [
                "PERIODICOS ENTREGADOS",
                "VISITAS EFECTIVAS",
                "VISITAS SERVIDORES DE LA SALUD",
                "0",
                "nan",
                "Personal de Bienestar",
            ]
        ]
        if len(nombres) > 0:
            return nombres
    except Exception as e:
        st.error(f"Error al cargar el personal: {e}")

    return ["Seleccionar..."]


lista_personal = cargar_personal()


# --------------------------------
