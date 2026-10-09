from datetime import date
import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración de la página
st.set_page_config(
    page_title="Reporte de Territorio", page_icon="📊", layout="wide"
)

st.title("📊 Reporte Diario de Territorio")
st.write(
    "Sistema conectado en tiempo real con Google Sheets (**TERRITORIO**)."
)

# Conectar con Google Sheets usando Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# 1. Leer nombres de la pestaña PERSONAL_DE_BIENESTAR (Columna B)
try:
  df_personal = conn.read(worksheet="PERSONAL_DE_BIENESTAR", ttl="5m")

  # Tomar la columna B (índice 1)
  if df_personal.shape[1] >= 2:
    col_nombres = df_personal.iloc[:, 1]
  else:
    col_nombres = df_personal.iloc[:, 0]

  lista_personal = sorted(
      col_nombres.dropna().astype(str).str.strip().unique().tolist()
  )
except Exception as e:
  st.warning(f"No se pudieron cargar los nombres desde Google Sheets: {e}")
  lista_personal = ["Seleccionar..."]

# 2. Leer registros de la pestaña CONCENTRADO_DE_REPORTES_DIARIOS
try:
  df_concentrado = conn.read(
      worksheet="CONCENTRADO_DE_REPORTES_DIARIOS", ttl="0s"
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

# Pestañas de la aplicación
tab_form, tab_tabla = st.tabs(["📝 Capturar Reporte", "📋 Concentrado General"])

with tab_form:
  st.subheader("Ingreso de Datos")

  with st.form("form_territorio", clear_on_submit=True):
    col_a, col_b = st.columns(2)

    with col_a:
      fecha = st.date_input("Fecha", value=date.today())
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
      nuevo_registro = pd.DataFrame([{
          "Fecha": fecha.strftime("%Y-%m-%d"),
          "Personal de Bienestar": personal,
          "Visitas Realizadas": visitas_realizadas,
          "Periódicos Entregados": periodicos_entregados,
          "Visitas Efectivas": visitas_efectivas,
          "Visitas Servidores de la Salud": visitas_salud,
          "Observaciones": observaciones,
      }])

      df_actualizado = pd.concat(
          [df_concentrado, nuevo_registro], ignore_index=True
      )

      # Actualizar la hoja de Google Sheets en la pestaña del concentrado
      try:
        conn.update(
            worksheet="CONCENTRADO_DE_REPORTES_DIARIOS", data=df_actualizado
        )
        st.success(
            f"¡Reporte enviado exitosamente a Google Sheets para {personal}!"
        )
        st.cache_data.clear()
      except Exception as ex:
        st.error(f"Error al escribir en Google Sheets: {ex}")

with tab_tabla:
  st.subheader("📋 Concentrado General en Tiempo Real")

  if df_concentrado.empty:
    st.info("Aún no se han registrado reportes en el concentrado.")
  else:
    st.dataframe(df_concentrado, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📈 Totales Acumulados")

    # Convertir a formato numérico para sumar correctamente
    for col in [
        "Visitas Realizadas",
        "Periódicos Entregados",
        "Visitas Efectivas",
        "Visitas Servidores de la Salud",
    ]:
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
