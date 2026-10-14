from datetime import date, datetime
import re
from zoneinfo import ZoneInfo
import pandas as pd
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
# TAB 3: COMPARATIVA DE VISITAS EFECTIVAS POR DÍA (PROTEGIDA)
# ---------------------------------------------------------
with tab_comparativa:
  st.subheader("🔍 Comparativa de Visitas Efectivas por Día")

  password_comp = st.text_input(
      "🔒 Ingrese la contraseña de acceso para la Comparativa:",
      type="password",
      key="p_comp",
  )

  if password_comp == "Monica.1":
    st.success("🔓 Acceso concedido a la sección de Comparativa.")

    hoja_matriz_input = st.text_input(
        "Pestaña del reporte matriz horizontal:",
        value="Reporte",
    )

    df_matriz_raw = None
    try:
      df_matriz_raw = conn.read(
          spreadsheet=SPREADSHEET_URL,
          worksheet=hoja_matriz_input.strip(),
          ttl="0s",
          header=None,  # Leer sin asumirlos como encabezado para encontrar la fila real
      )
    except Exception:
      try:
        df_matriz_raw = conn.read(
            spreadsheet=SPREADSHEET_URL, worksheet=0, ttl="0s", header=None
        )
      except Exception:
        pass

    if df_matriz_raw is not None and not df_matriz_raw.empty:
      # Buscar la fila que contiene las columnas de fechas
      hdr_idx = 0
      for idx, row in df_matriz_raw.iterrows():
        row_str = " ".join(row.dropna().astype(str))
        if any(
            d in row_str.lower()
            for d in ["lunes", "martes", "miércoles", "miercoles", "jueves", "viernes", "sábado", "sabado", "domingo"]
        ):
          hdr_idx = idx
          break

      # Reestructurar la matriz usando la fila correcta como encabezado
      headers = df_matriz_raw.iloc[hdr_idx].values
      df_matriz = df_matriz_raw.iloc[hdr_idx + 1 :].copy()
      df_matriz.columns = [str(h).strip() for h in headers]

      # Procesar y normalizar fechas del Concentrado
      df_c = df_concentrado.copy() if df_concentrado is not None else pd.DataFrame()
      fechas_disponibles = []
      if not df_c.empty and "Fecha" in df_c.columns:
        df_c["Visitas Efectivas"] = pd.to_numeric(
            df_c["Visitas Efectivas"], errors="coerce"
        ).fillna(0)
        df_c["Personal_Clean"] = (
            df_c["Personal de Bienestar"].astype(str).str.strip().str.upper()
        )
        fechas_disponibles = sorted(
            df_c["Fecha"].dropna().astype(str).str.strip().unique().tolist(),
            reverse=True,
        )

      cols_matriz = [c for c in df_matriz.columns if c and c.lower() != "nan"]
      col_persona_matriz = cols_matriz[0]
      for c in cols_matriz:
        if "servidor" in c.lower() or "personal" in c.lower() or "nombre" in c.lower():
          col_persona_matriz = c
          break

      cols_fechas_matriz = [
          c
          for c in cols_matriz
          if c
          not in [
              col_persona_matriz,
              "Dependencia",
              "Visitas totales",
              "Visitas del periodo",
              "None",
          ]
      ]

      col_fecha_sel, col_matriz_sel = st.columns(2)
      with col_fecha_sel:
        fecha_filtro = st.selectbox(
            "📅 Selecciona el día a comparar (Concentrado):",
            options=fechas_disponibles if fechas_disponibles else ["Sin fechas"],
        )
      with col_matriz_sel:
        col_columna_matriz = st.selectbox(
            "📊 Selecciona la columna del Día equivalente (Excel Matriz):",
            options=cols_fechas_matriz if cols_fechas_matriz else cols_matriz,
        )

      if st.button("🚀 Comparar Visitas Efectivas del Día", type="primary"):
        # 1. Filtrar Concentrado
        df_c_dia = df_c[df_c["Fecha"] == fecha_filtro].copy() if not df_c.empty else pd.DataFrame()
        df_c_grouped = (
            df_c_dia.groupby("Personal_Clean")["Visitas Efectivas"]
            .sum()
            .reset_index()
        )

        # 2. Filtrar Matriz Horizontal
        df_m = df_matriz[[col_persona_matriz, col_columna_matriz]].copy()
        df_m.columns = ["Personal_Clean", "Efectivas_Matriz"]
        df_m["Personal_Clean"] = (
            df_m["Personal_Clean"].astype(str).str.strip().str.upper()
        )
        df_m["Efectivas_Matriz"] = pd.to_numeric(
            df_m["Efectivas_Matriz"], errors="coerce"
        ).fillna(0)

        # 3. Unir ambos datasets
        df_cruse = pd.merge(
            df_c_grouped, df_m, on="Personal_Clean", how="outer"
        ).fillna(0)
        df_cruse.columns = [
            "Personal de Bienestar",
            "Efectivas (Concentrado)",
            "Efectivas (Matriz)",
        ]
        df_cruse["Diferencia"] = (
            df_cruse["Efectivas (Concentrado)"] - df_cruse["Efectivas (Matriz)"]
        )

        # 4. Mostrar Gráficas
        st.markdown("---")
        st.markdown(
            f"### 📊 Comparativa de Visitas Efectivas para el día: **{fecha_filtro}**"
        )

        g1, g2 = st.columns(2)
        with g1:
          st.write("#### 📝 1. Concentrado Diario (Streamlit)")
          st.bar_chart(
              df_cruse.set_index("Personal de Bienestar")[
                  "Efectivas (Concentrado)"
              ]
          )
          st.metric(
              "Total Efectivas Concentrado",
              int(df_cruse["Efectivas (Concentrado)"].sum()),
          )

        with g2:
          st.write(f"#### 📄 2. Excel Matriz ({col_columna_matriz})")
          st.bar_chart(
              df_cruse.set_index("Personal de Bienestar")["Efectivas (Matriz)"]
          )
          st.metric(
              "Total Efectivas Matriz", int(df_cruse["Efectivas (Matriz)"].sum())
          )

        st.markdown("---")
        st.markdown("### 📋 Tabla Comparativa Detallada por Persona")
        st.dataframe(df_cruse, use_container_width=True)

        # Botón de Descarga
        csv_comp = df_cruse.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar Comparativa del Día en Excel / CSV",
            data=csv_comp,
            file_name=f"COMPARATIVA_EFECTIVAS_{fecha_filtro}.csv",
            mime="text/csv",
        )
    else:
      st.info("No se pudieron cargar los datos de la hoja matriz.")

  elif password_comp:
    st.error("❌ Contraseña incorrecta.")
  else:
    st.info("🔑 Ingrese la contraseña (`Monica.1`) para desbloquear esta sección.")
