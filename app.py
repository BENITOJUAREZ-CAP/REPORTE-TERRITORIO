from datetime import date, datetime
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
# Cargar Personal
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
      return ["Seleccionar..."] + [
          n for n in nombres if n and n != "nan" and n != "Personal de Bienestar"
      ]
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
      return df
  except Exception:
    pass
  return pd.DataFrame()


df_concentrado = obtener_concentrado()

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
  sistema_bloqueado = not (hora_apertura <= ahora_mexico < hora_cierre)

  if ahora_mexico < hora_apertura:
    st.warning("⏳ El sistema abrirá a las 15:00 hrs.")
  elif ahora_mexico >= hora_cierre:
    st.warning("🕒 El sistema de captura se encuentra cerrado.")
  else:
    st.info("⏱️ Sistema abierto para captura.")

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
          "Visitas Realizadas", min_value=0, step=1, disabled=sistema_bloqueado
      )
      periodicos_entregados = st.number_input(
          "Periódicos Entregados",
          min_value=0,
          step=1,
          disabled=sistema_bloqueado,
      )
    with col_b:
      visitas_efectivas = st.number_input(
          "Visitas Efectivas", min_value=0, step=1, disabled=sistema_bloqueado
      )
      visitas_salud = st.number_input(
          "Visitas Servidores de la Salud",
          min_value=0,
          step=1,
          disabled=sistema_bloqueado,
      )
      observaciones = st.text_area(
          "Observaciones", height=100, disabled=sistema_bloqueado
      )

    guardar = st.form_submit_button(
        "💾 Guardar", type="primary", disabled=sistema_bloqueado
    )

    if guardar and not sistema_bloqueado:
      if not personal or personal == "Seleccionar...":
        st.error("Selecciona un nombre válido.")
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
        df_act = pd.concat([df_concentrado, nuevo_registro], ignore_index=True)
        try:
          conn.update(
              spreadsheet=SPREADSHEET_URL,
              worksheet=HOJA_CONCENTRADO,
              data=df_act,
          )
          st.success("🎉 ¡Guardado exitosamente!")
          st.balloons()
          st.cache_data.clear()
        except Exception as e:
          st.error(f"Error al guardar: {e}")

# ---------------------------------------------------------
# TAB 2: ESTADÍSTICAS Y ACUMULADOS
# ---------------------------------------------------------
with tab_tabla:
  st.subheader("📊 Estadísticas y Acumulados")
  p_stat = st.text_input("🔒 Contraseña:", type="password", key="ps")
  if p_stat == "Monica.1":
    st.success("Acceso concedido.")
    if not df_concentrado.empty:
      st.dataframe(df_concentrado, use_container_width=True)
  elif p_stat:
    st.error("Contraseña incorrecta.")

# ---------------------------------------------------------
# TAB 3: COMPARATIVA (PROTEGIDA)
# ---------------------------------------------------------
with tab_comparativa:
  st.subheader("🔍 Comparativa de Visitas Efectivas por Día")
  p_comp = st.text_input("🔒 Contraseña para Comparativa:", type="password", key="pc")

  if p_comp == "Monica.1":
    st.success("Acceso concedido.")

    hoja_matriz = st.text_input("Nombre de la pestaña matriz:", value="Reporte")

    df_matriz = None
    try:
      df_matriz = conn.read(
          spreadsheet=SPREADSHEET_URL, worksheet=hoja_matriz.strip(), ttl="0s"
      )
    except Exception:
      try:
        df_matriz = conn.read(
            spreadsheet=SPREADSHEET_URL, worksheet=0, ttl="0s"
        )
      except Exception:
        pass

    if df_matriz is not None and not df_matriz.empty:
      # Fechas disponibles en el Concentrado
      fechas_disp = []
      if not df_concentrado.empty and "Fecha" in df_concentrado.columns:
        fechas_disp = sorted(
            df_concentrado["Fecha"].dropna().astype(str).unique().tolist(),
            reverse=True,
        )

      cols = list(df_matriz.columns)

      c1, c2 = st.columns(2)
      with c1:
        f_sel = st.selectbox(
            "📅 Fecha (Concentrado Diario):",
            options=fechas_disp if fechas_disp else ["Sin fechas"],
        )
      with c2:
        col_idx = st.selectbox(
            "📊 Columna en la Matriz (Día):",
            options=range(len(cols)),
            format_func=lambda i: f"Columna {i+1}: {cols[i]}",
            index=min(5, len(cols) - 1),  # Apunta por defecto cerca de la columna F
        )

      if st.button("🚀 Ejecutar Comparativa", type="primary"):
        try:
          # 1. Agrupar concentrado por día
          df_c = df_concentrado.copy()
          df_c["Personal_Clean"] = (
              df_c["Personal de Bienestar"].astype(str).str.strip().str.upper()
          )
          df_c["Visitas Efectivas"] = pd.to_numeric(
              df_c["Visitas Efectivas"], errors="coerce"
          ).fillna(0)

          df_c_dia = df_c[df_c["Fecha"] == f_sel]
          df_c_grouped = (
              df_c_dia.groupby("Personal_Clean")["Visitas Efectivas"]
              .sum()
              .reset_index()
          )

          # 2. Extraer datos del Excel Matriz por posición de columna
          # Columna 1 (índice 1 o 0) para el nombre, y col_idx para el valor
          df_m = df_matriz.iloc[:, [1, col_idx]].copy()
          df_m.columns = ["Personal_Clean", "Efectivas_Matriz"]
          df_m["Personal_Clean"] = (
              df_m["Personal_Clean"].astype(str).str.strip().str.upper()
          )
          df_m["Efectivas_Matriz"] = pd.to_numeric(
              df_m["Efectivas_Matriz"], errors="coerce"
          ).fillna(0)

          # 3. Cruzar la información
          df_final = pd.merge(
              df_c_grouped, df_m, on="Personal_Clean", how="outer"
          ).fillna(0)
          df_final.columns = [
              "Servidor de la Nación",
              "Efectivas (Concentrado)",
              "Efectivas (Matriz)",
          ]
          df_final["Diferencia"] = (
              df_final["Efectivas (Concentrado)"]
              - df_final["Efectivas (Matriz)"]
          )

          # 4. Mostrar Gráficas Lado a Lado
          st.markdown("---")
          st.markdown(f"### 📈 Resultados para el día: **{f_sel}**")

          gc1, gc2 = st.columns(2)
          with gc1:
            st.write("#### 📝 1. Concentrado Diario")
            st.bar_chart(
                df_final.set_index("Servidor de la Nación")[
                    "Efectivas (Concentrado)"
                ]
            )
            st.metric(
                "Total Concentrado",
                int(df_final["Efectivas (Concentrado)"].sum()),
            )

          with gc2:
            st.write(f"#### 📄 2. Excel Matriz ({cols[col_idx]})")
            st.bar_chart(
                df_final.set_index("Servidor de la Nación")[
                    "Efectivas (Matriz)"
                ]
            )
            st.metric(
                "Total Matriz", int(df_final["Efectivas (Matriz)"].sum())
            )

          st.markdown("---")
          st.markdown("### 📋 Tabla Detallada")
          st.dataframe(df_final, use_container_width=True)

          # Descarga CSV
          csv_data = df_final.to_csv(index=False).encode("utf-8")
          st.download_button(
              label="📥 Descargar Reporte Comparativo (CSV)",
              data=csv_data,
              file_name=f"COMPARATIVA_{f_sel}.csv",
              mime="text/csv",
          )
        except Exception as err:
          st.error(f"Error al procesar la comparación: {err}")
    else:
      st.info("No se pudo leer la hoja matriz.")

  elif p_comp:
    st.error("Contraseña incorrecta.")
  else:
    st.info("🔑 Ingrese la contraseña `Monica.1`.")
