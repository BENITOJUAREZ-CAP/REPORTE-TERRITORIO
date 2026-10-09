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

  with st.form("form_territorio", clear_on_submit=True):
    col_a, col_b = st.columns(2)

    with col_a:
      fecha = st.date_input("Fecha de captura", value=date.today())
      personal = st.selectbox("Personal de Bienestar", options=lista_personal)
      visitas_realizadas = st.number_input(
          "1. Visitas Realizadas", min_value=0, step=1, value=0
      )
      periodicos_entregados = st.number_input(
          "2. Periódicos Entregados", min_value=0, step=1, value=0
      )

    with col_b:
      visitas_efectivas = st.number_input(
          "3. Visitas Efectivas", min_value=0, step=1, value=0
      )
      visitas_salud = st.number_input(
          "4. Visitas Servidores de la Salud", min_value=0, step=1, value=0
      )
      observaciones = st.text_area(
          "Observaciones adicionales (Opcional)", height=100
      )

    guardar = st.form_submit_button(
        "💾 Guardar en Google Sheets", type="primary"
    )

    if guardar:
      if not personal or personal == "Seleccionar...":
        st.error(
            "Por favor selecciona un miembro válido del Personal de Bienestar."
        )
      else:
        nuevo_registro = pd.DataFrame([{
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Personal de Bienestar": personal,
            "Visitas Realizadas": int(visitas_realizadas),
            "Periódicos Entregados": int(periodicos_entregados),
            "Visitas Efectivas": int(visitas_efectivas),
            "Visitas Servidores de la Salud": int(visitas_salud),
            "Observaciones": observaciones,
        }])

        df_actualizado = pd.concat(
            [df_concentrado, nuevo_registro], ignore_index=True
        )

        try:
          conn.update(
              spreadsheet=SPREADSHEET_URL,
              worksheet=nombre_pestaña_real,
              data=df_actualizado,
          )
          st.success(
              f"¡Reporte guardado exitosamente en Google Sheets para {personal}!"
          )
          st.cache_data.clear()
          st.rerun()
        except Exception as ex:
          st.error(f"Error al guardar en Google Sheets: {ex}")

# ---------------------------------------------------------
# TAB 2: ESTADÍSTICAS Y ACUMULADOS
# ---------------------------------------------------------
with tab_tabla:
  st.subheader("📊 Estadísticas y
