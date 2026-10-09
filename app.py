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

# URLs de Google Sheets
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1StjBMVIkueBy9sVy5dNh1ylpG5he-51iCYeeaj_mixM/edit"
# Enlace publicado especificando el GID de la pestaña PERSONAL_DE_BIENESTAR (gid=700313474)
PUBLISHED_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQq16I0eaHC0-Mf4hxWnQFIHdxIO11u5CtDmcDGTJ2UZGgv6YhM-x8RJhW31n6dSKBnFEQO9doPoD1y/pub?gid=700313474&single=true&output=csv"

# Conexión con Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)


# ---------------------------------------------------------
# 1. Cargar nombres del Personal de Bienestar
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_personal():
  # Intento 1: Leer directamente la pestaña PERSONAL_DE_BIENESTAR por API
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
  except Exception:
    pass

  # Intento 2: CSV publicado especificando la pestaña de personal (gid=700313474)
  try:
    df_publico = pd.read_csv(PUBLISHED_CSV_URL)
    if df_publico.shape[1] >= 2:
      col_nombres = df_publico.iloc[:, 1]
    else:
      col_nombres = df_publico.iloc[:, 0]

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
  except Exception:
    pass

  # Intento 3: Lista base de respaldo integrada
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
              worksheet="CONCENTRADO_DE_REPORTES_DIARIOS",
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
# TAB 2: CONCENTRADO GENERAL Y TOTALES
# ---------------------------------------------------------
with tab_tabla:
  st.subheader("📋 Concentrado General en Tiempo Real")

  if df_concentrado.empty:
    st.info("Aún no se han registrado reportes en el concentrado.")
  else:
    st.dataframe(df_concentrado, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📈 Totales Acumulados Globales")

    cols_m = [
        "Visitas Realizadas",
        "Periódicos Entregados",
        "Visitas Efectivas",
        "Visitas Servidores de la Salud",
    ]
    for col in cols_m:
      if col in df_concentrado.columns:
        df_concentrado[col] = pd.to_numeric(
            df_concentrado[col], errors="coerce"
        ).fillna(0)

    m1, m2, m3, m4 = st.columns(4)

    if "Visitas Realizadas" in df_concentrado.columns:
      m1.metric(
          "Visitas Realizadas", int(df_concentrado["Visitas Realizadas"].sum())
      )

    if "Periódicos Entregados" in df_concentrado.columns:
      m2.metric(
          "Periódicos Entregados",
          int(df_concentrado["Periódicos Entregados"].sum()),
      )

    if "Visitas Efectivas" in df_concentrado.columns:
      m3.metric(
          "Visitas Efectivas", int(df_concentrado["Visitas Efectivas"].sum())
      )

    if "Visitas Servidores de la Salud" in df_concentrado.columns:
      m4.metric(
          "Visitas Serv. Salud",
          int(df_concentrado["Visitas Servidores de la Salud"].sum()),
      )

    st.markdown("---")
    csv = df_concentrado.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Descargar Copia en Excel / CSV",
        data=csv,
        file_name="CONCENTRADO_DE_REPORTES_DIARIOS.csv",
        mime="text/csv",
    )
