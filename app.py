import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from supabase import create_client
from datetime import date

st.set_page_config(page_title="Control Financiero", layout="wide", initial_sidebar_state="collapsed")

# Inyección de CSS para simular la apariencia de Tailwind/React
st.markdown("""
<style>
    /* Fondo principal de la app (slate-50) */
    .stApp {
        background-color: #f8fafc;
    }
    
    /* Reducir padding superior de Streamlit y centrar contenido */
    .block-container {
        padding-top: 2rem;
        max-width: 64rem; /* Max-w-6xl */
    }
    
    /* Ocultar el header predeterminado de Streamlit */
    header {visibility: hidden;}
    
    /* Estilizar el contenedor del formulario expandible */
    .streamlit-expanderHeader {
        background-color: white !important;
        border-radius: 0.75rem !important;
        border: 1px solid #f1f5f9 !important;
        color: #334155 !important;
        font-weight: 600 !important;
    }
    
    /* Estilizar el botón principal de guardar */
    .stButton > button {
        background-color: #2563eb !important;
        color: white !important;
        border-radius: 0.75rem !important;
        border: none !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2) !important;
    }
    
    /* Fondo transparente para las alertas de info */
    .stAlert {
        border-radius: 0.75rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Conexión Supabase directa
SUPABASE_URL = "https://uylnumfofwykwjamwtwk.supabase.co"
SUPABASE_KEY = "sb_publishable_-F-3L3EmsN2DGdQ3xLvKgQ_0_DFq1CY"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Diccionario de meses en español
NOMBRES_MESES = {
    "01": "enero", "02": "febrero", "03": "marzo", "04": "abril",
    "05": "mayo", "06": "junio", "07": "julio", "08": "agosto",
    "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
}

# Paleta de colores de la versión React
COLORES_GRAFICOS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#14b8a6', '#f43f5e', '#84cc16', '#0ea5e9', '#d946ef']

def formato_mes_espanol(codigo_periodo):
    """Convierte 'YYYY-MM' en 'mes YYYY' (ej: '2026-09' -> 'septiembre 2026')"""
    if codigo_periodo == "Consolidado Total":
        return "Consolidado Total"
    try:
        anio, mes = codigo_periodo.split("-")
        return f"{NOMBRES_MESES.get(mes, mes)} {anio}".capitalize()
    except Exception:
        return codigo_periodo

@st.cache_data(ttl=60)
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
        st.cache_data.clear() # Limpiar caché para actualizar al instante
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
    if "categoria" in df.columns:
        df["categoria"] = df["categoria"].astype(str).str.strip()

# --- INTERFAZ / HEADER ---
st.markdown("""
<div style="background-color: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 1px 3px 0 rgba(0,0,0,0.1); border: 1px solid #f1f5f9; display: flex; align-items: center; gap: 1.25rem; margin-bottom: 1.5rem;">
    <div style="background-color: #dbeafe; color: #2563eb; padding: 0.85rem; border-radius: 0.75rem; font-size: 1.75rem; display: flex; align-items: center; justify-content: center;">
        💳
    </div>
    <div>
        <h1 style="margin: 0; font-size: 1.75rem; color: #1e293b; line-height: 1.2; font-weight: 700;">Mi Control Financiero</h1>
        <p style="margin: 0; margin-top: 0.25rem; color: #64748b; font-size: 0.95rem;">Gestión de ingresos y egresos en la nube</p>
    </div>
</div>
""", unsafe_allow_html=True)

base_egresos = ["ana", "casa", "comida", "cuotas", "educación", "gustos", "movilidad", "padres", "salud", "trabajo", "vestimenta", "otros"]
base_ingresos = ["sunass", "cas", "gratificación", "cobro de deuda", "otros"]

if not df.empty and "categoria" in df.columns:
    egresos_db = df[df["tipo"].str.lower() == "egreso"]["categoria"].dropna().unique().tolist()
    ingresos_db = df[df["tipo"].str.lower() == "ingreso"]["categoria"].dropna().unique().tolist()
    
    egresos_db_clean = [cat.lower() for cat in egresos_db]
    ingresos_db_clean = [cat.lower() for cat in ingresos_db]
    
    cats_egreso = sorted(list(set([c.capitalize() for c in base_egresos + egresos_db_clean])))
    cats_ingreso = sorted(list(set([c.capitalize() for c in base_ingresos + ingresos_db_clean])))
else:
    cats_egreso = sorted([c.capitalize() for c in base_egresos])
    cats_ingreso = sorted([c.capitalize() for c in base_ingresos])

# Formulario de entrada
with st.expander("➕ Ingresar Nuevo Movimiento", expanded=False):
    st.markdown("<br>", unsafe_allow_html=True)
    tipo = st.radio("Tipo de movimiento", ["Egreso", "Ingreso"], horizontal=True)

    with st.form("nuevo_movimiento", clear_on_submit=True):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_input = st.date_input("Fecha", value=date.today())
            categoria = st.selectbox("Categoría", cats_egreso if tipo == "Egreso" else cats_ingreso)
        with col_f2:
            monto = st.number_input("Monto (S/.)", min_value=0.0, step=1.0, format="%.2f")
            detalle = st.text_input("Detalle", placeholder="Ej. Menú, pasaje, cuota...")

        st.markdown("<br>", unsafe_allow_html=True)
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

st.markdown("<br>", unsafe_allow_html=True)

if not df.empty and "mes_periodo" in df.columns:
    meses_disponibles = sorted(df["mes_periodo"].unique().tolist(), reverse=True)
    opciones_filtro = ["Consolidado Total"] + meses_disponibles
    mes_actual_str = date.today().strftime("%Y-%m")
    
    indice_defecto = opciones_filtro.index(mes_actual_str) if mes_actual_str in opciones_filtro else 0

    col_filtro1, col_filtro2 = st.columns([1, 2])
    with col_filtro1:
        mes_seleccionado = st.selectbox(
            "📅 Periodo:",
            opciones_filtro,
            index=indice_defecto,
            format_func=formato_mes_espanol
        )

    if mes_seleccionado != "Consolidado Total":
        df_filtrado = df[df["mes_periodo"] == mes_seleccionado]
        etiqueta_periodo = formato_mes_espanol(mes_seleccionado)
    else:
        df_filtrado = df
        etiqueta_periodo = "Consolidado Total"
else:
    df_filtrado = df
    mes_seleccionado = "Consolidado Total"
    etiqueta_periodo = "Consolidado Total"

ingresos = df_filtrado[df_filtrado["tipo"].str.lower() == "ingreso"]["monto"].sum() if not df_filtrado.empty else 0.0
egresos = df_filtrado[df_filtrado["tipo"].str.lower() == "egreso"]["monto"].sum() if not df_filtrado.empty else 0.0
disponible = ingresos - egresos

# Tarjetas KPI Estilo React
kpi1, kpi2, kpi3 = st.columns(3)

with kpi1:
    st.markdown(f"""
    <div style="background-color: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #f1f5f9;">
        <p style="margin: 0; color: #64748b; font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Ingresos</p>
        <p style="margin: 0; margin-top: 0.5rem; color: #059669; font-size: 1.875rem; font-weight: 700;">S/ {ingresos:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

with kpi2:
    st.markdown(f"""
    <div style="background-color: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #f1f5f9;">
        <p style="margin: 0; color: #64748b; font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Egresos</p>
        <p style="margin: 0; margin-top: 0.5rem; color: #e11d48; font-size: 1.875rem; font-weight: 700;">S/ {egresos:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

with kpi3:
    color_disponible = "#2563eb" if disponible >= 0 else "#e11d48"
    st.markdown(f"""
    <div style="background-color: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #f1f5f9;">
        <p style="margin: 0; color: #64748b; font-size: 0.875rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em;">Disponible</p>
        <p style="margin: 0; margin-top: 0.5rem; color: {color_disponible}; font-size: 1.875rem; font-weight: 700;">S/ {disponible:,.2f}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

if not df_filtrado.empty and egresos > 0:
    df_egresos = df_filtrado[df_filtrado["tipo"].str.lower() == "egreso"].copy()

    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        if not df_egresos.empty:
            # Envolver el gráfico en una "tarjeta" blanca
            st.markdown('<div style="background-color: white; padding: 1rem; border-radius: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #f1f5f9;">', unsafe_allow_html=True)
            
            fig_donut = px.pie(
                df_egresos,
                values="monto",
                names="categoria",
                hole=0.6,
                title=f"Egresos por Categoría",
                color_discrete_sequence=COLORES_GRAFICOS
            )
            fig_donut.update_traces(textposition='inside', textinfo='percent')
            fig_donut.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#334155', family="sans-serif"),
                margin=dict(t=50, b=20, l=20, r=20),
                title_font=dict(size=18, color='#1e293b'),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5)
            )
            st.plotly_chart(fig_donut, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with col_g2:
        # Importante: Este bloque HTML debe estar pegado a la izquierda sin espacios para que Markdown no lo tome como bloque de código
        st.markdown('<div style="background-color: white; padding: 2.5rem 1.5rem; border-radius: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #f1f5f9; height: 100%; display: flex; flex-direction: column; justify-content: center;">', unsafe_allow_html=True)
        
        porcentaje = min((egresos / ingresos) * 100, 100) if ingresos > 0 else (100 if egresos > 0 else 0)
        color_barra = "#ef4444" if egresos > ingresos else "#3b82f6"
        
        html_barra = f"""
<h3 style="color: #1e293b; margin-top: 0; margin-bottom: 2rem; font-size: 1.125rem; font-family: sans-serif; text-align: center; font-weight: normal;">Egresos vs Ingresos</h3>
<div style="max-width: 400px; margin: 0 auto; width: 100%;">
<div style="display: flex; justify-content: space-between; font-size: 0.875rem; color: #475569; margin-bottom: 0.75rem; font-weight: 500; font-family: sans-serif;">
<span>Egresos: S/ {egresos:,.2f}</span>
<span>Ingresos: S/ {ingresos:,.2f}</span>
</div>
<div style="width: 100%; background-color: #d1fae5; border-radius: 9999px; height: 1.25rem; overflow: hidden; box-shadow: inset 0 2px 4px 0 rgba(0, 0, 0, 0.06);">
<div style="width: {porcentaje:.2f}%; background-color: {color_barra}; height: 100%; border-radius: 9999px; transition: width 1s ease-in-out;"></div>
</div>
<p style="margin-top: 1rem; color: #64748b; font-size: 0.875rem; font-weight: 700; text-align: center; font-family: sans-serif;">
{porcentaje:.1f}% Consumido
</p>
</div>
"""
        st.markdown(html_barra, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    df_cat_totales = df_egresos.groupby("categoria", as_index=False)["monto"].sum()
    df_cat_totales = df_cat_totales.sort_values(by="monto", ascending=False)

    st.markdown('<div style="background-color: white; padding: 1.5rem; border-radius: 1rem; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #f1f5f9;">', unsafe_allow_html=True)
    fig_bar = px.bar(
        df_cat_totales,
        x="categoria",
        y="monto",
        text="monto",
        title=f"Total de Egresos por Categoría",
        labels={"categoria": "", "monto": "Monto (S/.)"},
        color="categoria",
        color_discrete_sequence=COLORES_GRAFICOS
    )
    fig_bar.update_traces(
        texttemplate='S/ %{text:,.2f}',
        textposition='outside',
        cliponaxis=False
    )
    fig_bar.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#334155', family="sans-serif"),
        title_font=dict(size=18, color='#1e293b'),
        xaxis_tickangle=-45,
        showlegend=False,
        margin=dict(t=50, b=20, l=20, r=20),
        yaxis=dict(showgrid=True, gridcolor='#f1f5f9')
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Tabla de Movimientos estéticamente limpia
    st.markdown('<h3 style="color: #1e293b; font-size: 1.25rem; font-family: sans-serif; margin-bottom: 1rem;">Movimientos del Periodo</h3>', unsafe_allow_html=True)
    df_mostrar = df_filtrado[["fecha", "tipo", "categoria", "detalle", "monto"]].copy()
    df_mostrar['fecha'] = df_mostrar['fecha'].dt.strftime("%Y-%m-%d")
    df_mostrar['categoria'] = df_mostrar['categoria'].apply(lambda x: str(x).capitalize())
    df_mostrar['tipo'] = df_mostrar['tipo'].apply(lambda x: str(x).capitalize())
    
    # Mostrar la tabla nativa de Streamlit (que ya tiene un diseño muy limpio en versiones recientes)
    st.dataframe(
        df_mostrar.head(20), 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "fecha": st.column_config.DateColumn("Fecha"),
            "tipo": st.column_config.TextColumn("Tipo"),
            "categoria": st.column_config.TextColumn("Categoría"),
            "detalle": st.column_config.TextColumn("Detalle"),
            "monto": st.column_config.NumberColumn("Monto (S/.)", format="S/ %.2f")
        }
    )
else:
    st.info(f"No hay movimientos registrados para {etiqueta_periodo}.")