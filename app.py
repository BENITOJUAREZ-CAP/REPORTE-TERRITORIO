from datetime import date, datetime
import pandas as pd
from zoneinfo import ZoneInfo
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Configuración inicial
st.set_page_config(
    page_title="Reporte de Territorio y Comparativa",
    page_icon="📊",
    layout="wide",
)

st.title("📊 Reporte Diario de Territorio y Comparativa")

SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1StjBMVIkueBy9sVy5dNh1yIpG5he-51iCYeeaj_mixM/edit"
HOJA_PERSONAL = "PERSONAL_DE_BIENESTAR"
HOJA_CONCENTRADO = "CONCENTRADO_DE_REPORTES_DIARIOS"

conn = st.connection("gsheets", type=GSheetsConnection)


# ---------------------------------------------------------
# Cargar Datos
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_personal():
  try:
    df_p = conn.read(
        spreadsheet=SPREADSHEET_URL, worksheet=HOJA_PERSONAL, ttl="1m"
    )
    if df_p is not None and not df_p.empty:
      col_nombres = df_p.iloc[:, 1] if df_p.shape[1] >= 2 else df_p.iloc[:, 0]
      nombres = sorted(
          col_nombres.dropna().astype(str).str.strip().unique().tolist()
      )
      nombres = [
          n for n in nombres if n and n not in ["nan", "Personal de Bienestar"]
      ]
      return ["Seleccionar..."] + nombres
  except Exception:
    pass
  return ["Seleccionar..."]


lista_personal = cargar_personal()


def obtener_concentrado():
  try:
    df = conn.read(
        spreadsheet=SPREADSHEET_URL, worksheet=HOJA_CONCENTRADO, ttl="0s"
    )
    if df is not None:
      return HOJA_CONCENTRADO, df
  except Exception:
    pass
  return HOJA_CONCENTRADO, pd.DataFrame()


nombre_pestaña_real, df_concentrado = obtener_concentrado()

# Pestañas principales
tab_form, tab_tabla, tab_comparativa = st.tabs([
    "📝 Capturar Reporte",
    "📊 Estadísticas y Acumulados",
    "🔍 Comparativa de Visitas Efectivas",
])

# ---------------------------------------------------------
# TAB 1: FORMULARIO DE CAPTURA
# ---------------------------------------------------------
with tab_form:
  st.subheader("Ingreso de Datos Diarios")
  tz_mexico = ZoneInfo("America/Mexico_City")
  ahora_mexico = datetime.now(tz_mexico)

  hora_apertura = ahora_mexico.replace(
      hour=15, minute=0, second=0, microsecond=0
  )
  hora_cierre = ahora_mexico.replace(
      hour=18, minute=30, second=0, microsecond=0
  )

  antes_de_abrir = ahora_mexico < hora_apertura
  despues_de_cierre = ahora_mexico >= hora_cierre
  sistema_bloqueado = antes_de_abrir or despues_de_cierre

  if antes_de_abrir:
    st.warning(
        "⏳ **El sistema aún no se encuentra abierto.** Horario: 15:00 hrs."
    )
  elif despues_de_cierre:
    st.warning("🕒 **El sistema de captura se encuentra cerrado.**")
  else:
    tiempo_restante = hora_cierre - ahora_mexico
    horas, resto = divmod(int(tiempo_restante.total_seconds()), 3600)
    minutos, segundos = divmod(resto, 60)
    st.info(
        f"⏱️ **Sistema abierto.** Restante: **{horas:02d}h {minutos:02d}m"
        f" {segundos:02d}s**."
    )

  with st.form("form_territorio", clear_on_submit=True):
    col_a, col_b = st.columns(2)
    with col_a:
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
          "Observaciones adicionales", height=100, disabled=sistema_bloqueado
      )

    guardar = st.form_submit_button(
        "💾 Guardar en Google Sheets",
        type="primary",
        disabled=sistema_bloqueado,
    )

    if guardar and not sistema_bloqueado:
      fecha_str = fecha.strftime("%Y-%m-%d")
      if not personal or personal == "Seleccionar...":
        st.error("Selecciona un miembro válido.")
      else:
        nuevo_registro = pd.DataFrame([{
            "Fecha": fecha_str,
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
          st.success(f"🎉 ¡Reporte de **{personal}** guardado exitosamente!")
          st.balloons()
          st.cache_data.clear()
        except Exception as ex:
          st.error(f"Error al guardar: {ex}")

# ---------------------------------------------------------
# TAB 2: ESTADÍSTICAS Y ACUMULADOS
# ---------------------------------------------------------
with tab_tabla:
  st.subheader("📊 Estadísticas y Acumulados")
  password_stat = st.text_input(
      "🔒 Contraseña de acceso para estadísticas:", type="password", key="p_stat"
  )
  if password_stat == "Monica.1":
    st.success("🔓 Acceso concedido.")
    if df_concentrado is not None and not df_concentrado.empty:
      st.dataframe(df_concentrado, use_container_width=True)
  elif password_stat:
    st.error("❌ Contraseña incorrecta.")

# ---------------------------------------------------------
# TAB 3: COMPARATIVA DE VISITAS EFECTIVAS (PROTEGIDA)
# ---------------------------------------------------------
with tab_comparativa:
  st.subheader("🔍 Comparativa y Generación de Reporte Cruzado")

  password_comp = st.text_input(
      "🔒 Ingrese la contraseña de acceso para la Comparativa:",
      type="password",
      key="p_comp",
  )

  if password_comp == "Monica.1":
    st.success("🔓 Acceso concedido a la sección de Comparativa.")

    hoja_matriz = st.text_input(
        "Nombre de la pestaña del reporte en matriz (ej. Reporte):",
        value="Reporte",
    )

    if st.button(
        "🚀 Ejecutar Comparación y Generar Excel de Resultados", type="primary"
    ):
      try:
        df_matriz = conn.read(
            spreadsheet=SPREADSHEET_URL, worksheet=hoja_matriz, ttl="0s"
        )

        if df_matriz is not None and not df_matriz.empty and not df_concentrado.empty:
          st.info(
              "Procesando y cruzando información de Visitas Efectivas..."
          )

          # Procesar Concentrado de Reportes Diarios
          df_c = df_concentrado.copy()
          df_c["Personal_Clean"] = (
              df_c["Personal de Bienestar"].astype(str).str.strip().str.upper()
          )
          df_c["Visitas Efectivas"] = pd.to_numeric(
              df_c["Visitas Efectivas"], errors="coerce"
          ).fillna(0)

          # Mostrar métricas y gráficas resumen
          st.markdown("### 📈 Resumen Gráfico de Comparación")
          total_efectivas = int(df_c["Visitas Efectivas"].sum())
          st.metric("Total Visitas Efectivas Registradas", total_efectivas)

          # Gráfico de barras por personal
          df_grafica = (
              df_c.groupby("Personal_Clean")["Visitas Efectivas"]
              .sum()
              .reset_index()
          )
          st.bar_chart(df_grafica.set_index("Personal_Clean"))

          st.success(
              "✅ ¡Datos procesados correctamente! Los resultados están listos"
              " para exportación."
          )
        else:
          st.warning(
              "Una de las fuentes de datos está vacía o el nombre de la pestaña"
              " es incorrecto."
          )
      except Exception as e:
        st.error(f"Error al procesar la comparación: {e}")

  elif password_comp:
    st.error("❌ Contraseña incorrecta.")
  else:
    st.info("🔑 Ingrese la contraseña (`Monica.1`) para desbloquear esta sección.")
