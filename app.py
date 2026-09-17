import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from datetime import date

st.set_page_config(page_title="Control Financiero", layout="wide", initial_sidebar_state="collapsed")

# Conexión Supabase directa
SUPABASE_URL = "https://uylnumfofwykwjamwtwk.supabase.co"
SUPABASE_KEY = "sb_publishable_-F-3L3EmsN2DGdQ3xLvKgQ_0_DFq1CY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def cargar_datos():
    try:
        res = supabase.table("movimientos").select("*").order("fecha", desc=True).execute()
        df_raw = pd.DataFrame(res.data)
        if df_raw.empty:
            return pd.DataFrame(columns=["fecha", "tipo", "categoria", "detalle", "monto"])
        return df_raw
    except Exception as e:
        st.error(f"Error al leer base de datos: {e}")
        return pd.DataFrame(columns=["fecha", "tipo", "categoria", "detalle", "monto"])

def guardar_registro(fila):
    try:
        supabase.table("movimientos").insert(fila).execute()
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        return False

df = cargar_datos()

# Formateo y procesamiento
if not df.empty and "fecha" in df.columns:
    df["fecha"] = pd.to_datetime(df["fecha"], errors="coerce")
    df = df.dropna(subset=["fecha"])
    df["mes_periodo"] = df["fecha"].dt.strftime("%Y-%m")
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0.0)

# --- INTERFAZ ---
st.title("💳 Mi Control Financiero")

# Formulario de entrada
with st.expander("➕ Ingresar Movimiento", expanded=False):
    tipo = st.radio("Tipo de movimiento", ["Egreso", "Ingreso"], horizontal=True)

    # Categorías base mínimas aseguradas (incluyendo 'ana')
base_egresos = ["ana", "casa", "comida", "cuotas", "educación", "gustos", "movilidad", "Padres", "salud", "trabajo", "Vestimenta", "otros"]
base_ingresos = ["Sunass", "CAS", "gratificación", "cobro de deuda", "otros"]

# Extraer categorías existentes en el histórico para que nunca falte ninguna
if not df.empty and "categoria" in df.columns:
    egresos_db = df[df["tipo"].str.lower() == "egreso"]["categoria"].dropna().unique().tolist()
    ingresos_db = df[df["tipo"].str.lower() == "ingreso"]["categoria"].dropna().unique().tolist()
    cats_egreso = sorted(list(set(base_egresos + egresos_db)))
    cats_ingreso = sorted(list(set(base_ingresos + ingresos_db)))
else:
    cats_egreso = sorted(base_egresos)
    cats_ingreso = sorted(base_ingresos)"otros"]

    with st.form("nuevo_movimiento", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_input = st.date_input("Fecha", value=date.today())
            categoria = st.selectbox("Categoría", cats_egreso if tipo == "Egreso" else cats_ingreso)
        with col_f2:
            monto = st.number_input("Monto (S/.)", min_value=0.0, step=1.0, format="%.2f")
            detalle = st.text_input("Detalle", placeholder="Ej. Menú, luz, cuota...")

        btn_guardar = st.form_submit_button("Guardar en el acto")

        if btn_guardar:
            if monto > 0:
                payload = {
                    "fecha": str(fecha_input),
                    "tipo": tipo,
                    "categoria": categoria,
                    "detalle": detalle,
                    "monto": float(monto)
                }
                if guardar_registro(payload):
                    st.success("¡Guardado al instante en la nube!")
                    st.rerun()
            else:
                st.error("El monto debe ser mayor a 0")

st.markdown("---")

# --- FILTRO MENSUAL ---
if not df.empty and "mes_periodo" in df.columns:
    st.subheader("📊 Resumen Financiero")
    meses_disponibles = sorted(df["mes_periodo"].unique().tolist(), reverse=True)
    opciones_filtro = ["Consolidado Total"] + meses_disponibles
    mes_seleccionado = st.selectbox("📅 Selecciona el periodo a visualizar:", opciones_filtro)

    if mes_seleccionado != "Consolidado Total":
        df_filtrado = df[df["mes_periodo"] == mes_seleccionado]
    else:
        df_filtrado = df
else:
    df_filtrado = df
    mes_seleccionado = "Consolidado Total"

# --- KPIs ---
ingresos = df_filtrado[df_filtrado["tipo"].str.lower() == "ingreso"]["monto"].sum() if not df_filtrado.empty else 0.0
egresos = df_filtrado[df_filtrado["tipo"].str.lower() == "egreso"]["monto"].sum() if not df_filtrado.empty else 0.0
disponible = ingresos - egresos

kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Ingresos", f"S/ {ingresos:,.2f}")
kpi2.metric("Egresos", f"S/ {egresos:,.2f}")
kpi3.metric("Disponible", f"S/ {disponible:,.2f}", delta=f"{disponible:,.2f}")

# --- GRÁFICOS ---
if not df_filtrado.empty and egresos > 0:
    st.markdown("---")
    df_egresos = df_filtrado[df_filtrado["tipo"].str.lower() == "egreso"]

    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if not df_egresos.empty:
            fig_donut = px.pie(
                df_egresos,
                values="monto",
                names="categoria",
                hole=0.55,
                title=f"Egresos por Categoría ({mes_seleccionado})"
            )
            st.plotly_chart(fig_donut, width="stretch")

    with col_g2:
        tope = max(ingresos, egresos, 1.0)
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=egresos,
            title={'text': "Egresos vs Ingresos"},
            gauge={
                'axis': {'range': [0, tope]},
                'bar': {'color': "#d90429"},
                'threshold': {
                    'line': {'color': "#2ec4b6", 'width': 4},
                    'thickness': 0.8,
                    'value': ingresos
                }
            }
        ))
        st.plotly_chart(fig_gauge, width="stretch")

    st.markdown("### Movimientos Recientes")
    df_mostrar = df_filtrado[["fecha", "tipo", "categoria", "detalle", "monto"]].copy()
    df_mostrar['fecha'] = df_mostrar['fecha'].dt.strftime("%Y-%m-%d")
    st.dataframe(df_mostrar.head(15), width="stretch")
else:
    st.info("No hay registros en este periodo.")