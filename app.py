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
# TAB 2: CONCENTRADO GENERAL Y ESTADÍSTICAS
# ---------------------------------------------------------
with tab_tabla:
  st.subheader("📋 Concentrado General y Estadísticas")

  # Campo para contraseña de protección
  password = st.text_input(
      "🔒 Ingrese la contraseña de acceso para ver el concentrado:",
      type="password",
  )

  if password == "Monica.1":
    st.success("🔓 Acceso concedido.")

    if df_concentrado.empty:
      st.info("Aún no se han registrado reportes en el concentrado.")
    else:
      # Convertir columnas cuantitativas a valores numéricos
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

      # 1. Tabla General de Registros
      st.markdown("### 📄 Registros del Concentrado")
      st.dataframe(df_concentrado, use_container_width=True)

      st.markdown("---")

      # 2. Estadísticas Acumuladas Globales
      st.markdown("### 📈 Totales Acumulados Globales")
      m1, m2, m3, m4 = st.columns(4)

      if "Visitas Realizadas" in df_concentrado.columns:
        m1.metric(
            "Visitas Realizadas",
            int(df_concentrado["Visitas Realizadas"].sum()),
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

      # 3. Estadísticas Desglosadas por Día
      st.markdown("### 📅 Estadísticas Desglosadas por Día")

      if "Fecha" in df_concentrado.columns:
        cols_existentes = [
            col for col in cols_m if col in df_concentrado.columns
        ]
        df_diario = (
            df_concentrado.groupby("Fecha")[cols_existentes]
            .sum()
            .reset_index()
        )
        st.dataframe(df_diario, use_container_width=True)

        st.markdown("#### 📊 Gráfico de Comparación Diaria")
        st.bar_chart(df_diario.set_index("Fecha"))

      st.markdown("---")

      # 4. Descarga de Copia en CSV
      csv = df_concentrado.to_csv(index=False).encode("utf-8")
      st.download_button(
          label="📥 Descargar Copia en Excel / CSV",
          data=csv,
          file_name="CONCENTRADO_DE_REPORTES_DIARIOS.csv",
          mime="text/csv",
      )

  elif password:
    st.error("❌ Contraseña incorrecta. Intente de nuevo.")
  else:
    st.info(
        "🔑 Por favor ingrese la contraseña para acceder a la información de"
        " esta sección."
    )
