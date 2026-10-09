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
    if df_personal is not None and not df_personal.empty:
      if df_personal.shape[1] >= 2:
        col_nombres = df_personal.iloc[:, 1]
      else:
        col_nombres = df_personal.iloc[:, 0]

      nombres = sorted(
          col_nombres.dropna().astype(str).str.strip().unique().tolist()
      )
      nombres = [
          n for n in nombres if n and n not in ["nan", "Personal de Bienestar"]
      ]
      if len(nombres) > 0:
        return ["Seleccionar..."] + nombres
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
      if df is not None:
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

  # Hora actual en CDMX
  tz_mexico = ZoneInfo("America/Mexico_City")
  ahora_mexico = datetime.now(tz_mexico)

  # Definir horario de apertura (15:00) y cierre (18:10)
  hora_apertura = ahora_mexico.replace(
      hour=15, minute=0, second=0, microsecond=0
  )
  hora_cierre = ahora_mexico.replace(
      hour=18, minute=10, second=0, microsecond=0
  )

  # Validar estados del sistema
  antes_de_abrir = ahora_mexico < hora_apertura
  despues_de_cierre = ahora_mexico >= hora_cierre
  sistema_bloqueado = antes_de_abrir or despues_de_cierre

  if antes_de_abrir:
    st.warning(
        "⏳ **El sistema aún no se encuentra abierto.** El horario de captura"
        " inicia a las **15:00 hrs** (Hora México)."
    )
  elif despues_de_cierre:
    st.warning(
        "🕒 **El sistema de captura se encuentra cerrado.** El horario límite"
        " de envío concluyó a las **18:10 hrs** (Hora México). Podrás ingresar"
        " nuevos reportes el día de mañana."
    )
  else:
    # Mostrar contador dinámico de tiempo restante para el cierre
    tiempo_restante = hora_cierre - ahora_mexico
    horas, resto = divmod(int(tiempo_restante.total_seconds()), 3600)
    minutos, segundos = divmod(resto, 60)
    st.info(
        f"⏱️ **Sistema abierto.** Tiempo restante para el cierre: **{horas:02d}"
        f" horas, {minutos:02d} minutos, {segundos:02d} segundos**."
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
        # Verificar si ya existe registro para hoy
        ya_registrado = False
        if (
            df_concentrado is not None
            and not df_concentrado.empty
            and "Fecha" in df_concentrado.columns
            and "Personal de Bienestar" in df_concentrado.columns
        ):
          col_f = df_concentrado["Fecha"].astype(str).str.strip()
          col_p = (
              df_concentrado["Personal de Bienestar"].astype(str).str.strip()
          )

          filtro = (col_f == fecha_str) & (col_p == str(personal).strip())
          if not df_concentrado[filtro].empty:
            ya_registrado = True

        if ya_registrado:
          st.warning(
              f"⚠️ **{personal}** ya registró su reporte para la fecha"
              f" **{fecha_str}**. Solo se permite un envío por día."
          )
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
            # Mensaje destacado de guardado exitoso
            st.success(
                f"🎉 ¡GUARDADO EXITOSAMENTE! El reporte de **{personal}** se ha"
                " registrado correctamente en Google Sheets."
            )
            st.balloons()
            st.cache_data.clear()
          except Exception as ex:
            st.error(f"Error al guardar en Google Sheets: {ex}")

# ---------------------------------------------------------
# TAB 2: ESTADÍSTICAS Y ACUMULADOS
# ---------------------------------------------------------
with tab_tabla:
  st.subheader("📊 Estadísticas y Acumulados")

  password = st.text_input(
      "🔒 Ingrese la contraseña de acceso para ver las estadísticas:",
      type="password",
  )

  if password == "Monica.1":
    st.success("🔓 Acceso concedido.")

    if df_concentrado is None or df_concentrado.empty:
      st.info("Aún no se han registrado reportes en el concentrado.")
    else:
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

      st.markdown("### 📅 Estadísticas Desglosadas por Día")

      if "Fecha" in df_concentrado.columns:
        cols_existentes = [c for c in cols_m if c in df_concentrado.columns]
        df_diario = (
            df_concentrado.groupby("Fecha")[cols_existentes]
            .sum()
            .reset_index()
        )
        st.dataframe(df_diario, use_container_width=True)

        st.markdown("#### 📊 Gráfico de Comparación Diaria")
        st.bar_chart(df_diario.set_index("Fecha"))

      st.markdown("---")

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
    st.info("🔑 Por favor ingrese la contraseña para acceder a esta sección.")
