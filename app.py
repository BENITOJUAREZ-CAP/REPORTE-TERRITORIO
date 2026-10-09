from datetime import date, datetime
from zoneinfo import ZoneInfo
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
        n for n in nombres if n and n not in ["nan", "Personal de Bienestar"]
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
  for nombre_hoja in [
      "CONCENTRADO_DE_REPORTES_DIARIOS",
      "CONTENTRADO_DE_REPORTES_DIARIOS",
  ]:
    try:
      df = conn.read(
          spreadsheet=SPREADSHEET_URL,
          worksheet=nombre_hoja,
          ttl="0s",
      )
      return nombre_hoja, df
    except Exception:
      pass
  return HOJA_CONCENTRADO, pd.DataFrame(
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

  # Obtener fecha y hora actual en Zona Horaria de Ciudad de México sin librerías externas
  tz_mexico = ZoneInfo("America/Mexico_City")
  ahora_mexico = datetime.now(tz_mexico)
  hora_limite = ahora_mexico.replace(
      hour=18, minute=10, second=0, microsecond=0
  )

  # Verificar si ya pasó la hora límite (18:10)
  sistema_bloqueado = ahora_mexico >= hora_limite

  if sistema_bloqueado:
    st.warning(
        "🕒 **El sistema de captura se encuentra cerrado.** El horario límite"
        " de envío de reportes es a las **18:10 hrs** (Hora del Centro de"
        " México). Podrás ingresar nuevos reportes el día de mañana."
    )

  with st.form("form_territorio", clear_on_submit=True):
    col_a, col_b = st.columns(2)

    with col_a:
      # Fecha bloqueada para visualización únicamente
      fecha = st.date_input(
          "Fecha de captura", value=ahora_mexico.date(), disabled=True
      )
      personal = st.selectbox(
          "Personal de Bienestar",
          options=lista_personal,
          disabled=sistema_bloqueado,
      )
      visitas_realizadas = st.number_input(
          "1. Visitas Realizadas",
          min_value=0,
          step=1,
          value=0,
          disabled=sistema_bloqueado,
      )
      periodicos_entregados = st.number_input(
          "2. Periódicos Entregados",
          min_value=0,
          step=1,
          value=0,
          disabled=sistema_bloqueado,
      )

    with col_b:
      visitas_efectivas = st.number_input(
          "3. Visitas Efectivas",
          min_value=0,
          step=1,
          value=0,
          disabled=sistema_bloqueado,
      )
      visitas_salud = st.number_input(
          "4. Visitas Servidores de la Salud",
          min_value=0,
          step=1,
          value=0,
          disabled=sistema_bloqueado,
      )
      observaciones = st.text_area(
          "Observaciones adicionales (Opcional)",
          height=100,
          disabled=sistema_bloqueado,
      )

    guardar = st.form_submit_button(
        "💾 Guardar en Google Sheets",
        type="primary",
        disabled=sistema_bloqueado,
    )

    if guardar and not sistema_bloqueado:
      fecha_str = fecha.strftime("%Y-%m-%d")

      if not personal or personal == "Seleccionar...":
        st.error(
            "Por favor selecciona un miembro válido del Personal de Bienestar."
        )
      else:
        # Validación de registro único diario
        ya_registrado = False
        if (
            not df_concentrado.empty
            and "Fecha" in df_concentrado.columns
            and "Personal de Bienestar" in df_concentrado.columns
        ):
          existe = df_concentrado[
              (df_concentrado["Fecha"].astype(str
