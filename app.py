from datetime import date, datetime
from zoneinfo import ZoneInfo
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
        if df_personal.shape[1] >= 2:
            col_nombres = df_personal.iloc[:, 1]
        else:
            col_nombres = df_personal.iloc[:, 0]

        nombres = sorted(
            col_nombres.dropna().astype(str).str.strip().unique().tolist()
        )
        nombres = [
            n for n in nombres 
            if n and n not in ["nan", "Personal de Bienestar"]
        ]
        if len(nombres) > 0:
            return nombres
    except Exception as e:
        st.error(f"Error al cargar el personal: {e}")

    return ["Seleccionar..."]


lista_personal = cargar_personal()


# ---------------------------------------------------------
# 2. Cargar Concentrado de Reportes
# ---------------------------------------------------------
def obtener_concentrado():
    hojas_posibles = [
        "CONCENTRADO_DE_REPORTES_DIARIOS",
        "CONTENTRADO_DE_REPORTES_DIARIOS",
    ]
    for nombre_hoja in hojas_posibles:
        try:
            df = conn.read(
                spreadsheet=SPREADSHEET_URL,
                worksheet=nombre_hoja,
                ttl="0s",
            )
            return nombre_hoja, df
        except Exception:
            pass
            
    columnas_default = [
        "Fecha",
        "Personal de Bienestar",
        "Visitas Realizadas",
        "Periódicos Entregados",
        "Visitas Efectivas",
        "Visitas Servidores de la Salud",
        "Observaciones",
    ]
    return HOJA_CONCENTRADO, pd.DataFrame(columns=columnas_default)


nombre_pestaña_real, df_concentrado = obtener_concentrado()

# ---------------------------------------------------------
# Pestañas de la aplicación
# ---------------------------------------------------------
tab_form, tab_tabla = st.tabs(
    ["📝 Capturar Reporte", "📊 Estadísticas y Acumulados"]
)

# ---------------------------------------------------------
# TAB 1: FORMULARIO DE CAPTURA
# ---------------------------------------------------------
with tab_form:
    st.subheader("Ingreso de Datos Diarios")

    # Hora de CDMX
    tz_mexico = ZoneInfo("America/Mexico_City")
    ahora_mexico = datetime.now(tz_mexico)
    hora_limite = ahora_mexico.replace(
        hour=18, minute=10, second=0, microsecond=0
    )

    # Bloqueo a las 18:10 hrs
    sistema_bloqueado = ahora_mexico >= hora_limite

    if sistema_bloqueado:
        st.warning(
            "🕒 **El sistema de captura se encuentra cerrado.** "
            "El horario límite de envío es a las **18:10 hrs** (Hora México). "
            "Podrás ingresar nuevos reportes el día de mañana."
        )

    with st.form("form_territorio", clear_on_submit=True):
        col_a, col_b = st.columns(2)

        with col_a:
            fecha = st.date_input(
                "Fecha de captura",
                value=ahora_mexico.date(),
                disabled=True
            )
            personal = st.selectbox(
                "Personal de Bienestar",
                options=lista_personal,
                disabled=sistema_bloqueado,
            )
            vis
