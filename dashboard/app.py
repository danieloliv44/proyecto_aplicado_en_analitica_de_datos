import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.insurance import cotizar_seguro, municipios_disponibles, anios_disponibles


st.set_page_config(
    page_title="Simulador de Seguro Indexado",
    page_icon="🌱",
    layout="wide",
)


# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    """
    <style>
    .stApp {
        background-color: #f5f7fb;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }

    .main-title {
        font-size: 34px;
        font-weight: 850;
        color: #172033;
        margin-bottom: 0px;
    }

    .subtitle {
        font-size: 16px;
        color: #667085;
        margin-bottom: 22px;
    }

    .section-title {
        font-size: 20px;
        font-weight: 800;
        color: #1f2937;
        margin-top: 16px;
        margin-bottom: 12px;
    }

    .card {
        background-color: white;
        border-radius: 18px;
        padding: 20px 22px;
        box-shadow: 0 6px 18px rgba(15,23,42,0.07);
        border: 1px solid #e9edf5;
        min-height: 128px;
    }

    .kpi-label {
        color: #667085;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 6px;
    }

    .kpi-value {
        font-size: 28px;
        font-weight: 850;
        margin-bottom: 2px;
    }

    .kpi-small {
        font-size: 12.5px;
        color: #667085;
    }

    .risk-high {
        background-color: #fde2e2;
        color: #b91c1c;
        border: 1px solid #fecaca;
    }

    .risk-medium {
        background-color: #fff3d6;
        color: #b45309;
        border: 1px solid #fed7aa;
    }

    .risk-low {
        background-color: #dcfce7;
        color: #15803d;
        border: 1px solid #bbf7d0;
    }

    .status-box {
        border-radius: 16px;
        padding: 18px;
        font-size: 18px;
        font-weight: 850;
        text-align: center;
        margin-bottom: 14px;
    }

    .interpretation {
        background-color: white;
        border-radius: 18px;
        padding: 22px;
        border-left: 6px solid #0e7490;
        box-shadow: 0 6px 18px rgba(15,23,42,0.07);
        line-height: 1.45;
    }

    .note-box {
        background-color: #eef6ff;
        border: 1px solid #bfdbfe;
        border-radius: 14px;
        padding: 14px 16px;
        color: #1e3a8a;
        font-size: 14px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 24px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def get_value(result, *keys, default=0):
    for key in keys:
        if key in result and result[key] is not None:
            return result[key]
    return default


def money_usd(x):
    try:
        return f"${float(x):,.0f} USD"
    except Exception:
        return str(x)


def number(x, decimals=2):
    try:
        return f"{float(x):,.{decimals}f}"
    except Exception:
        return str(x)


def pct(x):
    try:
        return f"{float(x) * 100:,.1f}%"
    except Exception:
        return str(x)


def risk_class(nivel):
    nivel = str(nivel).lower()
    if "alto" in nivel:
        return "risk-high"
    if "medio" in nivel:
        return "risk-medium"
    return "risk-low"


def risk_color(nivel):
    nivel = str(nivel).lower()
    if "alto" in nivel:
        return "#dc2626"
    if "medio" in nivel:
        return "#f59e0b"
    return "#16a34a"


def risk_status(nivel):
    nivel = str(nivel).lower()
    if "alto" in nivel:
        return "REGIÓN DE ALTA EXPOSICIÓN"
    if "medio" in nivel:
        return "REGIÓN ASEGURABLE CON MONITOREO"
    return "REGIÓN ASEGURABLE"


def interpretation_text(result):
    nivel = get_value(result, "nivel_riesgo", default="No disponible")
    prob = get_value(result, "probabilidad_perdida", default=0)
    indice = get_value(result, "indice_riesgo", default=0)
    payout = get_value(result, "payout", default=0)

    if str(nivel).lower() == "alto":
        return (
            f"Para el municipio seleccionado, el modelo estima un nivel de riesgo alto, "
            f"con índice de riesgo de {number(indice, 2)} y probabilidad de pérdida de {pct(prob)}. "
            f"Esto indica una exposición importante a condiciones climáticas adversas. "
            f"El payout estimado es de {pct(payout)}, por lo que la indemnización esperada "
            f"puede ser relevante frente al monto asegurado."
        )

    if str(nivel).lower() == "medio":
        return (
            f"Para el municipio seleccionado, el modelo estima un nivel de riesgo medio, "
            f"con índice de riesgo de {number(indice, 2)} y probabilidad de pérdida de {pct(prob)}. "
            f"El perfil es asegurable, aunque se recomienda monitorear la evolución del índice climático "
            f"y validar periódicamente las condiciones de exposición."
        )

    return (
        f"Para el municipio seleccionado, el modelo estima un nivel de riesgo bajo, "
        f"con índice de riesgo de {number(indice, 2)} y probabilidad de pérdida de {pct(prob)}. "
        f"Las condiciones proyectadas son relativamente favorables para la cotización del seguro."
    )


def build_financial_chart(result):
    monto = get_value(result, "monto_asegurado_usd", "monto_asegurado_USD")
    prima = get_value(result, "prima_comercial_usd", "prima_comercial_USD")
    indemnizacion = get_value(result, "indemnizacion_estimada_usd", "indemnizacion_estimada_USD")

    labels = ["Monto asegurado", "Prima comercial", "Indemnización estimada"]
    values = [monto, prima, indemnizacion]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=labels,
            x=values,
            orientation="h",
            text=[money_usd(v) for v in values],
            textposition="auto",
            marker_color=["#0e7490", "#7c3aed", "#16a34a"],
        )
    )

    fig.update_layout(
        height=285,
        margin=dict(l=10, r=10, t=20, b=10),
        xaxis_title="USD",
        yaxis_title="",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=13),
    )

    return fig


def build_risk_gauge(result):
    prob = float(get_value(result, "probabilidad_perdida", default=0)) * 100
    nivel = get_value(result, "nivel_riesgo", default="Bajo")

    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=prob,
            number={"suffix": "%", "font": {"size": 34}},
            title={"text": "Probabilidad de pérdida"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": risk_color(nivel)},
                "steps": [
                    {"range": [0, 35], "color": "#dcfce7"},
                    {"range": [35, 50], "color": "#fef3c7"},
                    {"range": [50, 100], "color": "#fee2e2"},
                ],
            },
        )
    )

    fig.update_layout(
        height=285,
        margin=dict(l=20, r=20, t=45, b=20),
        paper_bgcolor="white",
        font=dict(size=13),
    )

    return fig


def build_index_reference_chart(result):
    indice = float(get_value(result, "indice_riesgo", default=0))
    nivel = get_value(result, "nivel_riesgo", default="Bajo")

    fig = go.Figure()

    fig.add_shape(
        type="rect",
        x0=-3,
        x1=0,
        y0=0,
        y1=1,
        fillcolor="#fee2e2",
        opacity=0.75,
        line_width=0,
    )
    fig.add_shape(
        type="rect",
        x0=0,
        x1=0.5,
        y0=0,
        y1=1,
        fillcolor="#fef3c7",
        opacity=0.8,
        line_width=0,
    )
    fig.add_shape(
        type="rect",
        x0=0.5,
        x1=3,
        y0=0,
        y1=1,
        fillcolor="#dcfce7",
        opacity=0.8,
        line_width=0,
    )

    fig.add_trace(
        go.Scatter(
            x=[indice],
            y=[0.5],
            mode="markers+text",
            marker=dict(size=22, color=risk_color(nivel)),
            text=[number(indice, 2)],
            textposition="top center",
            name="Índice seleccionado",
        )
    )

    fig.update_layout(
        height=220,
        margin=dict(l=15, r=15, t=25, b=25),
        xaxis=dict(title="Índice de riesgo", range=[-3, 3]),
        yaxis=dict(visible=False, range=[0, 1]),
        plot_bgcolor="white",
        paper_bgcolor="white",
        showlegend=False,
    )

    return fig


# ============================================================
# ENCABEZADO
# ============================================================

st.markdown('<div class="main-title">Simulador de Seguro Indexado</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Evaluación de riesgo, producción esperada y prima comercial para café en Caldas</div>',
    unsafe_allow_html=True,
)


# ============================================================
# BLOQUE 1 — PARÁMETROS
# ============================================================

st.markdown('<div class="section-title">1. Parámetros de cotización</div>', unsafe_allow_html=True)

try:
    municipios = municipios_disponibles()
    anios = [int(a) for a in anios_disponibles() if int(a) >= 2025]
    if not anios:
        anios = [int(a) for a in anios_disponibles()]
except Exception as e:
    st.error(f"No fue posible cargar municipios o años disponibles: {e}")
    st.stop()

col1, col2, col3, col4 = st.columns([1.15, 1.25, 0.9, 0.85])

with col1:
    area_ha = st.number_input(
        "Área a asegurar (ha)",
        min_value=0.1,
        value=8.5,
        step=0.5,
    )

with col2:
    default_mun = "MANIZALES"
    municipio = st.selectbox(
        "Municipio",
        municipios,
        index=municipios.index(default_mun) if default_mun in municipios else 0,
    )

with col3:
    anio = st.selectbox(
        "Año",
        anios,
        index=anios.index(2026) if 2026 in anios else 0,
    )

with col4:
    st.markdown("<br>", unsafe_allow_html=True)
    st.button("Simular", width="stretch")


# ============================================================
# EJECUTAR COTIZACIÓN
# ============================================================

try:
    result = cotizar_seguro(
        municipio=municipio,
        anio=int(anio),
        area_ha=float(area_ha),
    )
except Exception as e:
    st.error(f"No fue posible generar la cotización: {e}")
    st.stop()


# ============================================================
# BLOQUE 2 — RESULTADO FINANCIERO
# ============================================================

st.markdown('<div class="section-title">2. Resultado financiero del seguro</div>', unsafe_allow_html=True)

rendimiento = get_value(result, "rendimiento_esperado_t_ha")
produccion = get_value(result, "produccion_esperada_t")
precio = get_value(result, "precio_usd_ton", "precio_USD_ton")
indice = get_value(result, "indice_riesgo")
nivel = get_value(result, "nivel_riesgo")
probabilidad = get_value(result, "probabilidad_perdida")
monto = get_value(result, "monto_asegurado_usd", "monto_asegurado_USD")
prima = get_value(result, "prima_comercial_usd", "prima_comercial_USD")
indemnizacion = get_value(result, "indemnizacion_estimada_usd", "indemnizacion_estimada_USD")
payout = get_value(result, "payout")
cluster = get_value(result, "cluster")
tipo_estimacion = get_value(result, "tipo_estimacion")


row1 = st.columns(4)

with row1[0]:
    st.markdown(
        f"""
        <div class="card">
            <div class="kpi-label">Rendimiento esperado</div>
            <div class="kpi-value" style="color:#16a34a;">{number(rendimiento, 2)} t/ha</div>
            <div class="kpi-small">Promedio histórico municipal</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row1[1]:
    st.markdown(
        f"""
        <div class="card">
            <div class="kpi-label">Producción esperada</div>
            <div class="kpi-value" style="color:#16a34a;">{number(produccion, 2)} t</div>
            <div class="kpi-small">Rendimiento × área asegurada</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row1[2]:
    st.markdown(
        f"""
        <div class="card">
            <div class="kpi-label">Índice de riesgo</div>
            <div class="kpi-value" style="color:#2563eb;">{number(indice, 2)}</div>
            <div class="kpi-small">Índice climático estandarizado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row1[3]:
    css = risk_class(nivel)
    st.markdown(
        f"""
        <div class="card {css}">
            <div class="kpi-label">Nivel de riesgo</div>
            <div class="kpi-value">{str(nivel).upper()}</div>
            <div class="kpi-small">Clasificación del índice</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)

row2 = st.columns(4)

with row2[0]:
    st.markdown(
        f"""
        <div class="card">
            <div class="kpi-label">Probabilidad de pérdida</div>
            <div class="kpi-value" style="color:#f97316;">{pct(probabilidad)}</div>
            <div class="kpi-small">Estimación empírica histórica</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row2[1]:
    st.markdown(
        f"""
        <div class="card">
            <div class="kpi-label">Monto asegurado</div>
            <div class="kpi-value" style="color:#0e7490;">{money_usd(monto)}</div>
            <div class="kpi-small">Producción esperada × precio</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row2[2]:
    st.markdown(
        f"""
        <div class="card">
            <div class="kpi-label">Prima comercial</div>
            <div class="kpi-value" style="color:#7c3aed;">{money_usd(prima)}</div>
            <div class="kpi-small">Incluye utilidad/margen comercial</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

with row2[3]:
    st.markdown(
        f"""
        <div class="card">
            <div class="kpi-label">Indemnización estimada</div>
            <div class="kpi-value" style="color:#16a34a;">{money_usd(indemnizacion)}</div>
            <div class="kpi-small">Payout × monto asegurado</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# BLOQUE 3 — EXPLICACIÓN DEL RIESGO Y SOPORTE VISUAL
# ============================================================

st.markdown('<div class="section-title">3. Explicación del riesgo y soporte visual</div>', unsafe_allow_html=True)

left, right = st.columns([1.25, 1])

with left:
    st.markdown("#### Resumen financiero")
    st.plotly_chart(build_financial_chart(result), width="stretch")

    st.markdown("#### Referencia del índice de riesgo")
    st.plotly_chart(build_index_reference_chart(result), width="stretch")

with right:
    st.markdown(
        f"""
        <div class="status-box {risk_class(nivel)}">
            ESTADO: {risk_status(nivel)}<br>
            <span style="font-size:14px; font-weight:500;">Riesgo {str(nivel).lower()} | Cluster {cluster}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
        <div class="interpretation">
            <b>Interpretación para el cliente</b><br><br>
            {interpretation_text(result)}
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("#### Probabilidad de pérdida")
    st.plotly_chart(build_risk_gauge(result), width="stretch")


# ============================================================
# DETALLE DESCARGABLE
# ============================================================

st.markdown('<div class="section-title">Detalle de cotización</div>', unsafe_allow_html=True)

detalle = pd.DataFrame(
    {
        "Concepto": [
            "Municipio",
            "Año",
            "Área asegurada (ha)",
            "Cluster",
            "Tipo de estimación",
            "Rendimiento esperado (t/ha)",
            "Producción esperada (t)",
            "Precio venta (USD/ton)",
            "Índice de riesgo",
            "Nivel de riesgo",
            "Probabilidad de pérdida",
            "Payout esperado",
            "Monto asegurado",
            "Prima comercial",
            "Indemnización estimada",
        ],
        "Valor": [
            str(municipio),
            str(anio),
            number(area_ha, 2),
            str(cluster),
            str(tipo_estimacion),
            number(rendimiento, 2),
            number(produccion, 2),
            money_usd(precio),
            number(indice, 2),
            str(nivel),
            pct(probabilidad),
            pct(payout),
            money_usd(monto),
            money_usd(prima),
            money_usd(indemnizacion),
        ],
    }
)

detalle["Valor"] = detalle["Valor"].astype(str)

st.dataframe(detalle, width="stretch", hide_index=True)

st.download_button(
    label="Descargar cotización en CSV",
    data=detalle.to_csv(index=False).encode("utf-8-sig"),
    file_name=f"cotizacion_{municipio}_{anio}.csv",
    mime="text/csv",
    width="stretch",
)


st.markdown(
    """
    <div class="note-box">
        Nota: Este simulador corresponde a un prototipo académico de seguro agrícola indexado. 
        Los valores generados dependen de los supuestos, parámetros y datos disponibles en el modelo.
    </div>
    """,
    unsafe_allow_html=True,
)