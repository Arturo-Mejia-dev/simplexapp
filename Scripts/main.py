import streamlit as st
import pulp as pl
import pandas as pd
import plotly.express as px
import io
import json
import os
import math
import time
import requests
import datetime
import urllib3

# --- ⚙️ CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Simplex: Rebel Wings Personnel", layout="wide", initial_sidebar_state="expanded")

# --- 🎨 INYECCIÓN DE CSS (CENTRADOS ABSOLUTOS Y TABLAS ALINEADAS) ---
st.markdown("""
<style>
div[data-testid="stStatusWidget"] { visibility: hidden; height: 0%; position: fixed; }

/* Loader Nativo (Sutil) */
[data-testid="stSkeleton"], .stSkeleton {
    background: linear-gradient(110deg, rgba(255, 255, 255, 0.1) 30%, #FFD700 45%, #FF0000 50%, #00FFFF 55%, rgba(255, 255, 255, 0.1) 70%) !important;
    background-size: 300% 100% !important; animation: mega_shimmer 0.8s infinite linear !important; 
    border-radius: 15px !important; opacity: 0.9 !important; border: 2px solid rgba(255, 215, 0, 0.3);
}
@keyframes mega_shimmer { 0% { background-position: 300% 0; } 100% { background-position: -300% 0; } }

div.stSpinner > div > div { border-color: #FF0000 transparent transparent transparent !important; width: 80px !important; height: 80px !important; border-width: 8px !important; }
div.stSpinner { text-align: center; margin-top: 50px; font-size: 20px; font-weight: bold; color: #FF0000; }

/* Animaciones sutiles */
@keyframes pulse_red_small { 0% { box-shadow: 0 0 0 0 rgba(204, 0, 0, 0.6); } 70% { box-shadow: 0 0 0 6px rgba(204, 0, 0, 0); } 100% { box-shadow: 0 0 0 0 rgba(204, 0, 0, 0); } }
@keyframes pulse_yellow_small { 0% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.6); } 70% { box-shadow: 0 0 0 6px rgba(255, 193, 7, 0); } 100% { box-shadow: 0 0 0 0 rgba(255, 193, 7, 0); } }
@keyframes pulse_blue_small { 0% { box-shadow: 0 0 0 0 rgba(31, 119, 180, 0.4); } 70% { box-shadow: 0 0 0 6px rgba(31, 119, 180, 0); } 100% { box-shadow: 0 0 0 0 rgba(31, 119, 180, 0); } }
@keyframes pulse_green_small { 0% { box-shadow: 0 0 0 0 rgba(44, 160, 44, 0.6); } 70% { box-shadow: 0 0 0 6px rgba(44, 160, 44, 0); } 100% { box-shadow: 0 0 0 0 rgba(44, 160, 44, 0); } }

/* 🔥 FORZANDO CENTRADO ABSOLUTO DE DATOS DUROS 🔥 */
.anim_fuga, .anim_ahorro, .anim_metric_blue, .anim_metric_yellow, .anim_metric_green {
    display: flex !important; flex-direction: column !important; justify-content: center !important;
    align-items: center !important; text-align: center !important; border-radius: 10px; padding: 20px;
}
.anim_fuga { animation: pulse_red_small 2s infinite !important; border: 2px solid #FFCCCC !important; background-color: #FFF0F0; }
.anim_ahorro { animation: pulse_yellow_small 2s infinite !important; border: 2px solid #FFE680 !important; background-color: #FFFFE0; }
.anim_metric_blue { animation: pulse_blue_small 2s infinite !important; border: 1px solid #1F77B4; background-color: #F0F8FF; }
.anim_metric_yellow { animation: pulse_yellow_small 2s infinite !important; border: 1px solid #FFC107; background-color: #FFFFF0; }
.anim_metric_green { animation: pulse_green_small 2s infinite !important; border: 1px solid #2CA02C; background-color: #F0FFF0; }

[data-testid="stDataFrame"] td { text-align: center !important; }
[data-testid="stDataFrame"] th { text-align: center !important; }

/* --- 🔘 BOTONES SIMÉTRICOS Y ESTILIZADOS --- */
.stButton button[kind="primary"], .stButton button[kind="secondary"] {
    padding: 8px 15px !important;
    font-size: 14px !important;
    font-weight: bold !important;
    border-radius: 8px !important;
    height: 45px !important;
}

/* Primario: Negro y Pulso Rojo (Calcular e Inyectar) */
.stButton button[kind="primary"] { 
    background-color: #111111 !important; 
    color: #FFFFFF !important; 
    border: 2px solid #FF0000 !important; 
    animation: pulse_red_small 2s infinite !important; 
}
.stButton button[kind="primary"]:hover { background-color: #222222 !important; border-color: #FF3333 !important; }

/* Botón Calcular Gigante (Reescribe el tamaño solo para el botón final) */
div:has(> .stButton button:contains("CALCULAR")) .stButton button {
    height: 60px !important;
    font-size: 18px !important;
}

/* Secundario: Claro y Pulso Azul (Limpiar, Todo Matutino, etc.) */
.stButton button[kind="secondary"] { 
    border: 1px solid #ccc !important; 
    animation: pulse_blue_small 2s infinite !important; 
}
.stButton button[kind="secondary"]:hover { background-color: #1F77B4 !important; color: #FFFFFF !important; border-color: #1F77B4 !important;}

.stDownloadButton button { background-color: #1F77B4 !important; color: #FFFFFF !important; border: 2px solid #155987 !important; padding: 8px 15px !important; font-weight: bold !important; border-radius: 8px !important;}

[data-testid="stFileUploader"] { background-color: #EBF5FB !important; border: 2px dashed #2E86C1 !important; border-radius: 10px !important; }

/* Efecto Latido Intenso para Gráficas */
@keyframes latido_grafico { 
    0% { transform: scale(1); box-shadow: 0 0 5px rgba(31, 119, 180, 0.3); border-color: #EBF5FB; } 
    50% { transform: scale(1.01); box-shadow: 0 0 15px rgba(31, 119, 180, 0.5); border-color: #1F77B4; } 
    100% { transform: scale(1); box-shadow: 0 0 5px rgba(31, 119, 180, 0.3); border-color: #EBF5FB; } 
}
[data-testid="stPlotlyChart"] { border-radius: 12px !important; padding: 15px !important; background-color: #FFFFFF !important; border: 2px solid #EBF5FB !important; animation: latido_grafico 3s infinite ease-in-out !important; margin: 20px 5px !important; transition: all 0.3s ease !important; }
[data-testid="stPlotlyChart"]:hover { animation: none !important; transform: scale(1.02) !important; box-shadow: 0 0 15px rgba(31, 119, 180, 0.4) !important; border-color: #1F77B4 !important; }

@media print { section[data-testid="stSidebar"], header[data-testid="stHeader"], .stButton, .stDownloadButton { display: none !important; } * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; } }
</style>
""", unsafe_allow_html=True)

# --- 💾 CONFIGURACIÓN INICIAL ---
CONFIG_FILE = "config_simplex.json"
dias_semana = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
bloques = ["10:00 a 14:00 (4 hrs)", "14:00 a 17:00 (3 hrs)", "17:00 a 18:00 (1 hr)", "18:00 a 22:00 (4 hrs)", "22:00 a 01:00 (3 hrs)"]
horas_por_bloque = [4, 3, 1, 4, 3]
puestos_fijos = ['Supervisor', 'Caja', 'Hostes', 'Empacador', 'Auxiliar']

DEFAULT_CONFIG = {
    's_coc': 350.0, 's_ven': 300.0, 's_bar': 320.0, 's_sup': 500.0, 's_caj': 300.0, 's_hos': 250.0,
    's_emp': 250.0, 's_aux': 250.0, 'c_coc': 8, 'c_sal': 12, 'c_bar': 15,
    'esp_pct': {d: 0.0 for d in dias_semana}, 'ideal_sup': 2, 'ideal_caj': 3, 'ideal_hos': 3, 'ideal_emp': 2, 'ideal_aux': 2 
}

def consultarSimplex(ids,fi,ff):
    form_data = {
    'ids': str(ids),                     # El valor debe ser string o número; requests lo codificará
    'fi': fi.strftime('%Y-%m-%d'),       # Ej: '2025-03-01'
    'ff': ff.strftime('%Y-%m-%d')        # Ej: '2025-03-10'
    }
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    url = "https://operamx.no-ip.net/back/api_tickets/api/Simplex/ObtenerDatosSimplex"
    #url = 'https://localhost:7165/api/Simplex/ObtenerDatosSimplex'

    try:
        response = requests.post(url, data=form_data, verify=False)
        response.raise_for_status()  # Lanza excepción si hay error HTTP
        datosSimplex = response.json()

        valores = [datosSimplex[0]["venta"],
                    datosSimplex[5]["venta"],
                    datosSimplex[10]["venta"],
                    datosSimplex[15]["venta"],
                    datosSimplex[20]["venta"],
                    datosSimplex[25]["venta"],
                    datosSimplex[30]["venta"]]
        # Crear DataFrame
        dft = pd.DataFrame({
            'Día': dias_semana,
            'Venta Proyectada ($)': valores
        })
        dft['Día'] = dft['Día'].str.strip()
        st.session_state.df_ventas = dft

        filas_dem = []
        for d in dias_semana:
            index = 0; 
            for b in bloques:
                filas_dem.append({"Día": d, "Bloque": b, "🍳 Cmds Cocina": datosSimplex[index]["alimentos"], "🍳 Extra Cocina": 0.0, "🍔 Cmds Salón": datosSimplex[index]["salon"], "🍔 Extra Salón": 0.0, "🍺 Cmds Barra": datosSimplex[index]["bebidas"], "🍺 Extra Barra": 0.0})
                index = index + 1
        st.session_state.df_demanda = pd.DataFrame(filas_dem)
    except requests.exceptions.RequestException as e:
        print('Error en la petición:', e)
    
def get_week_dates(year, week_num):
    """Devuelve (domingo, sábado) de la semana `week_num` del año `year`."""
    start_week1 = get_week_start_base(year)
    start = start_week1 + datetime.timedelta(weeks=week_num - 1)
    end = start + datetime.timedelta(days=6)
    return start, end

# Función para obtener el domingo de inicio de la semana 1 del año
def get_week_start_base(year):
    # 1 de enero del año
    jan1 = datetime.date(year, 1, 1)
    # Días a restar para llegar al domingo anterior o igual al 1 de enero
    # weekday(): lunes=0, domingo=6
    days_to_subtract = (jan1.weekday() + 1) % 7
    return jan1 - datetime.timedelta(days=days_to_subtract)

# Función que devuelve el número de semana de una fecha dada
def week_number(date):
    start = get_week_start_base(date.year)
    delta = date - start
    return delta.days // 7 + 1

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                if 'esp_pct' not in data: data['esp_pct'] = {d: 0.0 for d in dias_semana}
                if 'ideal_sup' not in data: data['ideal_sup'] = 2
                if 'ideal_caj' not in data: data['ideal_caj'] = 3
                if 'ideal_hos' not in data: data['ideal_hos'] = 3
                if 'ideal_emp' not in data: data['ideal_emp'] = 2
                if 'ideal_aux' not in data: data['ideal_aux'] = 2
                if 's_emp' not in data: data['s_emp'] = 250.0
                if 's_aux' not in data: data['s_aux'] = 250.0
                return data
        except:
            return DEFAULT_CONFIG
    return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

config_data = load_config()

# --- 🧠 INICIALIZACIÓN DE SESIÓN (BASE DE DATOS ANTI-LAG Y EN CEROS) ---
if 'c_sup' not in st.session_state: st.session_state.c_sup = 0
if 'c_caj' not in st.session_state: st.session_state.c_caj = 0
if 'c_coc' not in st.session_state: st.session_state.c_coc = 0
if 'c_sal' not in st.session_state: st.session_state.c_sal = 0
if 'c_bar' not in st.session_state: st.session_state.c_bar = 0
if 'c_emp' not in st.session_state: st.session_state.c_emp = 0
if 'c_aux' not in st.session_state: st.session_state.c_aux = 0
if 'c_hos' not in st.session_state: st.session_state.c_hos = 0
if 'descanso_sup' not in st.session_state: st.session_state.descanso_sup = "Lunes"

# Contadores de versión dinámica para evitar StreamlitAPIException
for p in puestos_fijos:
    if f'counter_{p}' not in st.session_state:
        st.session_state[f'counter_{p}'] = 0
if 'counter_demanda' not in st.session_state:
    st.session_state['counter_demanda'] = 0

# MEMORIA BASE (EN CEROS)
if 'df_ventas' not in st.session_state:
    st.session_state.df_ventas = pd.DataFrame({"Día": dias_semana, "Venta Proyectada ($)": [0.0] * 7})

if 'df_fijos_dict' not in st.session_state:
    st.session_state.df_fijos_dict = {}
    for p in puestos_fijos:
        df_temp = pd.DataFrame([{"Día": d, "Matutino": False, "Intermedio": False, "Vespertino": False} for d in dias_semana])
        df_temp['Matutino'] = df_temp['Matutino'].astype(bool)
        df_temp['Intermedio'] = df_temp['Intermedio'].astype(bool)
        df_temp['Vespertino'] = df_temp['Vespertino'].astype(bool)
        st.session_state.df_fijos_dict[p] = df_temp

if 'df_demanda' not in st.session_state:
    filas_dem = []
    for d in dias_semana:
        for b in bloques:
            filas_dem.append({"Día": d, "Bloque": b, "🍳 Cmds Cocina": 0.0, "🍳 Extra Cocina": 0.0, "🍔 Cmds Salón": 0.0, "🍔 Extra Salón": 0.0, "🍺 Cmds Barra": 0.0, "🍺 Extra Barra": 0.0})
    st.session_state.df_demanda = pd.DataFrame(filas_dem)

if 'db' not in st.session_state:
    st.session_state.db = {'ventas': {}, 'fijos': {}, 'demanda': {}}
    for d in dias_semana:
        st.session_state.db['ventas'][d] = 0.0
        st.session_state.db['fijos'][d] = {'sm': False, 'si': False, 'sv': False, 'cm': False, 'ci': False, 'cv': False, 'hm': False, 'hi': False, 'hv': False, 'em': False, 'ei': False, 'ev': False, 'am': False, 'ai': False, 'av': False}
        st.session_state.db['demanda'][d] = {'cc': [0.0]*5, 'ec': [0.0]*5, 'cs': [0.0]*5, 'es': [0.0]*5, 'cb': [0.0]*5, 'eb': [0.0]*5}

if 'tope' not in st.session_state: st.session_state['tope'] = 20.0
if 'config_unlocked' not in st.session_state: st.session_state['config_unlocked'] = False
if 'resultados_diarios' not in st.session_state: st.session_state['resultados_diarios'] = None
if 'preview_v' not in st.session_state:
    st.session_state['preview_v'] = None; st.session_state['preview_f'] = None; st.session_state['preview_d'] = None
if 'plantilla_ideal' not in st.session_state: st.session_state['plantilla_ideal'] = {}

def sync_tope_slider(): st.session_state.tope = st.session_state.input_slider
def sync_tope_num(): st.session_state.tope = st.session_state.input_num

# --- 🚀 FUNCIONES DE CALLBACK (BOTONES MÁGICOS SIN SALTO DE PÁGINA) ---
def update_all_fijos(puesto, turno, valor):
    st.session_state.df_fijos_dict[puesto][turno] = valor
    st.session_state[f'counter_{puesto}'] += 1

def clear_all_fijos(puesto):
    st.session_state.df_fijos_dict[puesto]['Matutino'] = False
    st.session_state.df_fijos_dict[puesto]['Intermedio'] = False
    st.session_state.df_fijos_dict[puesto]['Vespertino'] = False
    st.session_state[f'counter_{puesto}'] += 1

def inyectar_horas_extra(dia_in, turno_in, area_in, hrs_in):
    df = st.session_state.df_demanda
    dias_target = dias_semana if dia_in == "Todos" else [dia_in]
    
    if turno_in == "☀️ Matutino":
        b_exacto = "10:00 a 14:00 (4 hrs)"
    else:
        b_exacto = "22:00 a 01:00 (3 hrs)"
        
    cols_target = []
    if area_in in ["Todas", "🍳 Cocina"]: cols_target.append("🍳 Extra Cocina")
    if area_in in ["Todas", "🍔 Salón"]: cols_target.append("🍔 Extra Salón")
    if area_in in ["Todas", "🍺 Barra"]: cols_target.append("🍺 Extra Barra")
    
    mask = (df['Día'].isin(dias_target)) & (df['Bloque'] == b_exacto)
    for col in cols_target:
        df.loc[mask, col] = float(hrs_in)
    
    st.session_state['counter_demanda'] += 1

def limpiar_horas_extra():
    df = st.session_state.df_demanda
    df['🍳 Extra Cocina'] = 0.0
    df['🍔 Extra Salón'] = 0.0
    df['🍺 Extra Barra'] = 0.0
    st.session_state['counter_demanda'] += 1

def generar_machote():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_v_out = st.session_state.get('df_ventas_edited', st.session_state.df_ventas)
        df_v_out.to_excel(writer, sheet_name="Ventas", index=False)
        
        df_eq = pd.DataFrame({
            "Parámetro": ["Supervisor", "Caja", "Cocinero", "Vendedor", "Barra", "Empacador", "Auxiliar", "Hostes", "Descanso_Supervisor"],
            "Valor": [st.session_state.c_sup, st.session_state.c_caj, st.session_state.c_coc, st.session_state.c_sal, st.session_state.c_bar, st.session_state.c_emp, st.session_state.c_aux, st.session_state.c_hos, st.session_state.descanso_sup]
        })
        df_eq.to_excel(writer, sheet_name="Equipo_Actual", index=False)
        
        filas_fijos_excel = []
        for d in dias_semana:
            fila = {"Día": d}
            for p in puestos_fijos:
                df_p = st.session_state.get(f"df_fijos_{p}_edited", st.session_state.df_fijos_dict[p])
                row_p = df_p[df_p['Día'] == d].iloc[0]
                fila[f"{p}_Matutino"] = "Si" if row_p['Matutino'] else "No"
                fila[f"{p}_Intermedio"] = "Si" if row_p['Intermedio'] else "No"
                fila[f"{p}_Vespertino"] = "Si" if row_p['Vespertino'] else "No"
            filas_fijos_excel.append(fila)
        pd.DataFrame(filas_fijos_excel).to_excel(writer, sheet_name="Personal_Fijo", index=False)
        
        df_d_out = st.session_state.get('df_demanda_edited', st.session_state.df_demanda)
        df_d_out.to_excel(writer, sheet_name="Demanda", index=False)
    return output.getvalue()

# --- 🍔 ENCABEZADO REBEL WINGS ---
st.markdown("<h1 style='text-align: center; color: #111; margin-bottom: 0; font-weight: bold;'>🍗 REBEL WINGS 🍔</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555; margin-top: 0;'>🔥 SIMPLEX: Tu Asistente para controlar tu personal</h3>", unsafe_allow_html=True)

st.markdown("""
<div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 10px; margin-bottom: 25px;">
    <p style="font-size: 15px; color: #333; margin: 0; line-height: 1.5;">
        <b>💡 ¿Qué es el Método Simplex?</b><br>
        Simplex es un algoritmo matemático diseñado para encontrar <b>la decisión más inteligente</b> entre miles de combinaciones posibles. En <b>REBEL WINGS</b> lo aplicamos analizando tus ventas, las cargas de trabajo, capacidad productiva y el límite de presupuesto. Simplex cruza todos estos datos para <b>calcular matemáticamente los turnos perfectos</b>, garantizando que nunca falten manos, sin gastar un solo peso de más en nómina, considerando algunas reglas más definidas en la operación.
    </p>
</div>
""", unsafe_allow_html=True)

# --- 🎛️ BARRA LATERAL (CON TODAS LAS VARIABLES DE MODO EDICIÓN) ---
with st.sidebar:
    st.header("💰 Límite Financiero")
    st.number_input("✏️ % exacto:", 10.0, 40.0, st.session_state.tope, 0.5, key="input_num", on_change=sync_tope_num)
    st.slider("🎚️ Ajuste:", 10.0, 40.0, st.session_state.tope, 0.5, key="input_slider", on_change=sync_tope_slider)
    st.markdown("---")
    st.header("🔐 Configuración Maestra")
    if not st.session_state['config_unlocked']:
        pwd = st.text_input("Contraseña:", type="password")
        if st.button("🔓 Desbloquear", type="primary"):
            if pwd == "M@5terkey": st.session_state['config_unlocked'] = True; st.rerun()
            else: st.error("Error.")
    else:
        st.success("🔓 Modo Edición Activo")
        with st.expander("💵 Ajuste de Salarios Fijos"):
            new_s_sup = st.number_input("Salario ⭐️ Supervisor ($)", value=config_data['s_sup'])
            new_s_caj = st.number_input("Salario 🖥️ Caja ($)", value=config_data['s_caj'])
            new_s_coc = st.number_input("Salario 🍳 Cocinero ($)", value=config_data['s_coc'])
            new_s_ven = st.number_input("Salario 🍔 Vendedor ($)", value=config_data['s_ven'])
            new_s_bar = st.number_input("Salario 🍺 Barra ($)", value=config_data['s_bar'])
            new_s_emp = st.number_input("Salario 📦 Empacador ($)", value=config_data.get('s_emp', 250.0))
            new_s_aux = st.number_input("Salario 🧹 Auxiliar ($)", value=config_data.get('s_aux', 250.0))
            new_s_hos = st.number_input("Salario 🛎️ Hostes ($)", value=config_data['s_hos'])
            
        with st.expander("⚙️ Capacidad Productiva"):
            new_c_coc = st.number_input("Capacidad Productiva Cocina (comandas/hora)", value=config_data['c_coc'])
            new_c_sal = st.number_input("Capacidad Productiva Salón (comandas/hora)", value=config_data['c_sal'])
            new_c_bar = st.number_input("Capacidad Productiva Barra (comandas/hora)", value=config_data['c_bar'])
            
        with st.expander("🎯 Límites de Plantilla Fija (Ideal)"):
            new_ideal_sup = st.number_input("Límite Ideal ⭐️ Supervisor", min_value=0, value=config_data.get('ideal_sup', 2))
            new_ideal_caj = st.number_input("Límite Ideal 🖥️ Caja", min_value=0, value=config_data.get('ideal_caj', 3))
            new_ideal_emp = st.number_input("Límite Ideal 📦 Empacador", min_value=0, value=config_data.get('ideal_emp', 2))
            new_ideal_aux = st.number_input("Límite Ideal 🧹 Auxiliar", min_value=0, value=config_data.get('ideal_aux', 2))
            new_ideal_hos = st.number_input("Límite Ideal 🛎️ Hostes", min_value=0, value=config_data.get('ideal_hos', 3))
            
        with st.expander("🎉 Configurar Días Festivos"):
            new_esp = {}
            for d in dias_semana:
                val_actual = float(config_data.get('esp_pct', {}).get(d, 0.0))
                new_esp[d] = st.number_input(f"Día Festivo: Incremento para {d} (%)", min_value=0.0, value=val_actual, step=5.0)
                
        if st.button("🔒 Guardar y Bloquear", type="primary"):
            config_data.update({
                's_coc': new_s_coc, 's_ven': new_s_ven, 's_bar': new_s_bar, 's_sup': new_s_sup, 's_caj': new_s_caj, 's_hos': new_s_hos, 
                's_emp': new_s_emp, 's_aux': new_s_aux, 'c_coc': new_c_coc, 'c_sal': new_c_sal, 'c_bar': new_c_bar, 'esp_pct': new_esp,
                'ideal_sup': new_ideal_sup, 'ideal_caj': new_ideal_caj, 'ideal_hos': new_ideal_hos, 'ideal_emp': new_ideal_emp, 'ideal_aux': new_ideal_aux
            })
            save_config(config_data)
            st.session_state['config_unlocked'] = False
            st.rerun()

    st.markdown("---")
    st.header("🖨️ Exportar")
    modo_impresion = st.checkbox("📄 Vista para PDF")

s_coc, s_ven, s_bar, s_sup, s_caj, s_hos, s_emp, s_aux = config_data['s_coc'], config_data['s_ven'], config_data['s_bar'], config_data['s_sup'], config_data['s_caj'], config_data['s_hos'], config_data.get('s_emp', 250.0), config_data.get('s_aux', 250.0)
c_coc, c_sal, c_bar = config_data['c_coc'], config_data['c_sal'], config_data['c_bar']
esp_pct = config_data.get('esp_pct', {d: 0.0 for d in dias_semana})
ideal_sup_cfg, ideal_caj_cfg, ideal_hos_cfg, ideal_emp_cfg, ideal_aux_cfg = config_data.get('ideal_sup', 2), config_data.get('ideal_caj', 3), config_data.get('ideal_hos', 3), config_data.get('ideal_emp', 2), config_data.get('ideal_aux', 2)
salarios_map = {'Supervisor': s_sup, 'Caja': s_caj, 'Cocinero': s_coc, 'Vendedor': s_ven, 'Barra': s_bar, 'Empacador': s_emp, 'Auxiliar': s_aux, 'Hostes': s_hos}

# ==========================================
# 🚀 PANTALLA PRINCIPAL: FLUJO DE PASOS
# ==========================================
tab_carga, tab_diario, tab_semanal, tab_ideal = st.tabs(["📥 1. CARGA DE DATOS", "📅 2. RESUMEN DIARIO", "📊 3. GRAN RESUMEN SEMANAL", "⚖️ 4. PLANTILLA IDEAL VS REAL"])

with tab_carga:
    st.markdown("### 1️⃣ PASO 1: Descarga o Sube tu Excel")
    c_up1, c_up2 = st.columns(2)
    with c_up1: 
        st.download_button(label="📥 Descargar Machote de Excel", data=generar_machote(), file_name="Machote_Semanal.xlsx", type="secondary")
    with c_up2: 
        uploaded_file = st.file_uploader("Arrastra tu Excel aquí", type=["xlsx"], label_visibility="collapsed")
        
        if uploaded_file is not None:
            if st.button("⚙️ Leer Datos del Excel", type="secondary"):
                try:
                    df_v = pd.read_excel(uploaded_file, sheet_name="Ventas")
                    df_eq = pd.read_excel(uploaded_file, sheet_name="Equipo_Actual")
                    df_f = pd.read_excel(uploaded_file, sheet_name="Personal_Fijo")
                    df_d = pd.read_excel(uploaded_file, sheet_name="Demanda")
                    
                    st.session_state.df_ventas = df_v
                    if "editor_ventas" in st.session_state: del st.session_state["editor_ventas"]
                    
                    st.session_state.c_sup = int(df_eq.loc[df_eq['Parámetro'] == 'Supervisor', 'Valor'].values[0])
                    st.session_state.c_caj = int(df_eq.loc[df_eq['Parámetro'] == 'Caja', 'Valor'].values[0])
                    st.session_state.c_coc = int(df_eq.loc[df_eq['Parámetro'] == 'Cocinero', 'Valor'].values[0])
                    st.session_state.c_sal = int(df_eq.loc[df_eq['Parámetro'] == 'Vendedor', 'Valor'].values[0])
                    st.session_state.c_bar = int(df_eq.loc[df_eq['Parámetro'] == 'Barra', 'Valor'].values[0])
                    st.session_state.c_emp = int(df_eq.loc[df_eq['Parámetro'] == 'Empacador', 'Valor'].values[0])
                    st.session_state.c_aux = int(df_eq.loc[df_eq['Parámetro'] == 'Auxiliar', 'Valor'].values[0])
                    st.session_state.c_hos = int(df_eq.loc[df_eq['Parámetro'] == 'Hostes', 'Valor'].values[0])
                    st.session_state.descanso_sup = str(df_eq.loc[df_eq['Parámetro'] == 'Descanso_Supervisor', 'Valor'].values[0])

                    for col in df_f.columns:
                        if col != "Día": df_f[col] = df_f[col].astype(str).str.strip().str.lower() == 'si'
                    
                    for p in puestos_fijos:
                        for idx, d in enumerate(dias_semana):
                            try:
                                row_data = df_f[df_f['Día'].str.strip() == d].iloc[0]
                                st.session_state.df_fijos_dict[p].loc[idx, 'Matutino'] = bool(row_data.get(f"{p}_Matutino", False))
                                st.session_state.df_fijos_dict[p].loc[idx, 'Intermedio'] = bool(row_data.get(f"{p}_Intermedio", False))
                                st.session_state.df_fijos_dict[p].loc[idx, 'Vespertino'] = bool(row_data.get(f"{p}_Vespertino", False))
                            except: pass 
                        st.session_state[f'counter_{p}'] += 1 
                            
                    st.session_state.df_demanda = df_d
                    st.session_state['counter_demanda'] += 1
                    
                    st.success("✅ ¡Datos de Excel leídos correctamente!")
                except Exception as e: st.error(f"⚠️ Error al leer Excel: {e}")

    # URL del endpoint
    url = "https://operamx.no-ip.net/back/api_tickets/api/Catalogos/getSucursales"

    # Intentar obtener datos
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        sucursales = response.json()
    except Exception as e:
        st.error(f"Error al conectar con el servidor: {e}")
        sucursales = []

            # Si hay datos, mostrar el selectbox
    if sucursales:
        sucursal_seleccionada = st.selectbox(
                    "SELECCIONA UNA SUCURSAL:",
                    sucursales,
                    format_func=lambda s: f"{s['name']}"  # muestra código y nombre
                    )
    else:
        st.info("No se pudieron cargar las sucursales.")
            
    # Año actual
    today = datetime.date.today()
    year = today.year

    # Calcular la última semana del año (semana que contiene el 31 de diciembre)
    last_day = datetime.date(year, 12, 31)
    max_week = week_number(last_day)

    # Crear lista de números de semana
    weeks = list(range(1, max_week + 1))

    # Obtener la semana actual
    current_week = week_number(today)

    # Buscar el índice de la semana actual en la lista
    # (Si por algún motivo no está, se puede elegir un valor por defecto, ej. 0)
    try:
        default_index = weeks.index(current_week)
    except ValueError:
        # En caso de que la semana actual no esté en la lista (p.ej., transición de año)
        default_index = 0  # Selecciona la primera semana

    # Selectbox en Streamlit con la semana actual preseleccionada
    selected_week = st.selectbox(
        "SELECCIONA LA SEMANA",
        weeks,
        index=default_index
    )
    fi, ff = get_week_dates(year, selected_week)
    st.button(
    "CARGAR INFORMACIÓN",
    on_click=lambda: consultarSimplex(sucursal_seleccionada["cod"], fi, ff),
    use_container_width=True   # Nota: es use_container_width, no "width"
    )

    if selected_week:
        inicio, fin = get_week_dates(year, selected_week)
        st.write(f"Semana **{selected_week}**: desde **{inicio}** hasta **{fin}**")


    st.markdown("---")
    st.markdown("### 2️⃣ PASO 2: Verifica o Captura tu Operación (Manual)")
    
    t_ven, t_equ, t_fij, t_dem = st.tabs(["💰 Ventas", "👥 Tu Equipo Actual", "📌 Personal Fijo (Turnos)", "📊 Demanda Operativa"])
    
    with t_ven:
        st.markdown("""<div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 5px; margin-bottom: 20px;"><p style="font-size: 14px; color: #333; margin: 0;"><b>💡 Guía:</b> Captura la proyección de venta diaria esperada. Simplex tomará este dinero y le aplicará el % Límite Financiero para calcular tu presupuesto máximo de nómina para cada día.</p></div>""", unsafe_allow_html=True)
        st.session_state.df_ventas_edited = st.data_editor(st.session_state.df_ventas, use_container_width=False, hide_index=True, height=300, key="editor_ventas")
    
    with t_equ:
        st.markdown("""<div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 5px; margin-bottom: 20px;"><p style="font-size: 14px; color: #333; margin: 0;"><b>💡 Guía:</b> Aquí capturas cuánta gente tienes HOY en la nómina contratada. El sistema usará estos datos al final para decirte exactamente si te falta personal (para operar sin colapsar) o si te sobra gente (y estás fugando dinero). También eliges qué día descansa el Supervisor.</p></div>""", unsafe_allow_html=True)
        st.session_state['descanso_sup'] = st.selectbox("🏖️ Día de Descanso del Supervisor:", dias_semana, index=dias_semana.index(st.session_state.descanso_sup) if st.session_state.descanso_sup in dias_semana else 1)
        c_rh1, c_rh2, c_rh3, c_rh4 = st.columns(4)
        with c_rh1:
            st.session_state['c_sup'] = st.number_input("⭐️ Supervisor", 0, value=st.session_state.get('c_sup', 0))
            st.session_state['c_caj'] = st.number_input("🖥️ Caja", 0, value=st.session_state.get('c_caj', 0))
        with c_rh2:
            st.session_state['c_coc'] = st.number_input("🍳 Cocinero", 0, value=st.session_state.get('c_coc', 0))
            st.session_state['c_sal'] = st.number_input("🍔 Vendedor", 0, value=st.session_state.get('c_sal', 0))
        with c_rh3:
            st.session_state['c_bar'] = st.number_input("🍺 Barra", 0, value=st.session_state.get('c_bar', 0))
            st.session_state['c_emp'] = st.number_input("📦 Empacador", 0, value=st.session_state.get('c_emp', 0))
        with c_rh4:
            st.session_state['c_aux'] = st.number_input("🧹 Auxiliar", 0, value=st.session_state.get('c_aux', 0))
            st.session_state['c_hos'] = st.number_input("🛎️ Hostes", 0, value=st.session_state.get('c_hos', 0))
            
    with t_fij:
        st.markdown("""<div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 5px; margin-bottom: 20px;"><p style="font-size: 14px; color: #333; margin: 0;"><b>💡 Guía:</b> Activa la casilla si quieres obligar al sistema a poner a alguien de este puesto en ese turno. Déjala vacía si prefieres darle el día o el turno de descanso. (Usa los botones rápidos para llenar una columna entera en un segundo).</p></div>""", unsafe_allow_html=True)
        tabs_puestos = st.tabs(["⭐️ Supervisor", "🖥️ Caja", "🛎️ Hostes", "📦 Empacador", "🧹 Auxiliar"])
        
        for idx, p in enumerate(puestos_fijos):
            with tabs_puestos[idx]:
                
                df_current = st.session_state.df_fijos_dict[p]
                
                b1, b2, b3, b4 = st.columns(4)
                b1.button(f"🧹 Limpiar Todo", key=f"btn_c_{p}", on_click=clear_all_fijos, args=(p,))
                b2.button(f"✅ Todo Matutino", key=f"btn_m_{p}", on_click=update_all_fijos, args=(p, 'Matutino', True))
                b3.button(f"✅ Todo Intermedio", key=f"btn_i_{p}", on_click=update_all_fijos, args=(p, 'Intermedio', True))
                b4.button(f"✅ Todo Vespertino", key=f"btn_v_{p}", on_click=update_all_fijos, args=(p, 'Vespertino', True))
                
                st.session_state[f"df_fijos_{p}_edited"] = st.data_editor(
                    df_current, 
                    use_container_width=True, 
                    hide_index=True, 
                    height=295, 
                    key=f"editor_fijos_{p}_{st.session_state[f'counter_{p}']}",
                    column_config={
                        "Día": st.column_config.TextColumn("Día", disabled=True),
                        "Matutino": st.column_config.CheckboxColumn("☀️ Matutino", default=False),
                        "Intermedio": st.column_config.CheckboxColumn("🌤️ Intermedio", default=False),
                        "Vespertino": st.column_config.CheckboxColumn("🌙 Vespertino", default=False)
                    }
                )
        
    with t_dem:
        st.markdown("""<div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 5px; margin-bottom: 20px;"><p style="font-size: 14px; color: #333; margin: 0;"><b>💡 Guía:</b> Captura cuántas comandas estimas procesar por bloque de horas (esto mide tu "Rush"). <b>Nota:</b> El Panel Rápido solo inyecta horas en apertura (Bloque 1) o cierre (Bloque 5). Si ocupas horas extra en otro horario, captúralo manual en la tabla.</p></div>""", unsafe_allow_html=True)
        st.markdown("#### ⚡ Panel de Asignación Rápida (Horas Extra)")
        
        c_i1, c_i2, c_i3, c_i4, c_i5, c_i6 = st.columns([1.5, 1.5, 1.5, 1, 1.5, 1.5])
        with c_i1: dia_qa = st.selectbox("📅 Día", ["Todos"] + dias_semana)
        with c_i2: bloque_qa = st.selectbox("🕒 Turno", ["☀️ Matutino", "🌙 Vespertino"])
        with c_i3: area_qa = st.selectbox("🎯 Área", ["Todas", "🍳 Cocina", "🍔 Salón", "🍺 Barra"])
        with c_i4: hrs_qa = st.number_input("⏱️ Horas", 0.0, 5.0, 1.0, 0.5)
        
        with c_i5: 
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("⚡ Inyectar Extras", type="primary", use_container_width=True, on_click=inyectar_horas_extra, args=(dia_qa, bloque_qa, area_qa, hrs_qa))
        with c_i6:
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("🧹 Borrar Extras", type="secondary", use_container_width=True, on_click=limpiar_horas_extra)
            
        st.markdown("---")
        st.markdown("**📊 Tabla Detallada de Operación**")
        st.session_state.df_demanda_edited = st.data_editor(
            st.session_state.df_demanda, 
            use_container_width=True, 
            hide_index=True, 
            height=1300, 
            key=f"editor_demanda_{st.session_state['counter_demanda']}"
        )

    st.markdown("---")
    st.markdown("### 3️⃣ PASO 3: Optimización Matemática")
    if st.button("🚀 CALCULAR PLANTILLA IDEAL (CLICK AQUÍ)", type="primary", use_container_width=True):
        
        st.session_state.db = {'ventas': {}, 'fijos': {}, 'demanda': {}}
        for d in dias_semana:
            st.session_state.db['ventas'][d] = 0.0
            st.session_state.db['fijos'][d] = {}
            st.session_state.db['demanda'][d] = {'cc': [0]*5, 'ec': [0]*5, 'cs': [0]*5, 'es': [0]*5, 'cb': [0]*5, 'eb': [0]*5}

        def get_venta_val(dia):
            try: return float(st.session_state.df_ventas_edited.loc[st.session_state.df_ventas_edited['Día'].astype(str).str.strip() == dia, 'Venta Proyectada ($)'].values[0])
            except: return 20000.0

        def get_fijo_val(puesto, dia, turno):
            try:
                df_p = st.session_state[f"df_fijos_{puesto}_edited"]
                return bool(df_p.loc[df_p['Día'].astype(str).str.strip() == dia, turno].values[0])
            except: return False

        def get_dem_val(dia, bloque, col):
            try:
                df = st.session_state.df_demanda_edited
                return float(df.loc[(df['Día'].astype(str).str.strip() == dia) & (df['Bloque'].astype(str).str.strip() == bloque), col].values[0])
            except: return 0.0

        for d in dias_semana:
            st.session_state.db['ventas'][d] = get_venta_val(d)
            st.session_state.db['fijos'][d] = {
                'sm': get_fijo_val('Supervisor', d, 'Matutino'), 'si': get_fijo_val('Supervisor', d, 'Intermedio'), 'sv': get_fijo_val('Supervisor', d, 'Vespertino'),
                'cm': get_fijo_val('Caja', d, 'Matutino'), 'ci': get_fijo_val('Caja', d, 'Intermedio'), 'cv': get_fijo_val('Caja', d, 'Vespertino'),
                'hm': get_fijo_val('Hostes', d, 'Matutino'), 'hi': get_fijo_val('Hostes', d, 'Intermedio'), 'hv': get_fijo_val('Hostes', d, 'Vespertino'),
                'em': get_fijo_val('Empacador', d, 'Matutino'), 'ei': get_fijo_val('Empacador', d, 'Intermedio'), 'ev': get_fijo_val('Empacador', d, 'Vespertino'),
                'am': get_fijo_val('Auxiliar', d, 'Matutino'), 'ai': get_fijo_val('Auxiliar', d, 'Intermedio'), 'av': get_fijo_val('Auxiliar', d, 'Vespertino')
            }
            for i, b in enumerate(bloques):
                st.session_state.db['demanda'][d]['cc'][i] = get_dem_val(d, b, '🍳 Cmds Cocina'); st.session_state.db['demanda'][d]['ec'][i] = get_dem_val(d, b, '🍳 Extra Cocina')
                st.session_state.db['demanda'][d]['cs'][i] = get_dem_val(d, b, '🍔 Cmds Salón');  st.session_state.db['demanda'][d]['es'][i] = get_dem_val(d, b, '🍔 Extra Salón')
                st.session_state.db['demanda'][d]['cb'][i] = get_dem_val(d, b, '🍺 Cmds Barra');  st.session_state.db['demanda'][d]['eb'][i] = get_dem_val(d, b, '🍺 Extra Barra')
        
        progress_container = st.empty()
        with progress_container.container():
            bar = st.progress(0)
            for i in range(10): bar.progress((i + 1) * 10); time.sleep(0.05) 
        
        resultados_diarios = {}; costo_total_semana = 0; venta_total_semana = 0; dias_inviables = []; turnos_semanales = {'Cocina': 0, 'Salon': 0, 'Barra': 0} 
        capacidades = {'Cocina': c_coc, 'Salon': c_sal, 'Barra': c_bar}; roles = ['Cocina', 'Salon', 'Barra']; turnos = ['M', 'I', 'V']
        
        for d in dias_semana:
            modelo = pl.LpProblem(f"Opt_{d}", pl.LpMinimize)
            vars_personal = pl.LpVariable.dicts(f"Pers_{d}", [(r, t) for r in roles for t in turnos], lowBound=0, cat='Integer')
            modelo += pl.lpSum([vars_personal[(r, t)] for r in roles for t in turnos])
            
            factor_crecimiento = 1.0 + (float(esp_pct.get(d, 0.0)) / 100.0)
            venta_ajustada = st.session_state.db['ventas'][d] * factor_crecimiento
            venta_total_semana += venta_ajustada 
            
            demandas = {'Cocina': [cmd * factor_crecimiento for cmd in st.session_state.db['demanda'][d]['cc']], 'Salon':  [cmd * factor_crecimiento for cmd in st.session_state.db['demanda'][d]['cs']], 'Barra':  [cmd * factor_crecimiento for cmd in st.session_state.db['demanda'][d]['cb']]}
            extras = {'Cocina': st.session_state.db['demanda'][d]['ec'], 'Salon':  st.session_state.db['demanda'][d]['es'], 'Barra':  st.session_state.db['demanda'][d]['eb']}
            plot_data_req = {'Cocina': [], 'Salon': [], 'Barra': []}; plot_data_prov = {'Cocina': [], 'Salon': [], 'Barra': []}
            
            for r in roles:
                for i in range(5):
                    req_horas = (demandas[r][i] / capacidades[r]) + extras[r][i]
                    if i == 0: gente = vars_personal[(r, 'M')]
                    elif i == 1: gente = vars_personal[(r, 'M')] + vars_personal[(r, 'I')]
                    elif i == 2: gente = vars_personal[(r, 'M')] + vars_personal[(r, 'I')] + vars_personal[(r, 'V')]
                    elif i == 3: gente = vars_personal[(r, 'I')] + vars_personal[(r, 'V')]
                    elif i == 4: gente = vars_personal[(r, 'V')]
                    modelo += (gente * horas_por_bloque[i]) >= req_horas

            sm_val, si_val, sv_val = (False, False, False) if d == st.session_state['descanso_sup'] else (st.session_state.db['fijos'][d]['sm'], st.session_state.db['fijos'][d]['si'], st.session_state.db['fijos'][d]['sv'])
            q_sup = sum([sm_val, si_val, sv_val]); q_caj = sum([st.session_state.db['fijos'][d]['cm'], st.session_state.db['fijos'][d]['ci'], st.session_state.db['fijos'][d]['cv']]); q_hos = sum([st.session_state.db['fijos'][d]['hm'], st.session_state.db['fijos'][d]['hi'], st.session_state.db['fijos'][d]['hv']]); q_emp = sum([st.session_state.db['fijos'][d]['em'], st.session_state.db['fijos'][d]['ei'], st.session_state.db['fijos'][d]['ev']]); q_aux = sum([st.session_state.db['fijos'][d]['am'], st.session_state.db['fijos'][d]['ai'], st.session_state.db['fijos'][d]['av']])
            c_fijo_dia = (q_sup * s_sup) + (q_caj * s_caj) + (q_hos * s_hos) + (q_emp * s_emp) + (q_aux * s_aux)
            presupuesto_diario = venta_ajustada * (st.session_state['tope'] / 100)
            c_var_dia = pl.lpSum([vars_personal[('Cocina', t)] * s_coc + vars_personal[('Salon', t)] * s_ven + vars_personal[('Barra', t)] * s_bar for t in turnos])
            
            modelo += (c_var_dia + c_fijo_dia) <= presupuesto_diario
            if modelo.solve() == 1:
                c_total_dia = pl.value(c_var_dia) + c_fijo_dia
                costo_total_semana += c_total_dia
                for r in roles:
                    for i in range(5):
                        plot_data_req[r].append(round((demandas[r][i] / capacidades[r]) + extras[r][i], 1))
                        if i == 0: g = vars_personal[(r, 'M')].varValue
                        elif i == 1: g = vars_personal[(r, 'M')].varValue + vars_personal[(r, 'I')].varValue
                        elif i == 2: g = vars_personal[(r, 'M')].varValue + vars_personal[(r, 'I')].varValue + vars_personal[(r, 'V')].varValue
                        elif i == 3: g = vars_personal[(r, 'I')].varValue + vars_personal[(r, 'V')].varValue
                        elif i == 4: g = vars_personal[(r, 'V')].varValue
                        plot_data_prov[r].append(round(g * horas_por_bloque[i], 1))
                
                resultados_diarios[d] = {
                    'M': [vars_personal[('Cocina','M')].varValue, vars_personal[('Salon','M')].varValue, vars_personal[('Barra','M')].varValue, int(st.session_state.db['fijos'][d]['cm']), int(sm_val), int(st.session_state.db['fijos'][d]['hm']), int(st.session_state.db['fijos'][d]['em']), int(st.session_state.db['fijos'][d]['am'])] ,
                    'I': [vars_personal[('Cocina','I')].varValue, vars_personal[('Salon','I')].varValue, vars_personal[('Barra','I')].varValue, int(st.session_state.db['fijos'][d]['ci']), int(si_val), int(st.session_state.db['fijos'][d]['hi']), int(st.session_state.db['fijos'][d]['ei']), int(st.session_state.db['fijos'][d]['ai'])] ,
                    'V': [vars_personal[('Cocina','V')].varValue, vars_personal[('Salon','V')].varValue, vars_personal[('Barra','V')].varValue, int(st.session_state.db['fijos'][d]['cv']), int(sv_val), int(st.session_state.db['fijos'][d]['hv']), int(st.session_state.db['fijos'][d]['ev']), int(st.session_state.db['fijos'][d]['av'])] ,
                    'Costo': c_total_dia, 'Costo_Fijo': c_fijo_dia, 'Costo_Var': pl.value(c_var_dia), 'Venta_Ajustada': venta_ajustada, 'Es_Especial': factor_crecimiento > 1.0, 'Pct_Extra': float(esp_pct.get(d, 0.0)), 'req': plot_data_req, 'prov': plot_data_prov, 'demanda_bruta': demandas
                }
                turnos_semanales['Cocina'] += sum([vars_personal[('Cocina', t)].varValue for t in turnos]); turnos_semanales['Salon'] += sum([vars_personal[('Salon', t)].varValue for t in turnos]); turnos_semanales['Barra'] += sum([vars_personal[('Barra', t)].varValue for t in turnos])
            else: dias_inviables.append(d)

        progress_container.empty()
        
        if dias_inviables: st.error(f"⚠️ **Presupuesto Inviable en:** {', '.join(dias_inviables)}. Aumenta el Tope Máximo."); st.session_state['resultados_diarios'] = None
        else:
            st.session_state['resultados_diarios'] = resultados_diarios; st.session_state['venta_total_semana_calc'] = venta_total_semana; st.session_state['costo_total_semana_calc'] = costo_total_semana
            st.session_state['plantilla_ideal'] = {'Supervisor': ideal_sup_cfg, 'Caja': ideal_caj_cfg, 'Cocinero': math.ceil(turnos_semanales['Cocina'] / 6.0), 'Vendedor': math.ceil(turnos_semanales['Salon'] / 6.0), 'Barra': math.ceil(turnos_semanales['Barra'] / 6.0), 'Empacador': ideal_emp_cfg, 'Auxiliar': ideal_aux_cfg, 'Hostes': ideal_hos_cfg}
            st.success("✅ ¡Cálculo Exitoso!")

# ==========================================
# 🧱 RENDERIZADO DE PESTAÑAS (RESULTADOS)
# ==========================================
with tab_diario:
    if st.session_state['resultados_diarios'] is not None:
        st.markdown("""<div style="background-color: #E8F4F8; padding: 15px; border-left: 5px solid #1F77B4; border-radius: 5px; margin-bottom: 20px;"><h4 style="margin-top: 0; color: #1F77B4;">🧠 Análisis Ejecutivo del Cálculo Diario</h4><p style="font-size: 14px; color: #333;"><b>1. Puestos Operativos (🍳 Cocinero, 🍔 Vendedor, 🍺 Barra):</b> El algoritmo analizó las ventas y comandas esperadas. Dividió el volumen entre la capacidad de cada puesto y asignó a las personas justas para cubrir los picos de "Rush", garantizando el servicio sin pasarse del límite de nómina.<br><b>2. Puestos Estructurales (⭐️ Supervisor, 🖥️ Caja, 📦 Empacador, 🧹 Auxiliar, 🛎️ Hostes):</b> Estas posiciones no dependen del volumen de clientes. El sistema leyó tu Machote de Excel para este día y asignó (o descansó) al personal tal como lo configuraste.</p></div>""", unsafe_allow_html=True)
        dia_sel = st.selectbox("👉 Elige el día a analizar:", dias_semana, key="sel_dia_print")
        res = st.session_state['resultados_diarios'][dia_sel]
        venta = res['Venta_Ajustada']
        pct = (res['Costo'] / venta) * 100 if venta > 0 else 0
        
        st.markdown("---")
        if res['Es_Especial']: st.success(f"🎉 **¡DÍA ESPECIAL ACTIVO!** Incremento del **{res['Pct_Extra']:g}%**")
        if dia_sel == st.session_state.get('descanso_sup', ''): st.info(f"🏖️ **DESCANSO DEL SUPERVISOR:** Hoy no se presupuestó al ⭐️ Supervisor.")

        col1, col2, col3 = st.columns(3)
        col1.markdown(f'<div class="anim_metric_blue"><p style="margin:0; font-size:15px; color:#555;">💰 Venta Esperada ({dia_sel})</p><h2 style="margin:0; color:#1F77B4;">$ {venta:,.2f}</h2></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="anim_metric_yellow"><p style="margin:0; font-size:15px; color:#555;">💸 Costo Nómina</p><h2 style="margin:0; color:#B38600;">$ {res["Costo"]:,.2f}</h2></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="anim_metric_green"><p style="margin:0; font-size:15px; color:#555;">📈 % de Nómina</p><h2 style="margin:0; color:#2CA02C;">{pct:.1f} %</h2></div>', unsafe_allow_html=True)
        
        st.write(""); st.info(f"🧐 **Desglose de Nómina:** Costo Fijo: \\$ {res['Costo_Fijo']:,.2f}  |  Costo Variable: \\$ {res['Costo_Var']:,.2f}"); st.markdown("---")
        
        st.subheader(f"📋 Plantilla Asignada para el {dia_sel}")
        t_sup = int(res['M'][4]+res['I'][4]+res['V'][4]); t_caj = int(res['M'][3]+res['I'][3]+res['V'][3]); t_coc = int(res['M'][0]+res['I'][0]+res['V'][0]); t_ven = int(res['M'][1]+res['I'][1]+res['V'][1]); t_bar = int(res['M'][2]+res['I'][2]+res['V'][2]); t_emp = int(res['M'][6]+res['I'][6]+res['V'][6]); t_aux = int(res['M'][7]+res['I'][7]+res['V'][7]); t_hos = int(res['M'][5]+res['I'][5]+res['V'][5])

        df_d = pd.DataFrame([{"Turno": "☀️ Matutino (10-18)", "⭐️ Supervisor": int(res['M'][4]), "🖥️ Caja": int(res['M'][3]), "🍳 Cocinero": int(res['M'][0]), "🍔 Vendedor": int(res['M'][1]), "🍺 Barra": int(res['M'][2]), "📦 Empacador": int(res['M'][6]), "🧹 Auxiliar": int(res['M'][7]), "🛎️ Hostes": int(res['M'][5])}, {"Turno": "🌤️ Intermedio (14-22)", "⭐️ Supervisor": int(res['I'][4]), "🖥️ Caja": int(res['I'][3]), "🍳 Cocinero": int(res['I'][0]), "🍔 Vendedor": int(res['I'][1]), "🍺 Barra": int(res['I'][2]), "📦 Empacador": int(res['I'][6]), "🧹 Auxiliar": int(res['I'][7]), "🛎️ Hostes": int(res['I'][5])}, {"Turno": "🌙 Vespertino (17-01)", "⭐️ Supervisor": int(res['V'][4]), "🖥️ Caja": int(res['V'][3]), "🍳 Cocinero": int(res['V'][0]), "🍔 Vendedor": int(res['V'][1]), "🍺 Barra": int(res['V'][2]), "📦 Empacador": int(res['V'][6]), "🧹 Auxiliar": int(res['V'][7]), "🛎️ Hostes": int(res['V'][5])}, {"Turno": "📌 TOTAL DÍA", "⭐️ Supervisor": t_sup, "🖥️ Caja": t_caj, "🍳 Cocinero": t_coc, "🍔 Vendedor": t_ven, "🍺 Barra": t_bar, "📦 Empacador": t_emp, "🧹 Auxiliar": t_aux, "🛎️ Hostes": t_hos}])
        st.dataframe(df_d.style.set_properties(**{'text-align': 'center'}).apply(lambda row: ['background-color: #1F77B4; color: white; font-weight: bold;'] * len(row) if "📌 TOTAL" in str(row['Turno']) else [''] * len(row), axis=1), height=195, use_container_width=False, hide_index=True)
        st.markdown("---")
        
        st.markdown("### 💎 Radiografía del Restaurante")
        df_rush = pd.DataFrame({'Bloque Horario': bloques * 3, 'Comandas': res['demanda_bruta']['Cocina'] + res['demanda_bruta']['Salon'] + res['demanda_bruta']['Barra'], 'Área': ['🍳 Cocina']*5 + ['🍔 Salón']*5 + ['🍺 Barra']*5})
        st.plotly_chart(px.area(df_rush, x='Bloque Horario', y='Comandas', color='Área', color_discrete_map={'🍳 Cocina': '#FF7F0E', '🍔 Salón': '#1F77B4', '🍺 Barra': '#2CA02C'}), use_container_width=True)
        
        st.markdown("""<div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 5px; margin-bottom: 25px;"><h5 style="margin-top: 0; color: #B38600;">💡 Guía rápida</h5><p style="font-size: 14px; color: #333; margin: 0;">Este gráfico mide el volumen de trabajo en el día. Entre más alta sea la montaña, más clientes hay y más presión recae sobre esa área específica.</p></div>""", unsafe_allow_html=True)
        
        st.markdown("### ⚖️ Cobertura de Personal")
        area = st.radio("Elige el Área Operativa:", ["Cocina", "Salon", "Barra"], horizontal=True)
        sum_n = sum(res['req'][area]); sum_p = sum(res['prov'][area]); p_n = sum_n / 8.0; p_p = int(sum_p / 8.0)

        st.markdown(f"""<div style="display: flex; gap: 20px; margin-bottom: 10px;"><div style="background-color: #fdf2f2; padding: 15px; border-radius: 8px; border: 1px solid #f8d7da; flex: 1; text-align: center;"><div style="color: #d62728; font-weight: bold; font-size: 16px;">🔴 Total Horas Necesarias en el Día: {sum_n:.1f} hrs</div><div style="color: #d62728; font-size: 14px; margin-top: 5px;">👥 <i>Equivale a <b>{p_n:.1f}</b> personas teóricas</i></div></div><div style="background-color: #f2fdf2; padding: 15px; border-radius: 8px; border: 1px solid #d1e7dd; flex: 1; text-align: center;"><div style="color: #2ca02c; font-weight: bold; font-size: 16px;">🟢 Total Horas Programadas (Personal): {sum_p:.1f} hrs</div><div style="color: #2ca02c; font-size: 14px; margin-top: 5px;">👥 <i>Equivale a <b>{p_p}</b> personas reales</i></div></div></div>""", unsafe_allow_html=True)

        fig_bar = px.bar(pd.DataFrame({'Horario': bloques * 2, 'Horas': res['req'][area] + res['prov'][area], 'Indicador': ['1. Horas NECESARIAS (Demanda)']*5 + ['2. Horas PROGRAMADAS (Personal)']*5}), x='Horario', y='Horas', color='Indicador', barmode='group', text_auto='.1f', color_discrete_map={'1. Horas NECESARIAS (Demanda)': '#d62728', '2. Horas PROGRAMADAS (Personal)': '#2ca02c'})
        fig_bar.update_layout(legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_bar, use_container_width=True)
        
        st.markdown(f"""
        <div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 5px; margin-bottom: 25px;">
            <h5 style="margin-top: 0; color: #B38600;">💡 Guía rápida</h5>
            <p style="font-size: 14px; color: #333; margin: 0;">
                <b>La meta:</b> La barra Verde siempre debe cubrir o superar a la Roja. <b>Si dejamos menos personas de las indicadas, no se alcanza a cubrir la necesidad y el personal no sería suficiente para garantizar el servicio.</b><br><br>
                <b>¿Por qué pide {p_p} personas si solo necesito {p_n:.1f}?</b><br>
                El {p_n:.1f} es un promedio matemático. El sistema detecta el "Rush" y te asigna a las {p_p} personas completas necesarias en ese pico crítico para que el servicio no colapse.<br><br>
                <b>¿Por qué hay 5 horarios en la gráfica si solo operamos con 3 turnos?</b><br>
                Tenemos 3 turnos: <b>MATUTINO</b>, <b>INTERMEDIO</b> y <b>VESPERTINO</b>. Al empalmarse estos turnos, el día se divide en 5 bloques operativos ({", ".join(bloques)}). Las montañas verdes más altas se forman justo cuando los turnos se cruzan.
            </p>
        </div>
        """, unsafe_allow_html=True)

with tab_semanal:
    if st.session_state['resultados_diarios'] is not None:
        st.markdown("""<div style="background-color: #FFF3E0; padding: 15px; border-left: 5px solid #FF9800; border-radius: 5px; margin-bottom: 20px;"><h4 style="margin-top: 0; color: #FF9800;">🧠 Análisis Ejecutivo Semanal</h4><p style="font-size: 14px; color: #333;">La <b>Plantilla Maestra Semanal</b> consolida todos los turnos diarios; es tu hoja de ruta final para convocar al equipo sin salirte del presupuesto.</p></div>""", unsafe_allow_html=True)
        v_tot = st.session_state['venta_total_semana_calc']
        c_tot = st.session_state['costo_total_semana_calc']
        pct = (c_tot / v_tot) * 100 if v_tot > 0 else 0
        
        col1, col2, col3 = st.columns(3)
        col1.markdown(f'<div class="anim_metric_blue"><p style="margin:0; font-size:15px; color:#555;">💰 Venta Total Proyectada</p><h2 style="margin:0; color:#1F77B4;">$ {v_tot:,.2f}</h2></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="anim_metric_yellow"><p style="margin:0; font-size:15px; color:#555;">💸 Costo Total Nómina</p><h2 style="margin:0; color:#B38600;">$ {c_tot:,.2f}</h2></div>', unsafe_allow_html=True)
        col3.markdown(f'<div class="anim_metric_green"><p style="margin:0; font-size:15px; color:#555;">🏆 % Nómina Promedio</p><h2 style="margin:0; color:#2CA02C;">{pct:.1f} %</h2></div>', unsafe_allow_html=True)
        
        st.write(""); st.markdown("---")
        fig_sem = px.bar(pd.DataFrame({'Día': dias_semana * 2, 'Dinero ($)': [st.session_state['resultados_diarios'][d]['Venta_Ajustada'] for d in dias_semana] + [st.session_state['resultados_diarios'][d]['Costo'] for d in dias_semana], 'Concepto': ['1. Venta Esperada']*7 + ['2. Costo de Nómina']*7}), x='Día', y='Dinero ($)', color='Concepto', barmode='group', text_auto='.2s', color_discrete_map={'1. Venta Esperada': '#2ca02c', '2. Costo de Nómina': '#d62728'})
        fig_sem.update_layout(legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_sem, use_container_width=True)
        
        st.markdown("""<div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 5px; margin-bottom: 25px;"><h5 style="margin-top: 0; color: #B38600;">💡 Guía rápida</h5><p style="font-size: 14px; color: #333; margin: 0;">Compara visualmente tus ventas contra tu nómina. Permite detectar de un vistazo los días más rentables (barras verdes altas) contra los días más caros de operar.</p></div>""", unsafe_allow_html=True)
        
        st.markdown("---"); st.subheader("📋 Tu Plantilla Maestra Semanal")
        filas_maestras = []
        for d in dias_semana:
            res = st.session_state['resultados_diarios'][d]
            n_dia = d
            if res['Es_Especial']: n_dia += f" ⭐ (+{res['Pct_Extra']:g}%)"
            if d == st.session_state.get('descanso_sup', ''): n_dia += " 🏖️(Descanso Sup)"
            
            filas_maestras.append({"Día": n_dia, "Turno": "☀️ Matutino", "⭐️ Supervisor": int(res['M'][4]), "🖥️ Caja": int(res['M'][3]), "🍳 Cocinero": int(res['M'][0]), "🍔 Vendedor": int(res['M'][1]), "🍺 Barra": int(res['M'][2]), "📦 Empacador": int(res['M'][6]), "🧹 Auxiliar": int(res['M'][7]), "🛎️ Hostes": int(res['M'][5]), "Costo del Día": f"$ {res['Costo']:,.2f}"})
            filas_maestras.append({"Día": n_dia, "Turno": "🌤️ Intermedio", "⭐️ Supervisor": int(res['I'][4]), "🖥️ Caja": int(res['I'][3]), "🍳 Cocinero": int(res['I'][0]), "🍔 Vendedor": int(res['I'][1]), "🍺 Barra": int(res['I'][2]), "📦 Empacador": int(res['I'][6]), "🧹 Auxiliar": int(res['I'][7]), "🛎️ Hostes": int(res['I'][5]), "Costo del Día": "---"})
            filas_maestras.append({"Día": n_dia, "Turno": "🌙 Vespertino", "⭐️ Supervisor": int(res['V'][4]), "🖥️ Caja": int(res['V'][3]), "🍳 Cocinero": int(res['V'][0]), "🍔 Vendedor": int(res['V'][1]), "🍺 Barra": int(res['V'][2]), "📦 Empacador": int(res['V'][6]), "🧹 Auxiliar": int(res['V'][7]), "🛎️ Hostes": int(res['V'][5]), "Costo del Día": "---"})
            
        t_sup = sum(f['⭐️ Supervisor'] for f in filas_maestras); t_caj = sum(f['🖥️ Caja'] for f in filas_maestras); t_coc = sum(f['🍳 Cocinero'] for f in filas_maestras); t_ven = sum(f['🍔 Vendedor'] for f in filas_maestras); t_bar = sum(f['🍺 Barra'] for f in filas_maestras); t_emp = sum(f['📦 Empacador'] for f in filas_maestras); t_aux = sum(f['🧹 Auxiliar'] for f in filas_maestras); t_hos = sum(f['🛎️ Hostes'] for f in filas_maestras)
        filas_maestras.append({"Día": "📌 TOTAL SEMANA", "Turno": "---", "⭐️ Supervisor": t_sup, "🖥️ Caja": t_caj, "🍳 Cocinero": t_coc, "🍔 Vendedor": t_ven, "🍺 Barra": t_bar, "📦 Empacador": t_emp, "🧹 Auxiliar": t_aux, "🛎️ Hostes": t_hos, "Costo del Día": f"$ {c_tot:,.2f}"})

        df_maestra = pd.DataFrame(filas_maestras)
        dias_alternos = ["Domingo", "Martes", "Jueves", "Sábado"]
        def color_filas(row):
            dia_str = str(row['Día'])
            if "📌 TOTAL" in dia_str: return ['background-color: #FF9800; color: white; font-weight: bold;'] * len(row) 
            elif "⭐" in dia_str: return ['background-color: rgba(255, 215, 0, 0.25)'] * len(row) 
            elif any(d in dia_str for d in dias_alternos): return ['background-color: rgba(130, 130, 130, 0.20)'] * len(row) 
            else: return [''] * len(row) 
        
        st.dataframe(df_maestra.style.set_properties(**{'text-align': 'center'}).apply(color_filas, axis=1), height=830, use_container_width=False, hide_index=True, column_config={"Día": st.column_config.TextColumn("Día", width=250)})

with tab_ideal:
    if st.session_state['resultados_diarios'] is not None:
        st.markdown("""<div style="background-color: #F3E5F5; padding: 15px; border-left: 5px solid #9C27B0; border-radius: 5px; margin-bottom: 20px;"><h4 style="margin-top: 0; color: #9C27B0;">🧠 Análisis Ejecutivo de Contratación (Plantilla Ideal)</h4><p style="font-size: 14px; color: #333;"><b>1. Operativos:</b> El sistema sumó todos los turnos que te pidió la "Plantilla Maestra Semanal" y los dividió entre 6 días. Al redondear matemáticamente hacia arriba (Regla 6x1), el algoritmo te dice exactamente el número de empleados que necesitas contratar para que tu restaurante cubra todos sus turnos <b>y al mismo tiempo garantices que todos descansen 1 día a la semana.</b><br><b>2. Estructurales Fijos:</b> El sistema respeta el límite de personal "Ideal" que tú configuraste en el panel lateral.</p></div>""", unsafe_allow_html=True)
        st.subheader("⚖️ Análisis Financiero de Recursos Humanos")
        ideal = st.session_state['plantilla_ideal']
        real = {'Supervisor': st.session_state.c_sup, 'Caja': st.session_state.c_caj, 'Cocinero': st.session_state.c_coc, 'Vendedor': st.session_state.c_sal, 'Barra': st.session_state.c_bar, 'Empacador': st.session_state.c_emp, 'Auxiliar': st.session_state.c_aux, 'Hostes': st.session_state.c_hos}
        
        fuga, ahorro = 0, 0
        for puesto in ideal.keys():
            dif = real[puesto] - ideal[puesto]; impacto = dif * salarios_map[puesto] * 7
            if dif > 0: fuga += impacto
            elif dif < 0: ahorro += abs(impacto)
                
        col1, col2 = st.columns(2)
        col1.markdown(f'<div class="anim_fuga"><p style="margin:0; font-size:15px; color:#555;">🔴 FUGA DE DINERO (Exceso de Plantilla)</p><h2 style="margin:0; color:#333;">$ {fuga:,.2f} / sem</h2></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="anim_ahorro"><p style="margin:0; font-size:15px; color:#555;">🟡 AHORRO RIESGOSO (Falta de Plantilla)</p><h2 style="margin:0; color:#333;">$ {ahorro:,.2f} / sem</h2></div>', unsafe_allow_html=True)
        st.write("<br>💡 **Nota Financiera:** Si tienes una **Fuga** 🔴, pagas nómina que no necesitas. Si tienes **Ahorro Riesgoso** 🟡, ahorras dinero, pero el personal está sobrecargado y el servicio corre peligro.", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("### 📋 Diagnóstico Detallado (Tarjetas de Impacto)")
        iconos = {'Supervisor': '⭐️', 'Caja': '🖥️', 'Cocinero': '🍳', 'Vendedor': '🍔', 'Barra': '🍺', 'Empacador': '📦', 'Auxiliar': '🧹', 'Hostes': '🛎️'}
        puestos = list(ideal.keys())
        for i in range(0, len(puestos), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(puestos):
                    p = puestos[i + j]; dif = real[p] - ideal[p]; cost = abs(dif) * salarios_map[p] * 7
                    if dif < 0: bg, text, border, est, msg, anim = "#FFFFE0", "#B38600", "#FFE680", f"Faltan {abs(dif)} persona(s)", f"🟡 Ahorro Riesgoso:<br>+\\$ {cost:,.2f} /sem", "anim_ahorro"
                    elif dif > 0: bg, text, border, est, msg, anim = "#FFF0F0", "#CC0000", "#FFCCCC", f"Sobran {dif} persona(s)", f"🔴 Fuga:<br>-\\$ {cost:,.2f} /sem", "anim_fuga"
                    else: bg, text, border, est, msg, anim = "#F0FFF0", "#008000", "#CCFFCC", "Plantilla Perfecta", f"🟢 Balance:<br>\\$ 0.00", ""
                    cols[j].markdown(f'<div class="{anim}" style="background-color: {bg}; border: 1px solid {border}; border-radius: 10px; padding: 15px; min-height: 160px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 15px;"><h4 style="margin: 0 0 10px 0; color: #333; font-size: 17px; line-height: 1.2;">{iconos[p]} {p}</h4><p style="margin: 0 0 5px 0; font-size: 14px; color: #333; line-height: 1.2;"><b>{est}</b></p><p style="margin: 0 0 10px 0; font-size: 12px; color: #666; line-height: 1.2;">(Ideal: {ideal[p]} | Tienes: {real[p]})</p><h5 style="margin: 0; color: {text}; font-size: 16px; line-height: 1.4;">{msg}</h5></div>', unsafe_allow_html=True)

        st.markdown("---"); st.markdown("### 📊 Comparativo Gráfico (Ideal vs Real)")
        nombres_con_icono = [f"{iconos[p]} {p}" for p in ideal.keys()]
        df_rh = pd.DataFrame({'Puesto': nombres_con_icono * 2, 'Empleados': list(ideal.values()) + list(real.values()), 'Tipo': ['1. Plantilla IDEAL (Requerida)'] * 8 + ['2. Plantilla REAL (Contratada)'] * 8})
        fig_rh = px.bar(df_rh, x='Puesto', y='Empleados', color='Tipo', barmode='group', text_auto=True, color_discrete_map={'1. Plantilla IDEAL (Requerida)': '#1f77b4', '2. Plantilla REAL (Contratada)': '#ff7f0e'})
        fig_rh.update_layout(legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_rh, use_container_width=True)
        st.markdown("""<div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 5px; margin-bottom: 25px;"><h5 style="margin-top: 0; color: #B38600;">💡 Guía rápida</h5><p style="font-size: 14px; color: #333; margin: 0;">Permite comparar visualmente el tamaño actual de tu equipo (Naranja) contra la estructura que las matemáticas exigen para operar perfectamente (Azul).</p></div>""", unsafe_allow_html=True)