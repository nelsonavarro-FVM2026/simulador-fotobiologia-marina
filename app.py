import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Simulador de Radiación y Fotobiología Marina", layout="wide"
)

st.title("🌊 Fotobiología Marina: Atenuación Espectral Terrestre y Submarina")

# --- CONTROLES EN BARRA LATERAL ---
st.sidebar.header("Parámetros de Simulación")
profundidad_max = st.sidebar.slider("Profundidad máxima mostrada (m)", 1.0, 30.0, 10.0, 1.0)
profundidad_usuario = st.sidebar.slider("Profundidad de análisis (m)", 0.0, profundidad_max, 2.0, 0.5)
tipo_agua = st.sidebar.selectbox(
    "Tipo de Agua (Clasificación Jerlov)", 
    ["Océano Abierto (Jerlov I)", "Agua Costera (Jerlov 3C)"]
)

# Rango de longitud de onda (200 a 800 nm)
lambdas = np.arange(200, 801, 1)

# --- 1. MODELO DE IRRADIANCIA SOLAR EN LA SUPERFICIE TERRESTRE ---
# Planck/Aproximación atmosférica (Corte de ozono en <290 nm + Pico ~500 nm + valles de absorción)
corte_ozono = 1 / (1 + np.exp(-(lambdas - 295) / 6))  # Absorción total por debajo de ~290nm
pico_solar = 1.32 * np.exp(-((lambdas - 500) / 180)**2)

# Valles de absorción atmosférica (H2O, O2, O3)
valle_h2o = 1 - 0.18 * np.exp(-((lambdas - 760) / 15)**2)
valle_o2 = 1 - 0.08 * np.exp(-((lambdas - 687) / 10)**2)

irradiancia_0 = pico_solar * corte_ozono * valle_h2o * valle_o2

# --- 2. COEFICIENTE DE ATENUACIÓN Kd(lambda) DE 200 A 800 nm ---
if tipo_agua == "Océano Abierto (Jerlov I)":
    # Fuerte absorción en UV (<300nm) y en Infrarrojo/Rojo (>700nm), ventana transparente en Azul (440-490nm)
    kd = 0.03 + 2.5 * np.exp(-(lambdas - 200) / 45) + 0.45 * (lambdas / 700)**8
else:
    # Agua costera: la materia orgánica disuelta (CDOM) extingue casi todo el UV y azul
    kd = 0.15 + 4.0 * np.exp(-(lambdas - 200) / 55) + 0.5 * (lambdas / 700)**6

irradiancia_z = irradiancia_0 * np.exp(-kd * profundidad_usuario)

# --- FUNCION PARA AÑADIR LAS BANDAS DE COLOR AL FONDO DEL GRÁFICO ---
def agregar_bandas_espectrales(fig):
    bandas = [
        (200, 315, "rgba(200, 200, 200, 0.25)", "UV (UVC/UVB)"),
        (315, 400, "rgba(180, 150, 220, 0.25)", "UVA"),
        (400, 430, "rgba(138, 43, 226, 0.25)", "Violeta"),
        (430, 500, "rgba(30, 144, 255, 0.25)", "Azul"),
        (500, 560, "rgba(50, 205, 50, 0.25)", "Verde"),
        (560, 590, "rgba(255, 215, 0, 0.25)", "Amarillo"),
        (590, 630, "rgba(255, 140, 0, 0.25)", "Naranja"),
        (630, 700, "rgba(255, 0, 0, 0.25)", "Rojo"),
        (700, 800, "rgba(139, 0, 0, 0.15)", "Infrarrojo (NIR)")
    ]
    for x0, x1, color, nombre in bandas:
        fig.add_vrect(
            x0=x0, x1=x1, fillcolor=color, opacity=0.8,
            layer="below", line_width=0,
            annotation_text=nombre if (x1 - x0) > 25 else "",
            annotation_position="top left",
            annotation_font_size=10
        )

# --- 3. GRÁFICO 1: ESPECTRO DE IRRADIANCIA TERRESTRE Y PROFUNDIDAD ---
fig_espectro = go.Figure()

fig_espectro.add_trace(go.Scatter(
    x=lambdas, y=irradiancia_0,
    name="Superficie Terrestre (0 m)",
    line=dict(color="black", width=2.5, dash="dash")
))

fig_espectro.add_trace(go.Scatter(
    x=lambdas, y=irradiancia_z,
    name=f"Profundidad Submarina ({profundidad_usuario} m)",
    fill="tozeroy",
    fillcolor="rgba(0, 191, 255, 0.4)",
    line=dict(color="navy", width=2)
))

agregar_bandas_espectrales(fig_espectro)

fig_espectro.update_layout(
    title="<b>Espectro de Irradiancia Terrestre vs. Penetraciones Submarinas (200 - 800 nm)</b>",
    xaxis=dict(title="Longitud de Onda (nm)", range=[200, 800]),
    yaxis=dict(title="Irradiancia Espectral (W m⁻² nm⁻¹)"),
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.98, xanchor="right", x=0.98)
)

# --- 4. GRÁFICO 2: FAN-PLOT DE ATENUACIÓN EN LA COLUMNA DE AGUA ---
fig_columna = go.Figure()

profundidades = np.linspace(0, profundidad_max, 6)
colores_linea = ["#000000", "#1A5276", "#2980B9", "#5DADE2", "#A9CCE3", "#D4E6F1"]

for prof, col in zip(profundidades, colores_linea):
    e_p = irradiancia_0 * np.exp(-kd * prof)
    fig_columna.add_trace(go.Scatter(
        x=lambdas, y=e_p,
        name=f"{prof:.1f} m",
        line=dict(color=col, width=2)
    ))

agregar_bandas_espectrales(fig_columna)

fig_columna.update_layout(
    title="<b>Perfil de Atenuación en la Columna de Agua (Fan-Plot)</b>",
    xaxis=dict(title="Longitud de Onda (nm)", range=[200, 800]),
    yaxis=dict(title="Irradiancia Espectral (W m⁻² nm⁻¹)"),
    hovermode="x unified",
    legend=dict(yanchor="top", y=0.98, xanchor="right", x=0.98)
)

# --- DESPLIEGUE EN STREAMLIT ---
st.plotly_chart(fig_espectro, use_container_width=True)
st.plotly_chart(fig_columna, use_container_width=True)

st.markdown("""
### 💡 Puntos Didácticos para el Alumnado:
* **Filtro de la Capa de Ozono:** Observa cómo por debajo de $290\\text{ nm}$ (UVC y parte del UVB) la radiación es nula en la superficie terrestre gracias a la absorción atmosférica de $O_3$.
* **Pico del Visible:** El máximo de irradiancia ocurre alrededor de los $500\\text{ nm}$ (luz azul-verde), coincidiendo con la ventana fototrófica.
* **Comportamiento en Agua:**
  * En **Océano Abierto**, las bandas del Rojo e Infrarrojo ($>700\\text{ nm}$) son absorbidas velozmente en los primeros metros por el agua pura, mientras la radiación azul se propaga en profundidad.
  * En **Agua Costera**, la materia orgánica (CDOM) extingue fuertemente la radiación violeta y azul, desplazando la máxima penetración hacia la banda del verde.
""")
