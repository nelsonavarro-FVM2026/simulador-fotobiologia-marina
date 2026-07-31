import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Simulador de Luz y Radiación Marina", layout="wide"
)

st.title("🌊 Fotobiología Marina: Atenuación y Radiación Efectiva")

# Sidebar - Parámetros
st.sidebar.header("Parámetros de Simulación")
profundidad_max = st.sidebar.slider("Profundidad máxima mostrada (m)", 1.0, 30.0, 10.0, 1.0)
profundidad_usuario = st.sidebar.slider("Profundidad de análisis (m)", 0.0, profundidad_max, 2.0, 0.5)
tipo_agua = st.sidebar.selectbox(
    "Tipo de Agua (Clasificación Jerlov)", 
    ["Océano Abierto (Jerlov I)", "Agua Costera (Jerlov 3C)"]
)

# Longitudes de onda (280 a 700 nm)
lambdas = np.arange(280, 701, 1)

# --- 1. MODELO CONTINUO DE IRRADIANCIA SUPERFICIAL E_0(lambda) ---
E_uv = 0.55 * np.exp(-((lambdas - 390) / 45)**2)
E_vis = 1.2 * np.exp(-((lambdas - 490) / 160)**2)
irradiancia_0 = np.where(lambdas < 400, E_uv, E_vis)
sigmoide = 1 / (1 + np.exp(-(lambdas - 400) / 5))
irradiancia_0 = (1 - sigmoide) * E_uv + sigmoide * E_vis

# --- 2. COEFICIENTE DE ATENUACIÓN Kd(lambda) SUAVE ---
if tipo_agua == "Océano Abierto (Jerlov I)":
    kd = 0.02 + 0.15 * np.exp(-(lambdas - 280) / 60) + 0.35 * (lambdas / 700)**8
else:
    kd = 0.12 + 0.8 * np.exp(-(lambdas - 280) / 70) + 0.4 * (lambdas / 700)**6

# --- 3. GRÁFICO 1: ESPECTRO DE IRRADIANCIA A PROFUNDIDAD ---
irradiancia_z = irradiancia_0 * np.exp(-kd * profundidad_usuario)

fig_espectro = go.Figure()

fig_espectro.add_trace(go.Scatter(
    x=lambdas, y=irradiancia_0,
    name="Superficie (0m)",
    line=dict(color="orange", width=2, dash="dash")
))

fig_espectro.add_trace(go.Scatter(
    x=lambdas, y=irradiancia_z,
    name=f"Profundidad ({profundidad_usuario}m)",
    fill="tozeroy",
    line=dict(color="deepskyblue", width=2.5)
))

fig_espectro.update_layout(
    title="Espectro Irradiancia Continuo (Sin discontinuidades)",
    xaxis_title="Longitud de Onda (nm)",
    yaxis_title="Irradiancia Espectral (W m⁻² nm⁻¹)",
    hovermode="x unified"
)

# --- 4. GRÁFICO 2: FAN-PLOT DE ATENUACIÓN EN LA COLUMNA DE AGUA ---
fig_columna = go.Figure()

profundidades = np.linspace(0, profundidad_max, 6)
colores = ["#FFA500", "#76D7C4", "#3498DB", "#2E4053", "#1B2631", "#0B132B"]

for prof, col in zip(profundidades, colores):
    e_p = irradiancia_0 * np.exp(-kd * prof)
    fig_columna.add_trace(go.Scatter(
        x=lambdas, y=e_p,
        name=f"{prof:.1f} m",
        line=dict(color=col, width=1.8)
    ))

fig_columna.update_layout(
    title="Fan-Plot: Atenuación Espectral Gradual en la Columna de Agua",
    xaxis_title="Longitud de Onda (nm)",
    yaxis_title="Irradiancia Espectral (W m⁻² nm⁻¹)",
    hovermode="x unified"
)

# Despliegue en Streamlit
st.plotly_chart(fig_espectro, use_container_width=True)
st.plotly_chart(fig_columna, use_container_width=True)

st.markdown("""
### 📝 Conceptos Clave para la Práctica:
* **Curva Continua:** La atenuación natural no presenta saltos discontinuos en 400 nm.
* **Ventana Azul:** Nota cómo en agua oceánica el azul (~470 nm) penetra a mayor profundidad, mientras que el rojo y el UV decaen rápidamente.
* **Efecto Costero:** Cambia a "Agua Costera" y observa cómo la materia orgánica disuelta (CDOM) extingue casi por completo la luz azul y UV.
""")
