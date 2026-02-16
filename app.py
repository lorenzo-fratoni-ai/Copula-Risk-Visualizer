import streamlit as st
import plotly.graph_objects as go
import numpy as np
from scipy.stats import norm, t, expon

# --- CONFIGURAZIONE PAGINA (Simula il layout React) ---
st.set_page_config(layout="wide", page_title="Copula Visualizer")

# Stile custom per avvicinarsi al look "Slate" di Tailwind del codice React
st.markdown("""
<style>
    .stApp { background-color: #0f172a; color: #e2e8f0; } 
    .stSelectbox, .stSlider { color: #e2e8f0; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR (Corrisponde al componente <aside>) ---
with st.sidebar:
    st.title("Copula Visualizer")
    st.caption("Quantitative Risk Management Tool")
    
    st.markdown("---")

    # 1. Input N (Simulations)
    # React: min="100" max="100000" step="100"
    n_sim = st.slider("Simulations (N)", 100, 100000, 1000, 100)

    # 2. Input D (Dimensions)
    # React: min="2" max="5" step="1"
    d_dim = st.slider("Number of Marginals (d)", 2, 5, 2, 1)

    # 3. Copula Type
    copula_type = st.selectbox(
        "Copula Type", 
        ["GAUSSIAN", "STUDENT_T", "GUMBEL"]
    )

    # 4. Marginal Type
    marginal_type = st.selectbox(
        "Marginal Distribution", 
        ["NORMAL", "STUDENT_T", "EXPONENTIAL"]
    )

    # 5. Dependency Params (Conditional rendering)
    st.markdown("### Dependency Parameters")
    
    rho = 0.5
    theta = 2.0

    if copula_type == "GUMBEL":
        # React: min="1.0" max="10.0" step="0.1"
        col1, col2 = st.columns([3, 1])
        theta = st.slider("Theta (θ)", 1.0, 10.0, 2.0, 0.1)
        st.caption("Controls tail dependence")
    else:
        # React: min="-0.99" max="0.99" step="0.01"
        rho = st.slider("Correlation (ρ)", -0.99, 0.99, 0.5, 0.01)
        st.caption("Equicorrelated matrix parameter")


# --- LOGICA MATEMATICA (Ricostruzione di ./utils/math) ---

def generate_data(n, d, copula, marginal, rho_val, theta_val):
    u_matrix = np.zeros((n, d))
    
    # 1. Generazione Copula (Spazio Uniforme)
    if copula == "GAUSSIAN":
        mean = np.zeros(d)
        cov = np.full((d, d), rho_val)
        np.fill_diagonal(cov, 1)
        x_mvn = np.random.multivariate_normal(mean, cov, size=n)
        u_matrix = norm.cdf(x_mvn)
        
    elif copula == "STUDENT_T":
        df = 4
        mean = np.zeros(d)
        cov = np.full((d, d), rho_val)
        np.fill_diagonal(cov, 1)
        x_mvn = np.random.multivariate_normal(mean, cov, size=n)
        w = np.random.chisquare(df, size=n) / df
        x_mvt = x_mvn / np.sqrt(w)[:, None]
        u_matrix = t.cdf(x_mvt, df=df)
        
    elif copula == "GUMBEL":
        # Simulazione per Gumbel Archimedea
        alpha = 1.0 / theta_val
        # Generatore variabile stabile (Chambers-Mallows-Stuck)
        pi = np.pi
        u_stab = np.random.uniform(-pi/2, pi/2, n)
        w_stab = np.random.exponential(1, n)
        
        # S ~ Stable(alpha, 1, 1, 0) skewata
        # Nota: formula semplificata per la simulazione
        val = (np.sin(alpha * u_stab) / (np.cos(u_stab) ** (1/alpha))) * \
              ((np.cos((1-alpha)*u_stab) / w_stab) ** ((1-alpha)/alpha))
        S = val
        
        E = np.random.exponential(1, (n, d))
        # Generatore inverso Gumbel: exp(-(E/S)^alpha)
        # Nota: gestione valori negativi/nan
        S = np.abs(S)
        u_matrix = np.exp(- (E / S[:, None]) ** alpha)

    # 2. Trasformazione Marginale (Inverse CDF)
    x_matrix = np.zeros_like(u_matrix)
    
    if marginal == "NORMAL":
        x_matrix = norm.ppf(u_matrix)
    elif marginal == "STUDENT_T":
        # Centrata, df=4
        x_matrix = t.ppf(u_matrix, df=4)
    elif marginal == "EXPONENTIAL":
        # Centrata in 0 (Exp standard - 1)
        x_matrix = expon.ppf(u_matrix) - 1.0
        
    return u_matrix, x_matrix

# Esecuzione simulazione
try:
    data_uniform, data_marginal = generate_data(n_sim, d_dim, copula_type, marginal_type, rho, theta)
except Exception as e:
    st.error(f"Simulation error: {e}")
    st.stop()

# --- PLOTTING (Simula useEffect Plotting) ---

# Configurazione colori React: #38bdf8 (Sky 400), #f472b6 (Pink 400)
color_uniform = '#38bdf8'
color_marginal = '#f472b6'

# Opacity logic: Math.max(0.1, Math.min(0.8, 1000 / params.n))
opacity_val = max(0.1, min(0.8, 1000 / n_sim))

# 3D Logic: const is3D = params.d >= 3;
is_3d = d_dim >= 3

# Subsampling per performance browser se necessario (opzionale, React non lo faceva ma Plotly Python è più lento di JS)
# Manteniamo tutto per fedeltà, ma attenzione a N=100k
plot_n = n_sim
if n_sim > 10000:
    idx = np.random.choice(n_sim, 10000, replace=False)
    u_plot = data_uniform[idx]
    x_plot = data_marginal[idx]
else:
    u_plot = data_uniform
    x_plot = data_marginal

col1, col2 = st.columns(2)

def get_plot_layout(title, range_vals=None):
    layout = dict(
        title=title,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(255,255,255,0.05)',
        font=dict(color='#e2e8f0'),
        margin=dict(t=40, b=30, l=30, r=30),
        height=450
    )
    return layout

# --- PLOT 1: UNIFORM ---
with col1:
    if is_3d:
        fig_u = go.Figure(go.Scatter3d(
            x=u_plot[:, 0], y=u_plot[:, 1], z=u_plot[:, 2],
            mode='markers', marker=dict(size=2, opacity=opacity_val, color=color_uniform)
        ))
        fig_u.update_layout(
            **get_plot_layout(f"Copula Space (Uniform) {d_dim}D"),
            scene=dict(
                xaxis=dict(title='U1', range=[0,1]),
                yaxis=dict(title='U2', range=[0,1]),
                zaxis=dict(title='U3', range=[0,1])
            )
        )
    else:
        fig_u = go.Figure(go.Scatter(
            x=u_plot[:, 0], y=u_plot[:, 1],
            mode='markers', marker=dict(size=3, opacity=opacity_val, color=color_uniform)
        ))
        fig_u.update_layout(
            **get_plot_layout(f"Copula Space (Uniform) {d_dim}D"),
            xaxis=dict(title='U1', range=[0,1]),
            yaxis=dict(title='U2', range=[0,1])
        )
    
    st.plotly_chart(fig_u, use_container_width=True)

# --- PLOT 2: MARGINAL ---
with col2:
    # Determinazione range come nel codice React
    rng = None
    if marginal_type == "NORMAL": rng = [-4, 4]
    elif marginal_type == "STUDENT_T": rng = [-6, 6]
    elif marginal_type == "EXPONENTIAL": rng = [-1.5, 5]

    if is_3d:
        fig_m = go.Figure(go.Scatter3d(
            x=x_plot[:, 0], y=x_plot[:, 1], z=x_plot[:, 2],
            mode='markers', marker=dict(size=2, opacity=opacity_val, color=color_marginal)
        ))
        fig_m.update_layout(
            **get_plot_layout(f"Marginal Space ({marginal_type})"),
            scene=dict(
                xaxis=dict(title='X1', range=rng),
                yaxis=dict(title='X2', range=rng),
                zaxis=dict(title='X3', range=rng)
            )
        )
    else:
        fig_m = go.Figure(go.Scatter(
            x=x_plot[:, 0], y=x_plot[:, 1],
            mode='markers', marker=dict(size=3, opacity=opacity_val, color=color_marginal)
        ))
        fig_m.update_layout(
            **get_plot_layout(f"Marginal Space ({marginal_type})"),
            xaxis=dict(title='X1', range=rng),
            yaxis=dict(title='X2', range=rng)
        )

    st.plotly_chart(fig_m, use_container_width=True)
