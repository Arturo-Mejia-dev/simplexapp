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
    padding: 8px 15px !important; font-size: 14px !important; font-weight: bold !important; border-radius: 8px !important; height: 45px !important;
}

.stButton button[kind="primary"] { background-color: #111111 !important; color: #FFFFFF !important; border: 2px solid #FF0000 !important; animation: pulse_red_small 2s infinite !important; }
.stButton button[kind="primary"]:hover { background-color: #222222 !important; border-color: #FF3333 !important; }

div:has(> .stButton button:contains("CALCULAR")) .stButton button { height: 60px !important; font-size: 18px !important; }

.stButton button[kind="secondary"] { border: 1px solid #ccc !important; animation: pulse_blue_small 2s infinite !important; }
.stButton button[kind="secondary"]:hover { background-color: #1F77B4 !important; color: #FFFFFF !important; border-color: #1F77B4 !important;}

.stDownloadButton button { background-color: #1F77B4 !important; color: #FFFFFF !important; border: 2px solid #155987 !important; padding: 8px 15px !important; font-weight: bold !important; border-radius: 8px !important;}
[data-testid="stFileUploader"] { background-color: #EBF5FB !important; border: 2px dashed #2E86C1 !important; border-radius: 10px !important; }

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
dias_semana = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
bloques = ["10:00 a 14:00 (4 hrs)", "14:00 a 17:00 (3 hrs)", "17:00 a 18:00 (1 hr)", "18:00 a 22:00 (4 hrs)", "22:00 a 01:00 (3 hrs)"]
horas_por_bloque = [4, 3, 1, 4, 3]
puestos_fijos = ['Supervisor', 'Caja', 'Hostes', 'Empacador', 'Auxiliar']

DEFAULT_CONFIG = {
    's_coc': 350.0, 's_ven': 300.0, 's_bar': 320.0, 's_sup': 500.0, 's_caj': 300.0, 's_hos': 250.0, 's_emp': 250.0, 's_aux': 250.0, 
    'c_coc': 8, 'c_sal': 12, 'c_bar': 15,
    'fatiga_pct': 15.0,  
    'esp_pct': {d: {'M': 0.0, 'I': 0.0, 'V': 0.0} for d in dias_semana}, 
    'ideal_sup': 2, 'ideal_caj': 3, 'ideal_hos': 3, 'ideal_emp': 2, 'ideal_aux': 2 
}

def consultarSimplex(ids,fi,ff):
    form_data = {'ids': str(ids), 'fi': fi.strftime('%Y-%m-%d'), 'ff': ff.strftime('%Y-%m-%d')}
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    url = "https://operamx.no-ip.net/back/api_tickets/api/Simplex/ObtenerDatosSimplex"
    try:
        headers = {"X-API-Key": st.secrets["API_KEY"]}
        response = requests.post(url, data=form_data, verify=False, headers= headers)
        response.raise_for_status() 
        datosSimplex = response.json()
        valores = []; arr_ventas = []; filas_dem = []; index2 = 0; index = 0
        for d in dias_semana:
            multiplicador = 1; arr_ventas = []
            for i in range(5):
              arr_ventas.append(datosSimplex[index2]["venta"]); index2 += 1
            valores.append(next((num for num in arr_ventas if num > 0), 0))
            for b in bloques:
                filas_dem.append({"Día": d, "Bloque": b, "🍳 Cmds Cocina": datosSimplex[index]["alimentos"]*multiplicador, "🍳 Extra Cocina": 0.0, "🍔 Cmds Salón": datosSimplex[index]["salon"]*multiplicador, "🍔 Extra Salón": 0.0, "🍺 Cmds Barra": datosSimplex[index]["bebidas"]*multiplicador, "🍺 Extra Barra": 0.0})
                index += 1
        st.session_state.df_demanda = pd.DataFrame(filas_dem)
        dft = pd.DataFrame({'Día': dias_semana, 'Venta Proyectada ($)': valores})
        dft['Día'] = dft['Día'].str.strip()
        st.session_state.df_ventas = dft
    except requests.exceptions.RequestException as e:
        print('Error en la petición:', e)
    
def get_week_dates(year, week_num):
    jan1 = datetime.date(year, 1, 1)
    days_to_subtract = (jan1.weekday() + 1) % 7
    start_week1 = jan1 - datetime.timedelta(days=days_to_subtract)
    start = start_week1 + datetime.timedelta(weeks=week_num - 1)
    return start, start + datetime.timedelta(days=6)

def week_number(date):
    jan1 = datetime.date(date.year, 1, 1)
    start = jan1 - datetime.timedelta(days=(jan1.weekday() + 1) % 7)
    return (date - start).days // 7 + 1

def load_config():
    try:
        headers = {"X-API-Key": st.secrets["API_KEY"]}
        url_config = 'https://operamx.no-ip.net/back/api_tickets/api/Simplex/getConfigMaestra'
        response = requests.get(url_config, params={},verify=False, headers= headers)
        response.raise_for_status()
        data = response.text
        if not data.strip(): return DEFAULT_CONFIG
        try:
            json_data = json.loads(data)
            if 'esp_pct' not in json_data or not isinstance(json_data['esp_pct'], dict) or (len(json_data['esp_pct']) > 0 and not isinstance(list(json_data['esp_pct'].values())[0], dict)):
                json_data['esp_pct'] = {d: {'M': 0.0, 'I': 0.0, 'V': 0.0} for d in dias_semana}
            
            for k, v in DEFAULT_CONFIG.items():
                if k not in json_data: json_data[k] = v
            return json_data
        except json.JSONDecodeError:
            return DEFAULT_CONFIG  
    except requests.exceptions.RequestException:
        return DEFAULT_CONFIG

def save_config(config):
    headers = {"X-API-Key": st.secrets["API_KEY"]}
    url_guardar = "https://operamx.no-ip.net/back/api_tickets/api/Simplex/guardarConfigMaestra"
    json_string = json.dumps(config)
    try: requests.post(url_guardar, data={'data': json_string},verify=False, headers= headers).raise_for_status()
    except requests.exceptions.RequestException as e: print(e)

config_data = load_config()

# --- 🧠 INICIALIZACIÓN DE SESIÓN ---
for var in ['c_sup', 'c_caj', 'c_coc', 'c_sal', 'c_bar', 'c_emp', 'c_aux', 'c_hos']:
    if var not in st.session_state: st.session_state[var] = 0
if 'descanso_sup' not in st.session_state: st.session_state.descanso_sup = "Lunes"

for p in puestos_fijos:
    if f'counter_{p}' not in st.session_state: st.session_state[f'counter_{p}'] = 0
if 'counter_demanda' not in st.session_state: st.session_state['counter_demanda'] = 0

if 'df_ventas' not in st.session_state: st.session_state.df_ventas = pd.DataFrame({"Día": dias_semana, "Venta Proyectada ($)": [0.0] * 7})

if 'df_fijos_dict' not in st.session_state:
    st.session_state.df_fijos_dict = {}
    for p in puestos_fijos:
        df_temp = pd.DataFrame([{"Día": d, "Matutino": False, "Intermedio": False, "Vespertino": False} for d in dias_semana])
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
if 'plantilla_ideal' not in st.session_state: st.session_state['plantilla_ideal'] = {}
if 'sucursal_seleccionada' not in st.session_state: st.session_state.sucursal_seleccionada = None

def sync_tope_slider(): st.session_state.tope = st.session_state.input_slider
def sync_tope_num(): st.session_state.tope = st.session_state.input_num

# --- 🚀 FUNCIONES DE CALLBACK ---
def update_all_fijos(puesto, turno, valor): st.session_state.df_fijos_dict[puesto][turno] = valor; st.session_state[f'counter_{puesto}'] += 1
def clear_all_fijos(puesto):
    st.session_state.df_fijos_dict[puesto]['Matutino'] = False
    st.session_state.df_fijos_dict[puesto]['Intermedio'] = False
    st.session_state.df_fijos_dict[puesto]['Vespertino'] = False
    st.session_state[f'counter_{puesto}'] += 1

# --- 🔥 FUNCIÓN QUIRÚRGICA MODIFICADA PARA MULTISELECCIÓN DE ÁREA 🔥 ---
def inyectar_horas_extra(dias_in, turno_in, areas_in, hrs_in):
    df = st.session_state.df_demanda
    if "Todos" in dias_in or not dias_in:
        dias_target = dias_semana
    else:
        dias_target = dias_in
        
    mapa_bloques = {
        "☀️ Matutino (10:00 - 14:00)": "10:00 a 14:00 (4 hrs)",
        "🌤️ Intermedio - Comida (14:00 - 17:00)": "14:00 a 17:00 (3 hrs)",
        "⚡ Cruce Pico (17:00 - 18:00)": "17:00 a 18:00 (1 hr)",
        "🌤️ Intermedio - Tarde (18:00 - 22:00)": "18:00 a 22:00 (4 hrs)",
        "🌙 Vespertino (22:00 - 01:00)": "22:00 a 01:00 (3 hrs)"
    }
    b_exacto = mapa_bloques.get(turno_in, "10:00 a 14:00 (4 hrs)")
    
    cols_target = []
    # Si seleccionan "Todas" o dejan el campo vacío, aplica a los 3 puestos operativos
    if "Todas" in areas_in or not areas_in:
        cols_target = ["🍳 Extra Cocina", "🍔 Extra Salón", "🍺 Extra Barra"]
    else:
        if "🍳 Cocina" in areas_in: cols_target.append("🍳 Extra Cocina")
        if "🍔 Salón" in areas_in: cols_target.append("🍔 Extra Salón")
        if "🍺 Barra" in areas_in: cols_target.append("🍺 Extra Barra")
    
    mask = (df['Día'].isin(dias_target)) & (df['Bloque'] == b_exacto)
    for col in cols_target: df.loc[mask, col] = float(hrs_in)
    st.session_state['counter_demanda'] += 1

def limpiar_horas_extra():
    df = st.session_state.df_demanda
    df['🍳 Extra Cocina'] = 0.0; df['🍔 Extra Salón'] = 0.0; df['🍺 Extra Barra'] = 0.0
    st.session_state['counter_demanda'] += 1

def generar_machote():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_v_out = st.session_state.get('df_ventas_edited', st.session_state.df_ventas)
        df_v_out.to_excel(writer, sheet_name="Ventas", index=False)
        df_eq = pd.DataFrame({"Parámetro": ["Supervisor", "Caja", "Cocinero", "Vendedor", "Barra", "Empacador", "Auxiliar", "Hostes", "Descanso_Supervisor"], "Valor": [st.session_state.c_sup, st.session_state.c_caj, st.session_state.c_coc, st.session_state.c_sal, st.session_state.c_bar, st.session_state.c_emp, st.session_state.c_aux, st.session_state.c_hos, st.session_state.descanso_sup]})
        df_eq.to_excel(writer, sheet_name="Equipo_Actual", index=False)
        filas_fijos_excel = []
        for d in dias_semana:
            fila = {"Día": d}
            for p in puestos_fijos:
                df_p = st.session_state.get(f"df_fijos_{p}_edited", st.session_state.df_fijos_dict[p])
                row_p = df_p[df_p['Día'] == d].iloc[0]
                fila[f"{p}_Matutino"] = "Si" if row_p['Matutino'] else "No"; fila[f"{p}_Intermedio"] = "Si" if row_p['Intermedio'] else "No"; fila[f"{p}_Vespertino"] = "Si" if row_p['Vespertino'] else "No"
            filas_fijos_excel.append(fila)
        pd.DataFrame(filas_fijos_excel).to_excel(writer, sheet_name="Personal_Fijo", index=False)
        df_d_out = st.session_state.get('df_demanda_edited', st.session_state.df_demanda)
        df_d_out.to_excel(writer, sheet_name="Demanda", index=False)
    return output.getvalue()

# --- 🍔 ENCABEZADO REBEL WINGS ---
st.markdown("<h1 style='text-align: center; color: #111; margin-bottom: 0; font-weight: bold;'>🍗 REBEL WINGS 🍔</h1><h3 style='text-align: center; color: #555; margin-top: 0;'>🔥 SIMPLEX: Tu Asistente para controlar tu personal</h3>", unsafe_allow_html=True)

# --- 🎛️ BARRA LATERAL ---
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
            
        with st.expander("⚙️ Capacidad Productiva y Desgaste"):
            new_c_coc = st.number_input("Capacidad Productiva Cocina (cmds/h)", value=config_data['c_coc'])
            new_c_sal = st.number_input("Capacidad Productiva Salón (cmds/h)", value=config_data['c_sal'])
            new_c_bar = st.number_input("Capacidad Productiva Barra (cmds/h)", value=config_data['c_bar'])
            new_fatiga = st.number_input("📉 % Desgaste Humano al final del turno (Fatiga)", min_value=0.0, max_value=50.0, value=float(config_data.get('fatiga_pct', 15.0)), step=1.0)
            
        with st.expander("🎯 Límites de Plantilla Fija (Ideal)"):
            new_ideal_sup = st.number_input("Límite Ideal ⭐️ Supervisor", min_value=0, value=config_data.get('ideal_sup', 2))
            new_ideal_caj = st.number_input("Límite Ideal 🖥️ Caja", min_value=0, value=config_data.get('ideal_caj', 3))
            new_ideal_emp = st.number_input("Límite Ideal 📦 Empacador", min_value=0, value=config_data.get('ideal_emp', 2))
            new_ideal_aux = st.number_input("Límite Ideal 🧹 Auxiliar", min_value=0, value=config_data.get('ideal_aux', 2))
            new_ideal_hos = st.number_input("Límite Ideal 🛎️ Hostes", min_value=0, value=config_data.get('ideal_hos', 3))
            
        with st.expander("🎉 Configurar Días Festivos (% Aumento por Turno)"):
            df_esp_inicial = pd.DataFrame([
                {"Día": d, "☀️ Matutino": config_data['esp_pct'][d]['M'], "🌤️ Intermedio": config_data['esp_pct'][d]['I'], "🌙 Vespertino": config_data['esp_pct'][d]['V']} for d in dias_semana
            ])
            edited_esp = st.data_editor(df_esp_inicial, hide_index=True, use_container_width=True)
            new_esp = {row['Día']: {'M': float(row['☀️ Matutino']), 'I': float(row['🌤️ Intermedio']), 'V': float(row['🌙 Vespertino'])} for _, row in edited_esp.iterrows()}
                
        if st.button("🔒 Guardar y Bloquear", type="primary"):
            config_data.update({'s_coc': new_s_coc, 's_ven': new_s_ven, 's_bar': new_s_bar, 's_sup': new_s_sup, 's_caj': new_s_caj, 's_hos': new_s_hos, 's_emp': new_s_emp, 's_aux': new_s_aux, 'c_coc': new_c_coc, 'c_sal': new_c_sal, 'c_bar': new_c_bar, 'fatiga_pct': new_fatiga, 'esp_pct': new_esp, 'ideal_sup': new_ideal_sup, 'ideal_caj': new_ideal_caj, 'ideal_hos': new_ideal_hos, 'ideal_emp': new_ideal_emp, 'ideal_aux': new_ideal_aux})
            save_config(config_data)
            st.session_state['config_unlocked'] = False
            st.rerun()

    st.markdown("---")
    modo_impresion = st.checkbox("📄 Vista para PDF")

s_coc, s_ven, s_bar, s_sup, s_caj, s_hos, s_emp, s_aux = config_data['s_coc'], config_data['s_ven'], config_data['s_bar'], config_data['s_sup'], config_data['s_caj'], config_data['s_hos'], config_data.get('s_emp', 250.0), config_data.get('s_aux', 250.0)
c_coc, c_sal, c_bar = config_data['c_coc'], config_data['c_sal'], config_data['c_bar']
fatiga_pct = float(config_data.get('fatiga_pct', 15.0))
factor_fatiga_mult = 1.0 - (fatiga_pct / 100.0 / 2.0)  

esp_pct = config_data.get('esp_pct', {d: {'M': 0.0, 'I': 0.0, 'V': 0.0} for d in dias_semana})
ideal_sup_cfg, ideal_caj_cfg, ideal_hos_cfg, ideal_emp_cfg, ideal_aux_cfg = config_data.get('ideal_sup', 2), config_data.get('ideal_caj', 3), config_data.get('ideal_hos', 3), config_data.get('ideal_emp', 2), config_data.get('ideal_aux', 2)
salarios_map = {'Supervisor': s_sup, 'Caja': s_caj, 'Cocinero': s_coc, 'Vendedor': s_ven, 'Barra': s_bar, 'Empacador': s_emp, 'Auxiliar': s_aux, 'Hostes': s_hos}

# ==========================================
# 🚀 PANTALLA PRINCIPAL: FLUJO DE PASOS
# ==========================================
tab_carga, tab_diario, tab_semanal, tab_ideal = st.tabs(["📥 1. CARGA DE DATOS", "📅 2. RESUMEN DIARIO", "📊 3. GRAN RESUMEN SEMANAL", "⚖️ 4. PLANTILLA IDEAL VS REAL"])

with tab_carga:
    st.markdown("### 1️⃣ PASO 1: Descarga o Sube tu Excel")
    c_up1, c_up2 = st.columns(2)
    with c_up1: st.download_button(label="📥 Descargar Machote de Excel", data=generar_machote(), file_name="Machote_Semanal.xlsx", type="secondary")
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

    url = "https://operamx.no-ip.net/back/api_tickets/api/Catalogos/getSucursales"
    try:
        headers = {"X-API-Key": st.secrets["API_KEY"]}
        response = requests.get(url, timeout=10,headers=headers)
        response.raise_for_status()
        sucursales = response.json()
    except Exception as e: sucursales = []

    if sucursales:
        current_index = 0
        if st.session_state.sucursal_seleccionada is not None:
            for i, s in enumerate(sucursales):
                if s.get('cod') == st.session_state.sucursal_seleccionada.get('cod'):
                    current_index = i
                    break
        sucursal_seleccionada = st.selectbox("SELECCIONA UNA SUCURSAL:", sucursales, index=current_index, format_func=lambda s: f"{s['name']}", key="sucursal_widget")
        st.session_state.sucursal_seleccionada = sucursal_seleccionada
    else: st.info("No se pudieron cargar las sucursales.")
            
    today = datetime.date.today()
    current_year = today.year
    years_list = list(range(current_year - 2, current_year + 4))

    col_yr, col_wk = st.columns([1, 2])
    with col_yr:
        if 'selected_year' not in st.session_state:
            st.session_state.selected_year = current_year
        if st.session_state.selected_year not in years_list:
            st.session_state.selected_year = current_year
        selected_year = st.selectbox("📅 SELECCIONA EL AÑO", years_list, index=years_list.index(st.session_state.selected_year), key="year_select")
        st.session_state.selected_year = selected_year
        year = selected_year

    with col_wk:
        last_day = datetime.date(year, 12, 31)
        max_week = week_number(last_day)
        weeks = list(range(1, max_week + 1))

        if 'selected_week' not in st.session_state:
            current_week = week_number(today)
            st.session_state.selected_week = current_week if current_week in weeks else weeks[0]
        if st.session_state.selected_week not in weeks: st.session_state.selected_week = weeks[0]

        try: default_index = weeks.index(st.session_state.selected_week)
        except ValueError: default_index = 0

        st.session_state.selected_week = st.selectbox("📆 SELECCIONA LA SEMANA", weeks, index=default_index, key="week_select")
        
    fi, ff = get_week_dates(year, st.session_state.selected_week)
    st.write(f"Semana **{st.session_state.selected_week}** del año **{year}**: desde **{fi}** hasta **{ff}**")

    st.button("CARGAR INFORMACIÓN", on_click=lambda: consultarSimplex(st.session_state.sucursal_seleccionada["cod"], fi, ff) if st.session_state.sucursal_seleccionada is not None else st.warning("Selecciona una sucursal primero"), use_container_width=True)

    st.markdown("---")
    st.markdown("### 2️⃣ PASO 2: Verifica o Captura tu Operación (Manual)")
    
    t_ven, t_equ, t_fij, t_dem = st.tabs(["💰 Ventas", "👥 Tu Equipo Actual", "📌 Personal Fijo (Turnos)", "📊 Demanda Operativa"])
    
    with t_ven:
        st.session_state.df_ventas_edited = st.data_editor(st.session_state.df_ventas, use_container_width=False, hide_index=True, height=300, key="editor_ventas")
    
    with t_equ:
        st.session_state['descanso_sup'] = st.selectbox("🏖️ Día de Descanso del Supervisor:", dias_semana, index=dias_semana.index(st.session_state.descanso_sup) if st.session_state.descanso_sup in dias_semana else 1)
        c_rh1, c_rh2, c_rh3, c_rh4 = st.columns(4)
        with c_rh1: st.session_state['c_sup'] = st.number_input("⭐️ Supervisor", 0, value=st.session_state.get('c_sup', 0)); st.session_state['c_caj'] = st.number_input("🖥️ Caja", 0, value=st.session_state.get('c_caj', 0))
        with c_rh2: st.session_state['c_coc'] = st.number_input("🍳 Cocinero", 0, value=st.session_state.get('c_coc', 0)); st.session_state['c_sal'] = st.number_input("🍔 Vendedor", 0, value=st.session_state.get('c_sal', 0))
        with c_rh3: st.session_state['c_bar'] = st.number_input("🍺 Barra", 0, value=st.session_state.get('c_bar', 0)); st.session_state['c_emp'] = st.number_input("📦 Empacador", 0, value=st.session_state.get('c_emp', 0))
        with c_rh4: st.session_state['c_aux'] = st.number_input("🧹 Auxiliar", 0, value=st.session_state.get('c_aux', 0)); st.session_state['c_hos'] = st.number_input("🛎️ Hostes", 0, value=st.session_state.get('c_hos', 0))
            
    with t_fij:
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
                    df_current, use_container_width=True, hide_index=True, height=295, key=f"editor_fijos_{p}_{st.session_state[f'counter_{p}']}",
                    column_config={"Día": st.column_config.TextColumn("Día", disabled=True), "Matutino": st.column_config.CheckboxColumn("☀️ Matutino", default=False), "Intermedio": st.column_config.CheckboxColumn("🌤️ Intermedio", default=False), "Vespertino": st.column_config.CheckboxColumn("🌙 Vespertino", default=False)}
                )
        
    with t_dem:
        # --- 🔥 MEJORA QUIRÚRGICA: MULTISELECCIÓN EN ÁREAS, DÍAS Y HORARIOS 🔥 ---
        st.markdown("#### ⚡ Panel de Asignación Rápida (Horas Extra)")
        c_i1, c_i2, c_i3, c_i4, c_i5, c_i6 = st.columns([2, 2, 2, 1, 1.5, 1.5])
        with c_i1: 
            dias_qa = st.multiselect("📅 Día(s)", ["Todos"] + dias_semana, default=["Todos"], placeholder="Elige día(s)...")
        with c_i2: 
            bloque_qa = st.selectbox("🕒 Turno / Horario", [
                "☀️ Matutino (10:00 - 14:00)", 
                "🌤️ Intermedio - Comida (14:00 - 17:00)", 
                "⚡ Cruce Pico (17:00 - 18:00)", 
                "🌤️ Intermedio - Tarde (18:00 - 22:00)", 
                "🌙 Vespertino (22:00 - 01:00)"
            ])
        with c_i3: 
            areas_qa = st.multiselect("🎯 Área(s)", ["Todas", "🍳 Cocina", "🍔 Salón", "🍺 Barra"], default=["Todas"], placeholder="Elige área(s)...")
        with c_i4: 
            hrs_qa = st.number_input("⏱️ Horas", 0.0, 5.0, 1.0, 0.5)
        with c_i5: 
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("⚡ Inyectar Extras", type="primary", use_container_width=True, on_click=inyectar_horas_extra, args=(dias_qa, bloque_qa, areas_qa, hrs_qa))
        with c_i6: 
            st.markdown("<br>", unsafe_allow_html=True)
            st.button("🧹 Borrar Extras", type="secondary", use_container_width=True, on_click=limpiar_horas_extra)
            
        st.markdown("---")
        st.session_state.df_demanda_edited = st.data_editor(st.session_state.df_demanda, use_container_width=True, hide_index=True, height=1300, key=f"editor_demanda_{st.session_state['counter_demanda']}")

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
            
            pct_M = esp_pct[d]['M'] / 100.0
            pct_I = esp_pct[d]['I'] / 100.0
            pct_V = esp_pct[d]['V'] / 100.0
            
            factores_bloque = [
                1.0 + pct_M,                           
                1.0 + max(pct_M, pct_I),               
                1.0 + max(pct_M, pct_I, pct_V),        
                1.0 + max(pct_I, pct_V),               
                1.0 + pct_V                            
            ]
            
            factor_crecimiento_max = 1.0 + max(pct_M, pct_I, pct_V)
            venta_ajustada = st.session_state.db['ventas'][d] * factor_crecimiento_max
            venta_total_semana += venta_ajustada 
            
            demandas = {
                'Cocina': [st.session_state.db['demanda'][d]['cc'][i] * factores_bloque[i] for i in range(5)],
                'Salon':  [st.session_state.db['demanda'][d]['cs'][i] * factores_bloque[i] for i in range(5)],
                'Barra':  [st.session_state.db['demanda'][d]['cb'][i] * factores_bloque[i] for i in range(5)]
            }
            extras = {'Cocina': st.session_state.db['demanda'][d]['ec'], 'Salon':  st.session_state.db['demanda'][d]['es'], 'Barra':  st.session_state.db['demanda'][d]['eb']}
            plot_data_req = {'Cocina': [], 'Salon': [], 'Barra': []}; plot_data_prov = {'Cocina': [], 'Salon': [], 'Barra': []}
            
            for r in roles:
                for i in range(5):
                    req_horas = (demandas[r][i] / (capacidades[r] * factor_fatiga_mult)) + extras[r][i]  
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
                        plot_data_req[r].append(round((demandas[r][i] / (capacidades[r] * factor_fatiga_mult)) + extras[r][i], 1))
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
                    'Costo': c_total_dia, 'Costo_Fijo': c_fijo_dia, 'Costo_Var': pl.value(c_var_dia), 'Venta_Ajustada': venta_ajustada, 
                    'Es_Especial': factor_crecimiento_max > 1.0, 'Pct_Extra': factor_crecimiento_max * 100 - 100, 
                    'req': plot_data_req, 'prov': plot_data_prov, 'demanda_bruta': demandas
                }
                turnos_semanales['Cocina'] += sum([vars_personal[('Cocina', t)].varValue for t in turnos]); turnos_semanales['Salon'] += sum([vars_personal[('Salon', t)].varValue for t in turnos]); turnos_semanales['Barra'] += sum([vars_personal[('Barra', t)].varValue for t in turnos])
            else: dias_inviables.append(d)

        progress_container.empty()
        
        if dias_inviables: st.error(f"⚠️ **Presupuesto Inviable en:** {', '.join(dias_inviables)}. Aumenta el Tope Máximo."); st.session_state['resultados_diarios'] = None
        else:
            st.session_state['resultados_diarios'] = resultados_diarios; st.session_state['venta_total_semana_calc'] = venta_total_semana; st.session_state['costo_total_semana_calc'] = costo_total_semana
            
            max_cocina_diario = max([int(resultados_diarios[d]['M'][0] + resultados_diarios[d]['I'][0] + resultados_diarios[d]['V'][0]) for d in dias_semana])
            max_vendedor_diario = max([int(resultados_diarios[d]['M'][1] + resultados_diarios[d]['I'][1] + resultados_diarios[d]['V'][1]) for d in dias_semana])
            max_barra_diario = max([int(resultados_diarios[d]['M'][2] + resultados_diarios[d]['I'][2] + resultados_diarios[d]['V'][2]) for d in dias_semana])

            st.session_state['plantilla_ideal'] = {
                'Supervisor': ideal_sup_cfg, 
                'Caja': ideal_caj_cfg, 
                'Cocinero': int(max(math.ceil(turnos_semanales['Cocina'] / 6.0), max_cocina_diario)), 
                'Vendedor': int(max(math.ceil(turnos_semanales['Salon'] / 6.0), max_vendedor_diario)), 
                'Barra': int(max(math.ceil(turnos_semanales['Barra'] / 6.0), max_barra_diario)), 
                'Empacador': ideal_emp_cfg, 
                'Auxiliar': ideal_aux_cfg, 
                'Hostes': ideal_hos_cfg
            }
            st.success("✅ ¡Cálculo Exitoso!")

# ==========================================
# 🧱 RENDERIZADO DE PESTAÑAS (RESULTADOS)
# ==========================================
with tab_diario:
    if st.session_state['resultados_diarios'] is not None:
        dia_sel = st.selectbox("👉 Elige el día a analizar:", dias_semana, key="sel_dia_print")
        res = st.session_state['resultados_diarios'][dia_sel]
        venta = res['Venta_Ajustada']; pct = (res['Costo'] / venta) * 100 if venta > 0 else 0
        
        st.markdown("---")
        if res['Es_Especial']: st.success(f"🎉 **¡DÍA ESPECIAL ACTIVO!** Aumento Máximo Cruzado: **+{res['Pct_Extra']:.1f}%**")
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

        st.markdown("### 📈 Tablero Visual de Saturación y Desgaste Humano")
        st.write(f"Visualización ejecutiva de la carga operativa por turno, aplicando un **Factor de Fatiga del {fatiga_pct:.1f}%** (caída natural de velocidad al cierre de jornada):")
        
        turnos_nombres = ["☀️ Matutino (10:00 - 18:00)", "🌤️ Intermedio (14:00 - 22:00)", "🌙 Vespertino (17:00 - 01:00)"]
        llaves_t = ['M', 'I', 'V']; roles_op = ["🍳 Cocinero", "🍔 Vendedor", "🍺 Barra"]
        indices_rol = [0, 1, 2]; llaves_rol = ["Cocina", "Salon", "Barra"]; caps_op = [c_coc, c_sal, c_bar]
        
        for t_idx, t_nom in enumerate(turnos_nombres):
            st.markdown(f"<h4 style='color: #1F77B4; margin-top: 15px; border-bottom: 2px solid #1F77B4; padding-bottom: 5px;'>{t_nom}</h4>", unsafe_allow_html=True)
            cols_t = st.columns(3); t_key = llaves_t[t_idx]
            for r_idx, col in enumerate(cols_t):
                with col:
                    gente_r = int(res[t_key][indices_rol[r_idx]])
                    cap_val_r = caps_op[r_idx]
                    cap_promedio_r = cap_val_r * factor_fatiga_mult  
                    rol_str = llaves_rol[r_idx]
                    
                    blk_idx_r = [0, 1, 2] if t_key == 'M' else ([1, 2, 3] if t_key == 'I' else [2, 3, 4])
                    cmds_r = sum(res['demanda_bruta'][rol_str][i] for i in blk_idx_r)
                    extras_r_db = {'Cocina': st.session_state.db['demanda'][dia_sel]['ec'], 'Salon': st.session_state.db['demanda'][dia_sel]['es'], 'Barra': st.session_state.db['demanda'][dia_sel]['eb']}
                    extras_r = sum(extras_r_db[rol_str][i] for i in blk_idx_r)
                    
                    hrs_req_r = round((cmds_r / cap_promedio_r) + extras_r, 1) if cap_promedio_r > 0 else 0
                    hrs_aut_r = gente_r * 8
                    cmds_aut_r = hrs_aut_r * cap_promedio_r
                    pct_sat_r = round((hrs_req_r / hrs_aut_r) * 100, 1) if hrs_aut_r > 0 else 0
                    
                    bar_col_r = "#2CA02C" if pct_sat_r <= 100 else "#FF7F0E"
                    bar_wid_r = min(pct_sat_r, 100)
                    txt_card_op = f"<span style='color: #D65A31; font-size: 12px; font-weight: bold;'>🔄 Cobertura cruzada (Empalme de turnos)</span>" if hrs_req_r > hrs_aut_r else f"<span style='color: #2CA02C; font-size: 12px; font-weight: bold;'>✅ Cobertura Autónoma Asegurada</span>"
                        
                    st.markdown(f"""<div style="background-color: #FFF; border: 1px solid #CCC; border-radius: 10px; padding: 15px; box-shadow: 0 2px 5px rgba(0,0,0,0.05);">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #EEE; padding-bottom: 8px; margin-bottom: 10px;">
<strong style="font-size: 16px; color: #333;">{roles_op[r_idx]}</strong><span style="background-color: #1F77B4; color: white; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: bold;">{gente_r} Pers.</span></div>
<div style="font-size: 13px; color: #555; margin-bottom: 8px;">
<div style="display: flex; justify-content: space-between;"><span>Demanda Esperada:</span> <b>{cmds_r:,.0f} cmds</b></div>
<div style="display: flex; justify-content: space-between;"><span>Cap. Real (C/ Fatiga):</span> <b>{cmds_aut_r:,.0f} cmds</b></div></div>
<div style="margin-bottom: 8px;"><div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: bold; color: #666; margin-bottom: 3px;">
<span>Saturación del Turno:</span> <span style="color: {bar_col_r};">{pct_sat_r}%</span></div>
<div style="background-color: #E9ECEF; border-radius: 6px; width: 100%; height: 10px; overflow: hidden;"><div style="background-color: {bar_col_r}; width: {bar_wid_r}%; height: 100%;"></div></div></div>{txt_card_op}</div>""", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown("### 💎 Radiografía del Restaurante")
        df_rush = pd.DataFrame({'Bloque Horario': bloques * 3, 'Comandas': res['demanda_bruta']['Cocina'] + res['demanda_bruta']['Salon'] + res['demanda_bruta']['Barra'], 'Área': ['🍳 Cocina']*5 + ['🍔 Salón']*5 + ['🍺 Barra']*5})
        st.plotly_chart(px.area(df_rush, x='Bloque Horario', y='Comandas', color='Área', color_discrete_map={'🍳 Cocina': '#FF7F0E', '🍔 Salón': '#1F77B4', '🍺 Barra': '#2CA02C'}), use_container_width=True)
        
        st.markdown("### ⚖️ Cobertura de Personal")
        area = st.radio("Elige el Área Operativa:", ["Cocina", "Salon", "Barra"], horizontal=True)
        sum_n = sum(res['req'][area]); sum_p = sum(res['prov'][area]); p_n = sum_n / 8.0; p_p = int(sum_p / 8.0)

        st.markdown(f"""<div style="display: flex; gap: 20px; margin-bottom: 10px;"><div style="background-color: #fdf2f2; padding: 15px; border-radius: 8px; border: 1px solid #f8d7da; flex: 1; text-align: center;"><div style="color: #d62728; font-weight: bold; font-size: 16px;">🔴 Total Horas Necesarias en el Día: {sum_n:.1f} hrs</div><div style="color: #d62728; font-size: 14px; margin-top: 5px;">👥 <i>Equivale a <b>{p_n:.1f}</b> personas teóricas</i></div></div><div style="background-color: #f2fdf2; padding: 15px; border-radius: 8px; border: 1px solid #d1e7dd; flex: 1; text-align: center;"><div style="color: #2ca02c; font-weight: bold; font-size: 16px;">🟢 Total Horas Programadas (Personal): {sum_p:.1f} hrs</div><div style="color: #2ca02c; font-size: 14px; margin-top: 5px;">👥 <i>Equivale a <b>{p_p}</b> personas reales</i></div></div></div>""", unsafe_allow_html=True)

        fig_bar = px.bar(pd.DataFrame({'Horario': bloques * 2, 'Horas': res['req'][area] + res['prov'][area], 'Indicador': ['1. Horas NECESARIAS (Demanda)']*5 + ['2. Horas PROGRAMADAS (Personal)']*5}), x='Horario', y='Horas', color='Indicador', barmode='group', text_auto='.1f', color_discrete_map={'1. Horas NECESARIAS (Demanda)': '#d62728', '2. Horas PROGRAMADAS (Personal)': '#2ca02c'})
        fig_bar.update_layout(legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_bar, use_container_width=True)

with tab_semanal:
    if st.session_state['resultados_diarios'] is not None:
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
        
        st.markdown("---"); st.subheader("📋 Tu Plantilla Maestra Semanal")
        filas_maestras = []
        for d in dias_semana:
            res = st.session_state['resultados_diarios'][d]
            n_dia = d
            if d == st.session_state.get('descanso_sup', ''): n_dia += " 🏖️(Descanso Sup)"
            
            pcts = esp_pct.get(d, {'M': 0.0, 'I': 0.0, 'V': 0.0})
            pm, pi, pv = float(pcts.get('M', 0.0)), float(pcts.get('I', 0.0)), float(pcts.get('V', 0.0))
            
            t_m = f"☀️ Matutino (+{pm:g}%) ⭐" if pm > 0 else "☀️ Matutino"
            t_i = f"🌤️ Intermedio (+{pi:g}%) ⭐" if pi > 0 else "🌤️ Intermedio"
            t_v = f"🌙 Vespertino (+{pv:g}%) ⭐" if pv > 0 else "🌙 Vespertino"
            
            filas_maestras.append({"Día": n_dia, "Turno": t_m, "⭐️ Supervisor": int(res['M'][4]), "🖥️ Caja": int(res['M'][3]), "🍳 Cocinero": int(res['M'][0]), "🍔 Vendedor": int(res['M'][1]), "🍺 Barra": int(res['M'][2]), "📦 Empacador": int(res['M'][6]), "🧹 Auxiliar": int(res['M'][7]), "🛎️ Hostes": int(res['M'][5]), "Costo del Día": f"$ {res['Costo']:,.2f}"})
            filas_maestras.append({"Día": n_dia, "Turno": t_i, "⭐️ Supervisor": int(res['I'][4]), "🖥️ Caja": int(res['I'][3]), "🍳 Cocinero": int(res['I'][0]), "🍔 Vendedor": int(res['I'][1]), "🍺 Barra": int(res['I'][2]), "📦 Empacador": int(res['I'][6]), "🧹 Auxiliar": int(res['I'][7]), "🛎️ Hostes": int(res['I'][5]), "Costo del Día": "---"})
            filas_maestras.append({"Día": n_dia, "Turno": t_v, "⭐️ Supervisor": int(res['V'][4]), "🖥️ Caja": int(res['V'][3]), "🍳 Cocinero": int(res['V'][0]), "🍔 Vendedor": int(res['V'][1]), "🍺 Barra": int(res['V'][2]), "📦 Empacador": int(res['V'][6]), "🧹 Auxiliar": int(res['V'][7]), "🛎️ Hostes": int(res['V'][5]), "Costo del Día": "---"})
            
        t_sup = sum(f['⭐️ Supervisor'] for f in filas_maestras); t_caj = sum(f['🖥️ Caja'] for f in filas_maestras); t_coc = sum(f['🍳 Cocinero'] for f in filas_maestras); t_ven = sum(f['🍔 Vendedor'] for f in filas_maestras); t_bar = sum(f['🍺 Barra'] for f in filas_maestras); t_emp = sum(f['📦 Empacador'] for f in filas_maestras); t_aux = sum(f['🧹 Auxiliar'] for f in filas_maestras); t_hos = sum(f['🛎️ Hostes'] for f in filas_maestras)
        filas_maestras.append({"Día": "📌 TOTAL SEMANA", "Turno": "---", "⭐️ Supervisor": t_sup, "🖥️ Caja": t_caj, "🍳 Cocinero": t_coc, "🍔 Vendedor": t_ven, "🍺 Barra": t_bar, "📦 Empacador": t_emp, "🧹 Auxiliar": t_aux, "🛎️ Hostes": t_hos, "Costo del Día": f"$ {c_tot:,.2f}"})

        df_maestra = pd.DataFrame(filas_maestras)
        dias_alternos = ["Domingo", "Martes", "Jueves", "Sábado"]
        def color_filas(row):
            dia_str = str(row['Día'])
            turno_str = str(row['Turno'])
            if "📌 TOTAL" in dia_str: return ['background-color: #FF9800; color: white; font-weight: bold;'] * len(row) 
            elif "⭐" in turno_str: return ['background-color: rgba(255, 215, 0, 0.25); font-weight: bold;'] * len(row) 
            elif any(d in dia_str for d in dias_alternos): return ['background-color: rgba(130, 130, 130, 0.20)'] * len(row) 
            else: return [''] * len(row) 
        st.dataframe(df_maestra.style.set_properties(**{'text-align': 'center'}).apply(color_filas, axis=1), height=830, use_container_width=False, hide_index=True, column_config={"Día": st.column_config.TextColumn("Día", width=250)})

        # --- AUDITORÍA QUIRÚRGICA DE CELDAS ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### 📊 Auditoría Visual de Carga Operativa y Empalmes (Celda por Celda)")
        
        c_sel1, c_sel2, c_sel3 = st.columns(3)
        with c_sel1: dia_aud = st.selectbox("📅 1. Día de la Semana:", dias_semana, key="aud_dia_sem")
        with c_sel2: turno_aud = st.selectbox("🕒 2. Turno a auditar:", ["☀️ Matutino (10-18)", "🌤️ Intermedio (14-22)", "🌙 Vespertino (17-01)"], key="aud_turno_sem")
        with c_sel3: puesto_aud = st.selectbox("🎯 3. Puesto a auditar:", ["🍳 Cocinero", "🍔 Vendedor", "🍺 Barra", "🖥️ Caja", "⭐️ Supervisor", "🛎️ Hostes", "📦 Empacador", "🧹 Auxiliar"], key="aud_puesto_sem")
            
        res_dia = st.session_state['resultados_diarios'][dia_aud]
        map_idx = {"🍳 Cocinero": 0, "🍔 Vendedor": 1, "🍺 Barra": 2, "🖥️ Caja": 3, "⭐️ Supervisor": 4, "🛎️ Hostes": 5, "📦 Empacador": 6, "🧹 Auxiliar": 7}
        t_key = 'M' if 'Matutino' in turno_aud else ('I' if 'Intermedio' in turno_aud else 'V')
        idx_rol = map_idx[puesto_aud]
        gente_celda = int(res_dia[t_key][idx_rol])
        
        if idx_rol in [0, 1, 2]:  
            rol_nombre = ["Cocina", "Salon", "Barra"][idx_rol]
            cap_val = [c_coc, c_sal, c_bar][idx_rol]
            cap_promedio = cap_val * factor_fatiga_mult  
            cap_fin = cap_val * (1.0 - (fatiga_pct / 100.0))
            
            blk_indices = [0, 1, 2] if t_key == 'M' else ([1, 2, 3] if t_key == 'I' else [2, 3, 4])
            cmds_turno = sum(res_dia['demanda_bruta'][rol_nombre][i] for i in blk_indices)
            extras_db = {'Cocina': st.session_state.db['demanda'][dia_aud]['ec'], 'Salon': st.session_state.db['demanda'][dia_aud]['es'], 'Barra': st.session_state.db['demanda'][dia_aud]['eb']}
            extras_turno = sum(extras_db[rol_nombre][i] for i in blk_indices)
            
            hrs_pura = round(cmds_turno / cap_promedio, 1) if cap_promedio > 0 else 0
            hrs_totales = round(hrs_pura + extras_turno, 1)
            hrs_autonomas = gente_celda * 8
            cap_comandas_autonoma = gente_celda * 8 * cap_promedio
            pct_saturacion = round((hrs_totales / hrs_autonomas) * 100, 1) if hrs_autonomas > 0 else 0
            
            bar_color = "#2CA02C" if pct_saturacion <= 100 else "#FF7F0E"
            bar_width = min(pct_saturacion, 100)
            
            if hrs_totales > hrs_autonomas:
                hrs_remanente = round(hrs_totales - hrs_autonomas, 1)
                cmds_remanente = round(hrs_remanente * cap_promedio, 0)
                txt_empalme = f"""<div style="background-color: #FFF8E1; border-left: 5px solid #FF8F00; padding: 15px; border-radius: 8px; margin-top: 15px;">
<p style="margin: 0 0 8px 0; font-size: 15px; color: #B36B00; font-weight: bold;">🔄 Dictamen de Cobertura mediante Empalme Operativo</p>
<p style="margin: 0; font-size: 14px; color: #333; line-height: 1.6;">El volumen requiere <b>{hrs_totales} horas-hombre</b>. La capacidad del personal asignado cubre <b>{hrs_autonomas} horas</b>.<br>👉 <b>Justificación Financiera:</b> El algoritmo mantiene la nómina ajustada en las horas de apertura/cierre de baja demanda. Las <b>{hrs_remanente} horas excedentes</b> ({cmds_remanente:,.0f} comandas) durante el "Rush" son absorbidas por el personal del turno posterior que se integra a la operación (Empalme de Turnos).</p></div>"""
            else:
                txt_empalme = f"""<div style="background-color: #E8F5E9; border-left: 5px solid #2E7D32; padding: 15px; border-radius: 8px; margin-top: 15px;"><p style="margin: 0; font-size: 14px; color: #1B5E20; line-height: 1.6;">✅ <b>Dictamen de Cobertura Autónoma:</b> El personal asignado cubre el 100% de la demanda ({hrs_totales} horas requeridas) manteniendo un margen operativo sano.</p></div>"""

            st.markdown(f"""<div style="background-color: #FFFFFF; border: 2px solid #1F77B4; border-radius: 15px; padding: 25px; margin-top: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08);">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #EEE; padding-bottom: 15px; margin-bottom: 20px;"><div><span style="font-size: 13px; color: #666; font-weight: bold; text-transform: uppercase;">RADIOGRAFÍA OPERATIVA DE CELDA (CON FACTOR DE FATIGA)</span><h4 style="margin: 4px 0 0 0; color: #1F77B4; font-size: 22px;">{puesto_aud} | {dia_aud} - {turno_aud}</h4></div>
<div style="background-color: #1F77B4; color: white; padding: 12px 25px; border-radius: 12px; text-align: center;"><span style="font-size: 11px; display: block; text-transform: uppercase; letter-spacing: 1px;">Personal Asignado</span><strong style="font-size: 24px;">{gente_celda} Colaborador(es)</strong></div></div>
<div style="display: flex; gap: 15px; margin-bottom: 20px;"><div style="flex: 1; background-color: #F8F9FA; padding: 15px; border-radius: 10px; border: 1px solid #E9ECEF; text-align: center;"><span style="font-size: 12px; color: #666; font-weight: bold;">DEMANDA ESPERADA</span><div style="font-size: 18px; font-weight: bold; color: #222; margin-top: 5px;">🔥 {cmds_turno:,.0f} Cmds</div></div>
<div style="flex: 1; background-color: #F8F9FA; padding: 15px; border-radius: 10px; border: 1px solid #E9ECEF; text-align: center;"><span style="font-size: 11px; color: #666; font-weight: bold;">DESGASTE HUMANO (-{fatiga_pct/2:.1f}% PROM.)</span><div style="font-size: 15px; font-weight: bold; color: #1F77B4; margin-top: 5px;">⚡ {cap_val} ➔ {cap_fin:.1f} cmds/hr</div></div>
<div style="flex: 1; background-color: #F8F9FA; padding: 15px; border-radius: 10px; border: 1px solid #E9ECEF; text-align: center;"><span style="font-size: 12px; color: #666; font-weight: bold;">CAPACIDAD AUTÓNOMA (REAL)</span><div style="font-size: 18px; font-weight: bold; color: #2CA02C; margin-top: 5px;">🛡️ {cap_comandas_autonoma:,.0f} Cmds</div></div></div>
<div style="margin-bottom: 15px;"><div style="display: flex; justify-content: space-between; font-size: 13px; font-weight: bold; color: #444; margin-bottom: 5px;"><span>ÍNDICE DE CARGA DEL TURNO (DEMANDA VS CAPACIDAD REAL):</span><span style="color: {bar_color};">{pct_saturacion}%</span></div>
<div style="background-color: #E9ECEF; border-radius: 10px; width: 100%; height: 16px; overflow: hidden; border: 1px solid #CCC;"><div style="background-color: {bar_color}; width: {bar_width}%; height: 100%;"></div></div></div>{txt_empalme}</div>""", unsafe_allow_html=True)
            
        else:  
            estado_txt = "ACTIVADO (Sí)" if gente_celda > 0 else "DESACTIVADO (No)"
            color_est = "#2CA02C" if gente_celda > 0 else "#666666"
            st.markdown(f"""<div style="background-color: #FFF9C4; border: 2px solid #FBC02D; border-radius: 15px; padding: 25px; margin-top: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.08);">
<div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #FCE588; padding-bottom: 15px; margin-bottom: 20px;"><div><span style="font-size: 13px; color: #8C6B00; font-weight: bold; text-transform: uppercase;">DIAGNÓSTICO DE PUESTO ESTRUCTURAL</span><h4 style="margin: 4px 0 0 0; color: #B38600; font-size: 22px;">{puesto_aud} | {dia_aud} - {turno_aud}</h4></div>
<div style="background-color: {color_est}; color: white; padding: 12px 25px; border-radius: 12px; text-align: center;"><span style="font-size: 11px; display: block; text-transform: uppercase; letter-spacing: 1px;">Asignación</span><strong style="font-size: 24px;">{gente_celda} Persona(s)</strong></div></div>
<p style="margin: 0; font-size: 15px; color: #222; line-height: 1.6;">📌 <b>Justificación de Puesto Estructural:</b><br>Esta posición opera bajo un criterio estructural. Su asignación depende de la matriz operativa dictada, no del volumen de comandas por hora.<br>👉 Para este bloque, la matriz indicó: <b style="color: {color_est};">{estado_txt}</b>.</p></div>""", unsafe_allow_html=True)
        st.markdown("---")

# ==========================================
# ⚖️ PESTAÑA 4: PLANTILLA IDEAL VS REAL (AJUSTE MÚLTIPLOS DE 6)
# ==========================================
with tab_ideal:
    if st.session_state['resultados_diarios'] is not None:
        st.markdown("""<div style="background-color: #F3E5F5; padding: 15px; border-left: 5px solid #9C27B0; border-radius: 5px; margin-bottom: 20px;"><h4 style="margin-top: 0; color: #9C27B0;">🧠 Análisis Ejecutivo de Contratación (Plantilla Ideal)</h4><p style="font-size: 14px; color: #333;"><b>1. Cálculo por Múltiplos de 6 Turnos:</b> El sistema suma el total de turnos semanales requeridos para cada puesto y los ajusta hacia arriba al múltiplo de 6 más cercano (Regla 6x1). De esta forma, se asigna exactly el personal necesario garantizando 1 día de descanso a la semana para todos.<br><b>2. Diagnóstico Financiero:</b> Compara la plantilla contratada hoy contra la plantilla ideal ajustada a múltiplos de 6.</p></div>""", unsafe_allow_html=True)
        st.subheader("⚖️ Análisis Financiero de Recursos Humanos")
        
        map_idx = {'Supervisor': 4, 'Caja': 3, 'Cocinero': 0, 'Vendedor': 1, 'Barra': 2, 'Empacador': 6, 'Auxiliar': 7, 'Hostes': 5}
        puestos_orden = ['Supervisor', 'Caja', 'Cocinero', 'Vendedor', 'Barra', 'Empacador', 'Auxiliar', 'Hostes']
        
        ideal = {}
        turnos_info = {}
        for p in puestos_orden:
            idx = map_idx[p]
            t_tot = sum(int(st.session_state['resultados_diarios'][d]['M'][idx] + st.session_state['resultados_diarios'][d]['I'][idx] + st.session_state['resultados_diarios'][d]['V'][idx]) for d in dias_semana)
            t_mult6 = math.ceil(t_tot / 6.0) * 6
            ideal_p = t_mult6 // 6
            ideal[p] = ideal_p
            turnos_info[p] = (t_tot, t_mult6)
        
        real = {'Supervisor': st.session_state.c_sup, 'Caja': st.session_state.c_caj, 'Cocinero': st.session_state.c_coc, 'Vendedor': st.session_state.c_sal, 'Barra': st.session_state.c_bar, 'Empacador': st.session_state.c_emp, 'Auxiliar': st.session_state.c_aux, 'Hostes': st.session_state.c_hos}
        
        fuga, ahorro = 0, 0
        for puesto in ideal.keys():
            dif = real[puesto] - ideal[puesto]; impacto = dif * salarios_map[puesto] * 7
            if dif > 0: fuga += impacto
            elif dif < 0: ahorro += abs(impacto)
                
        col1, col2 = st.columns(2)
        col1.markdown(f'<div class="anim_fuga"><p style="margin:0; font-size:15px; color:#555;">🔴 FUGA DE DINERO (Exceso de Plantilla)</p><h2 style="margin:0; color:#333;">$ {fuga:,.2f} / sem</h2></div>', unsafe_allow_html=True)
        col2.markdown(f'<div class="anim_ahorro"><p style="margin:0; font-size:15px; color:#555;">🟡 AHORRO RIESGOSO (Falta de Plantilla)</p><h2 style="margin:0; color:#333;">$ {ahorro:,.2f} / sem</h2></div>', unsafe_allow_html=True)
        st.write("<br>💡 **Nota Financiera:** El cálculo ideal se basa en turnos ajustados a múltiplos de 6 (cobertura 6x1 con 1 día de descanso). Si tienes una **Fuga** 🔴, pagas nómina sobrante. Si tienes **Ahorro Riesgoso** 🟡, falta personal para cubrir los turnos programados.", unsafe_allow_html=True)
        st.markdown("---")
        
        # --- TARJETAS DE IMPACTO PUESTO POR PUESTO ---
        st.markdown("### 📋 Diagnóstico Detallado (Tarjetas de Impacto)")
        iconos = {'Supervisor': '⭐️', 'Caja': '🖥️', 'Cocinero': '🍳', 'Vendedor': '🍔', 'Barra': '🍺', 'Empacador': '📦', 'Auxiliar': '🧹', 'Hostes': '🛎️'}
        puestos = list(ideal.keys())
        for i in range(0, len(puestos), 4):
            cols = st.columns(4)
            for j in range(4):
                if i + j < len(puestos):
                    p = puestos[i + j]
                    dif = real[p] - ideal[p]
                    cost = abs(dif) * salarios_map[p] * 7
                    t_tot, t_mult6 = turnos_info[p]
                    
                    if dif < 0:
                        bg, text, border, est, msg, anim = "#FFFFE0", "#B38600", "#FFE680", f"Faltan {abs(dif)} persona(s)", f"🟡 Ahorro Riesgoso:<br>+\\$ {cost:,.2f} /sem", "anim_ahorro"
                    elif dif > 0:
                        bg, text, border, est, msg, anim = "#FFF0F0", "#CC0000", "#FFCCCC", f"Sobran {dif} persona(s)", f"🔴 Fuga:<br>-\\$ {cost:,.2f} /sem", "anim_fuga"
                    else:
                        bg, text, border, est, msg, anim = "#F0FFF0", "#008000", "#CCFFCC", "Plantilla Perfecta", f"🟢 Balance:<br>\\$ 0.00", ""
                    
                    cols[j].markdown(f'<div class="{anim}" style="background-color: {bg}; border: 1px solid {border}; border-radius: 10px; padding: 15px; min-height: 180px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 15px;"><h4 style="margin: 0 0 5px 0; color: #333; font-size: 17px; line-height: 1.2;">{iconos[p]} {p}</h4><p style="margin: 0 0 3px 0; font-size: 13px; color: #333; line-height: 1.2;"><b>{est}</b></p><p style="margin: 0 0 3px 0; font-size: 12px; color: #555; line-height: 1.2;">(Ideal: {ideal[p]} | Tienes: {real[p]})</p><p style="margin: 0 0 8px 0; font-size: 11px; color: #777; line-height: 1.1;">Turnos: {t_tot} ➔ Múltiplo 6: {t_mult6}</p><h5 style="margin: 0; color: {text}; font-size: 15px; line-height: 1.3;">{msg}</h5></div>', unsafe_allow_html=True)

        st.markdown("---"); st.markdown("### 📊 Comparativo Gráfico (Ideal vs Real)")
        nombres_con_icono = [f"{iconos[p]} {p}" for p in ideal.keys()]
        df_rh = pd.DataFrame({'Puesto': nombres_con_icono * 2, 'Empleados': list(ideal.values()) + list(real.values()), 'Tipo': ['1. Plantilla IDEAL (Requerida)'] * 8 + ['2. Plantilla REAL (Contratada)'] * 8})
        fig_rh = px.bar(df_rh, x='Puesto', y='Empleados', color='Tipo', barmode='group', text_auto=True, color_discrete_map={'1. Plantilla IDEAL (Requerida)': '#1f77b4', '2. Plantilla REAL (Contratada)': '#ff7f0e'})
        fig_rh.update_layout(legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig_rh, use_container_width=True)
        st.markdown("""<div style="background-color: #FFF9C4; padding: 15px; border-left: 5px solid #FBC02D; border-radius: 8px; margin-top: 5px; margin-bottom: 25px;"><h5 style="margin-top: 0; color: #B38600;">💡 Guía rápida</h5><p style="font-size: 14px; color: #333; margin: 0;">Permite comparar visualmente el tamaño actual de tu equipo (Naranja) contra la estructura en múltiplos de 6 turnos (Azul).</p></div>""", unsafe_allow_html=True)