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


def normalizar_palabras_nombre(nombre_str):
  if not nombre_str or pd.isna(nombre_str):
    return ""
  palabras = str(nombre_str).upper().strip().split()
  palabras_filtradas = [
      p for p in palabras if p not in ["DE", "DEL", "LA", "LAS", "LOS", "Y"]
  ]
  return " ".join(sorted(palabras_filtradas))


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

tab_form, tab_tabla, tab_comparativa = st.tabs([
    "📝 Capturar Reporte",
    "📊 Estadísticas y Acumulados",
    "🔍 Comparativa por Fecha y Servidor",
])

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

with tab_tabla:
  st.subheader("📊 Estadísticas y Acumulados")
  p_stat = st.text_input("🔒 Contraseña:", type="password", key="ps")
  if p_stat == "Monica.1":
    st.success("Acceso concedido.")
    if not df_concentrado.empty:
      st.dataframe(df_concentrado, use_container_width=True)
  elif p_stat:
    st.error("Contraseña incorrecta.")

with tab_comparativa:
  st.subheader("🔍 Comparativa Directa por Fecha y Servidor")
  p_comp = st.text_input("🔒 Contraseña para Comparativa:", type="password", key="pc")

  if p_comp == "Monica.1":
    st.success("Acceso concedido.")

    hoja_matriz = st.text_input(
        "Nombre o número de la pestaña del Excel Matriz (ej. Reporte o 0):",
        value="Reporte",
    )

    df_matriz = None
    # Intento 1: Leer el nombre escrito por el usuario
    try:
      sheet_val = (
          int(hoja_matriz.strip())
          if hoja_matriz.strip().isdigit()
          else hoja_matriz.strip()
      )
      df_matriz = conn.read(
          spreadsheet=SPREADSHEET_URL, worksheet=sheet_val, ttl="0s"
      )
    except Exception:
      # Intento 2 (Respaldo automático): Si falla, leer directamente la primera pestaña (0)
      try:
        df_matriz = conn.read(
            spreadsheet=SPREADSHEET_URL, worksheet=0, ttl="0s"
        )
      except Exception as err:
        st.error(f"No se pudo leer la hoja matriz de ninguna forma: {err}")

    if df_matriz is not None and not df_matriz.empty:
      fechas_disp = []
      if not df_concentrado.empty and "Fecha" in df_concentrado.columns:
        fechas_disp = sorted(
            df_concentrado["Fecha"].dropna().astype(str).unique().tolist(),
            reverse=True,
        )

      col_a1, col_a2 = st.columns(2)
      with col_a1:
        fecha_elegida = st.selectbox(
            "1. Fecha a comparar:",
            options=fechas_disp if fechas_disp else ["Sin fechas"],
        )
      with col_a2:
        cols_matriz = [str(c).strip() for c in df_matriz.columns]
        idx_default = 0
        for idx, col in enumerate(cols_matriz):
          if fecha_elegida in col:
            idx_default = idx
            break

        columna_fecha_matriz = st.selectbox(
            "2. Columna del día en Excel Bienestar:",
            options=cols_matriz,
            index=min(idx_default, len(cols_matriz) - 1),
        )

      if st.button("🚀 Generar Comparativa", type="primary"):
        try:
          # 1. Concentrado de Territorio
          df_c = df_concentrado.copy()
          df_c["Servidor_Original"] = (
              df_c["Personal de Bienestar"].astype(str).str.strip()
          )
          df_c["Key_Match"] = df_c["Servidor_Original"].apply(
              normalizar_palabras_nombre
          )
          df_c["Visitas Efectivas"] = pd.to_numeric(
              df_c["Visitas Efectivas"], errors="coerce"
          ).fillna(0)

          df_c_dia = df_c[df_c["Fecha"] == fecha_elegida]
          df_c_grouped = (
              df_c_dia.groupby(["Key_Match", "Servidor_Original"])[
                  "Visitas Efectivas"
              ]
              .sum()
              .reset_index()
          )
          df_c_grouped.columns = [
              "Key_Match",
              "Servidor_Territorio",
              "Territorio (Concentrado)",
          ]

          # 2. Excel Matriz Bienestar
          col_nombre = (
              df_matriz.columns[1]
              if len(df_matriz.columns) > 1
              else df_matriz.columns[0]
          )
          df_m = df_matriz[[col_nombre, columna_fecha_matriz]].copy()
          df_m.columns = ["Servidor_Bienestar", "Bienestar (Matriz)"]
          df_m["Servidor_Bienestar"] = (
              df_m["Servidor_Bienestar"].astype(str).str.strip()
          )
          df_m["Key_Match"] = df_m["Servidor_Bienestar"].apply(
              normalizar_palabras_nombre
          )
          df_m["Bienestar (Matriz)"] = pd.to_numeric(
              df_m["Bienestar (Matriz)"], errors="coerce"
          ).fillna(0)

          df_m = df_m[df_m["Key_Match"] != ""]

          # 3. Cruzar reportes
          df_final = pd.merge(
              df_c_grouped, df_m, on="Key_Match", how="outer"
          ).fillna(0)

          df_final["Servidor de la Nación"] = df_final[
              "Servidor_Territorio"
          ].where(
              df_final["Servidor_Territorio"] != 0,
              df_final["Servidor_Bienestar"],
          )

          df_final = df_final[[
              "Servidor de la Nación",
              "Territorio (Concentrado)",
              "Bienestar (Matriz)",
          ]].copy()

          df_final["Territorio (Concentrado)"] = df_final[
              "Territorio (Concentrado)"
          ].astype(int)
          df_final["Bienestar (Matriz)"] = df_final["Bienestar (Matriz)"].astype(
              int
          )
          df_final["Diferencia"] = (
              df_final["Territorio (Concentrado)"]
              - df_final["Bienestar (Matriz)"]
          )

          df_final = df_final.sort_values(
              by="Servidor de la Nación"
          ).reset_index(drop=True)

          # 4. Mostrar Resultados y Gráficas Lado a Lado
          st.markdown("---")
          st.markdown(
              f"### 📈 Comparativa de Visitas Efectivas para el día: **{fecha_elegida}**"
          )

          g1, g2 = st.columns(2)
          with g1:
            st.write("#### 📝 1. Excel Territorio (Concentrado)")
            st.bar_chart(
                df_final.set_index("Servidor de la Nación")[
                    "Territorio (Concentrado)"
                ]
            )
            st.metric(
                "Total Territorio",
                int(df_final["Territorio (Concentrado)"].sum()),
            )

          with g2:
            st.write(f"#### 📄 2. Excel Bienestar ({columna_fecha_matriz})")
            st.bar_chart(
                df_final.set_index("Servidor de la Nación")[
                    "Bienestar (Matriz)"
                ]
            )
            st.metric(
                "Total Bienestar", int(df_final["Bienestar (Matriz)"].sum())
            )

          st.markdown("---")
          st.markdown("### 📋 Tabla Comparativa por Servidor de la Nación")
          st.dataframe(df_final, use_container_width=True)

          # Descarga CSV
          csv_data = df_final.to_csv(index=False).encode("utf-8")
          st.download_button(
              label="📥 Descargar Reporte Comparativo (CSV)",
              data=csv_data,
              file_name=f"COMPARATIVA_{fecha_elegida}.csv",
              mime="text/csv",
          )
        except Exception as err:
          st.error(f"Error al procesar la comparación: {err}")
    else:
      st.info("No se pudieron cargar los datos de la hoja matriz.")

  elif p_comp:
    st.error("Contraseña incorrecta.")
  else:
    st.info("🔑 Ingrese la contraseña `Monica.1`.")
