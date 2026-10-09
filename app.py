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

# Conexión directa con Google Sheets mediante Secrets
conn = st.connection("gsheets", type=GSheetsConnection)

# ---------------------------------------------------------
# 1. Leer nombres desde la pestaña PERSONAL_DE_BIENESTAR (Columna B)
# ---------------------------------------------------------
try:
  df_personal = conn.read(worksheet="PERSONAL_DE_BIENESTAR", ttl="5m")

  # Tomar la Columna B (índice 1 en Pandas)
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

# ---------------------------------------------------------
# 2. Leer registros desde la pestaña CONCENTRADO_DE_REPORTES_DIARIOS
# ---------------------------------------------------------
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
        # Estructurar la nueva fila
        nuevo_registro = pd.DataFrame([{
            "Fecha": fecha.strftime("%Y-%m-%d"),
            "Personal de Bienestar": personal,
            "Visitas Realizadas": int(visitas_realizadas),
            "Periódicos Entregados": int(periodicos_entregados),
            "Visitas Efectivas": int(visitas_efectivas),
            "Visitas Servidores de la Salud": int(visitas_salud),
            "Observaciones": observaciones,
        }])

        # Concatenar con los datos existentes
        df_actualizado = pd.concat(
            [df_concentrado, nuevo_registro], ignore_index=True
        )

        # Escribir la tabla actualizada en Google Sheets
        try:
          conn.update(
              worksheet="CONCENTRADO_DE_REPORTES_DIARIOS", data=df_actualizado
          )
          st.success(
              f"¡Reporte enviado exitosamente a Google Sheets para {personal}!"
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
    # Mostrar la tabla completa
    st.dataframe(df_concentrado, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📈 Totales Acumulados Globales")

    # Asegurar conversión numérica para realizar la suma correctamente
    columnas_metricas = [
        "Visitas Realizadas",
        "Periódicos Entregados",
        "Visitas Efectivas",
        "Visitas Servidores de la Salud",
    ]

    for col in columnas_metricas:
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
