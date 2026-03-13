import streamlit as st
import pulp as pl
import pandas as pd
import plotly.express as px
import io
import json
import os
import math
import requests
import datetime


# --- ⚙️ CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Simplex: Nómina y Turnos Ideales", layout="wide", initial_sidebar_state="expanded")

# --- 🎨 INYECCIÓN DE CSS (ANIMACIÓN, CARGA AZUL Y TARJETAS) ---
st.markdown("""
<style>
/* 1. OCULTAR EL INDICADOR NATIVO PEQUEÑO DE ARRIBA A LA DERECHA */
div[data-testid="stStatusWidget"] {
    visibility: hidden;
    height: 0%;
    position: fixed;
}

/* 2. SUPER-ANIMACIÓN DE CARGA (SKELETONS) MULTICOLOR OPERATIVA */
[data-testid="stSkeleton"], .stSkeleton {
    background: linear-gradient(
        110deg, 
        rgba(255, 255, 255, 0.1) 30%, 
        #FFD700 45%, 
        #FF0000 50%, 
        #00FFFF 55%, 
        rgba(255, 255, 255, 0.1) 70%
    ) !important;
    background-size: 300% 100% !important; 
    animation: mega_shimmer 0.8s infinite linear !important; 
    border-radius: 15px !important;
    opacity: 0.9 !important;
    border: 2px solid rgba(255, 215, 0, 0.3);
    box-shadow: 0 0 15px rgba(255, 0, 0, 0.2); 
}

@keyframes mega_shimmer {
    0% { background-position: 300% 0; }
    100% { background-position: -300% 0; }
}

/* 3. MEGA-SPINNER AMARILLO CENTRADO */
div.stSpinner > div > div {
    border-color: #FFD700 transparent transparent transparent !important;
    width: 80px !important;
    height: 80px !important;
    border-width: 8px !important;
}
div.stSpinner {
    text-align: center;
    margin-top: 50px;
    font-size: 20px;
    font-weight: bold;
    color: #FFD700;
}

/* 4. ESTILO ESPECIAL PARA EL BOTÓN CUANDO ESTÁ 'RUNNING' */
.stButton > button:disabled {
    border: 5px solid #FF0000 !important;
    animation: pulse_red_border 1s infinite !important;
    background-color: #330000 !important;
    color: white !important;
    font-weight: bold !important;
}

@keyframes pulse_red_border {
    0% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0.7); }
    70% { box-shadow: 0 0 0 20px rgba(255, 0, 0, 0); }
    100% { box-shadow: 0 0 0 0 rgba(255, 0, 0, 0); }
}

/* 5. FONDO AZUL PARA EL CARGADOR DE EXCEL */
[data-testid="stFileUploader"] {
    background-color: #EBF5FB !important; 
    border: 2px dashed #2E86C1 !important; 
    border-radius: 10px !important;
    padding: 15px !important;
}
[data-testid="stFileUploader"] label {
    color: #154360 !important; 
    font-weight: bold !important;
}

/* 6. MAGIA PARA EL PDF */
@media print {
    section[data-testid="stSidebar"] { display: none !important; }
    header[data-testid="stHeader"] { display: none !important; }
    .stButton { display: none !important; }
    * { -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }
}
</style>
""", unsafe_allow_html=True)

# --- 💾 CONFIGURACIÓN MAESTRA ---
CONFIG_FILE = "config_simplex.json"
dias_semana = ["Domingo", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

DEFAULT_CONFIG = {
    's_coc': 350.0, 's_ven': 300.0, 's_bar': 320.0, 's_sup': 500.0, 's_caj': 300.0, 's_hos': 250.0,
    's_emp': 250.0, 's_aux': 250.0, 
    'c_coc': 8, 'c_sal': 12, 'c_bar': 15,
    'esp_pct': {d: 0.0 for d in dias_semana},
    'ideal_sup': 2, 'ideal_caj': 3, 'ideal_hos': 3,
    'ideal_emp': 2, 'ideal_aux': 2 
}

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

# --- 🗓️ CONSTANTES ---
bloques = ["10:00 a 14:00 (4 hrs)", "14:00 a 17:00 (3 hrs)", "17:00 a 18:00 (1 hr)", "18:00 a 22:00 (4 hrs)", "22:00 a 01:00 (3 hrs)"]
horas_por_bloque = [4, 3, 1, 4, 3]

# --- 🧠 BASE DE DATOS MAESTRA ---
if 'db' not in st.session_state:
    st.session_state.db = {
        'ventas': {},
        'fijos': {},
        'demanda': {}
    }
    for d in dias_semana:
        factor = 1.5 if d in ["Viernes", "Sábado", "Domingo"] else 1.0
        st.session_state.db['ventas'][d] = 25000.0 if d == "Viernes" else (30000.0 if d == "Sábado" else (22000.0 if d == "Domingo" else 15000.0))
        st.session_state.db['fijos'][d] = {
            'sm': False, 'si': True, 'sv': False,
            'cm': True, 'ci': False, 'cv': True,
            'hm': False, 'hi': True, 'hv': True,
            'em': False, 'ei': True, 'ev': True,
            'am': False, 'ai': True, 'av': True
        }
        st.session_state.db['demanda'][d] = {
            'cc': [15.0 * factor, 30.0 * factor, 20.0 * factor, 60.0 * factor, 25.0 * factor],
            'ec': [1.0, 0.0, 0.0, 0.5, 1.5],
            'cs': [20.0 * factor, 45.0 * factor, 30.0 * factor, 85.0 * factor, 30.0 * factor],
            'es': [1.0, 0.0, 0.0, 0.5, 1.5],
            'cb': [5.0 * factor, 20.0 * factor, 15.0 * factor, 70.0 * factor, 40.0 * factor],
            'eb': [1.0, 0.0, 0.0, 0.5, 1.5]
        }

if 'tope' not in st.session_state: st.session_state['tope'] = 20.0
if 'config_unlocked' not in st.session_state: st.session_state['config_unlocked'] = False
if 'resultados_diarios' not in st.session_state: st.session_state['resultados_diarios'] = None
if 'preview_v' not in st.session_state:
    st.session_state['preview_v'] = None; st.session_state['preview_f'] = None; st.session_state['preview_d'] = None
if 'plantilla_ideal' not in st.session_state: st.session_state['plantilla_ideal'] = {}

def sync_tope_slider(): st.session_state.tope = st.session_state.input_slider
def sync_tope_num(): st.session_state.tope = st.session_state.input_num

# --- 📥 FUNCIÓN PARA DESCARGAR MACHOTE ---
def generar_machote():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame({"Día": dias_semana, "Venta Proyectada ($)": [st.session_state.db['ventas'][d] for d in dias_semana]}).to_excel(writer, sheet_name="Ventas", index=False)
        fijos_filas = []
        for d in dias_semana:
            fijos_filas.append({
                "Día": d,
                "Sup_Matutino": "Si" if st.session_state.db['fijos'][d]['sm'] else "No", "Sup_Intermedio": "Si" if st.session_state.db['fijos'][d]['si'] else "No", "Sup_Vespertino": "Si" if st.session_state.db['fijos'][d]['sv'] else "No",
                "Caj_Matutino": "Si" if st.session_state.db['fijos'][d]['cm'] else "No", "Caj_Intermedio": "Si" if st.session_state.db['fijos'][d]['ci'] else "No", "Caj_Vespertino": "Si" if st.session_state.db['fijos'][d]['cv'] else "No",
                "Hos_Matutino": "Si" if st.session_state.db['fijos'][d]['hm'] else "No", "Hos_Intermedio": "Si" if st.session_state.db['fijos'][d]['hi'] else "No", "Hos_Vespertino": "Si" if st.session_state.db['fijos'][d]['hv'] else "No",
                "Emp_Matutino": "Si" if st.session_state.db['fijos'][d]['em'] else "No", "Emp_Intermedio": "Si" if st.session_state.db['fijos'][d]['ei'] else "No", "Emp_Vespertino": "Si" if st.session_state.db['fijos'][d]['ev'] else "No",
                "Aux_Matutino": "Si" if st.session_state.db['fijos'][d]['am'] else "No", "Aux_Intermedio": "Si" if st.session_state.db['fijos'][d]['ai'] else "No", "Aux_Vespertino": "Si" if st.session_state.db['fijos'][d]['av'] else "No"
            })
        pd.DataFrame(fijos_filas).to_excel(writer, sheet_name="Personal_Fijo", index=False)
        filas = []
        for d in dias_semana:
            for i, b in enumerate(bloques):
                filas.append({
                    "Día": d, "Bloque": b,
                    "Cmds_Cocina": st.session_state.db['demanda'][d]['cc'][i], "Extra_Cocina": st.session_state.db['demanda'][d]['ec'][i],
                    "Cmds_Salon": st.session_state.db['demanda'][d]['cs'][i],  "Extra_Salon": st.session_state.db['demanda'][d]['es'][i],
                    "Cmds_Barra": st.session_state.db['demanda'][d]['cb'][i],  "Extra_Barra": st.session_state.db['demanda'][d]['eb'][i]
                })
        pd.DataFrame(filas).to_excel(writer, sheet_name="Demanda", index=False)
    return output.getvalue()

# --- 🍔 ENCABEZADO ---
st.title("🍔 SIMPLEX: Tu Asistente de Nómina y RH")

# --- 🎛️ BARRA LATERAL ---
with st.sidebar:
    st.header("💰 1. Límite Financiero")
    st.number_input("✏️ Ingresa el % exacto:", min_value=10.0, max_value=40.0, value=st.session_state.tope, step=0.5, key="input_num", on_change=sync_tope_num)
    st.slider("🎚️ O ajusta con la barra:", min_value=10.0, max_value=40.0, value=st.session_state.tope, step=0.5, key="input_slider", on_change=sync_tope_slider)
    
    st.markdown("---")
    st.header("🔐 Configuración Maestra")
    if not st.session_state['config_unlocked']:
        st.write("🔒 Parámetros bloqueados.")
        pwd = st.text_input("Contraseña:", type="password", key="ui_pwd_input")
        if st.button("🔓 Desbloquear"):
            if pwd == "M@5terkey":
                st.session_state['config_unlocked'] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta.")
    else:
        st.success("🔓 Modo Edición Activo")
        with st.expander("💵 Ajuste de Salarios y Capacidades"):
            new_s_sup = st.number_input("Sal. ⭐️ Supervisor ($)", value=config_data['s_sup'])
            new_s_caj = st.number_input("Sal. 🖥️ Caja ($)", value=config_data['s_caj'])
            new_s_coc = st.number_input("Sal. 🍳 Cocinero ($)", value=config_data['s_coc'])
            new_s_ven = st.number_input("Sal. 🍔 Vendedor ($)", value=config_data['s_ven'])
            new_s_bar = st.number_input("Sal. 🍺 Barra ($)", value=config_data['s_bar'])
            new_s_emp = st.number_input("Sal. 📦 Empacador ($)", value=config_data.get('s_emp', 250.0))
            new_s_aux = st.number_input("Sal. 🧹 Auxiliar ($)", value=config_data.get('s_aux', 250.0))
            new_s_hos = st.number_input("Sal. 🛎️ Hostes ($)", value=config_data['s_hos'])
            st.markdown("---")
            new_c_coc = st.number_input("Cap. Cocina (cmd/hr)", value=config_data['c_coc'])
            new_c_sal = st.number_input("Cap. Salón (cmd/hr)", value=config_data['c_sal'])
            new_c_bar = st.number_input("Cap. Barra (cmd/hr)", value=config_data['c_bar'])
            
        with st.expander("🎯 Límites de Plantilla Fija"):
            new_ideal_sup = st.number_input("⭐️ Ideal Supervisor", min_value=0, value=config_data.get('ideal_sup', 2))
            new_ideal_caj = st.number_input("🖥️ Ideal Caja", min_value=0, value=config_data.get('ideal_caj', 3))
            new_ideal_emp = st.number_input("📦 Ideal Empacador", min_value=0, value=config_data.get('ideal_emp', 2))
            new_ideal_aux = st.number_input("🧹 Ideal Auxiliar", min_value=0, value=config_data.get('ideal_aux', 2))
            new_ideal_hos = st.number_input("🛎️ Ideal Hostes", min_value=0, value=config_data.get('ideal_hos', 3))
            
        with st.expander("🎉 Configurar Días Especiales"):
            new_esp = {}
            for d in dias_semana:
                val_actual = float(config_data.get('esp_pct', {}).get(d, 0.0))
                new_esp[d] = st.number_input(f"Incremento para {d} (%)", min_value=0.0, value=val_actual, step=5.0)
                
        if st.button("🔒 Guardar y Bloquear"):
            config_data.update({
                's_coc': new_s_coc, 's_ven': new_s_ven, 's_bar': new_s_bar, 's_sup': new_s_sup, 's_caj': new_s_caj, 's_hos': new_s_hos, 
                's_emp': new_s_emp, 's_aux': new_s_aux, 'c_coc': new_c_coc, 'c_sal': new_c_sal, 'c_bar': new_c_bar, 'esp_pct': new_esp,
                'ideal_sup': new_ideal_sup, 'ideal_caj': new_ideal_caj, 'ideal_hos': new_ideal_hos, 'ideal_emp': new_ideal_emp, 'ideal_aux': new_ideal_aux
            })
            save_config(config_data)
            st.session_state['config_unlocked'] = False
            st.rerun()

    st.markdown("---")
    st.header("🖨️ Exportar a PDF")
    modo_impresion = st.checkbox("📄 Activar Vista para PDF")
    if modo_impresion:
        st.info("💡 El reporte está listo. Presiona **Cmd + P** (Mac) o **Ctrl + P** (Windows) y elige 'Guardar como PDF'.")

# Mapeo de variables
s_coc, s_ven, s_bar = config_data['s_coc'], config_data['s_ven'], config_data['s_bar']
s_sup, s_caj, s_hos = config_data['s_sup'], config_data['s_caj'], config_data['s_hos']
s_emp, s_aux = config_data.get('s_emp', 250.0), config_data.get('s_aux', 250.0)
c_coc, c_sal, c_bar = config_data['c_coc'], config_data['c_sal'], config_data['c_bar']
esp_pct = config_data.get('esp_pct', {d: 0.0 for d in dias_semana})

ideal_sup_cfg = config_data.get('ideal_sup', 2)
ideal_caj_cfg = config_data.get('ideal_caj', 3)
ideal_hos_cfg = config_data.get('ideal_hos', 3)
ideal_emp_cfg = config_data.get('ideal_emp', 2)
ideal_aux_cfg = config_data.get('ideal_aux', 2)

salarios_map = {'Supervisor': s_sup, 'Caja': s_caj, 'Cocinero': s_coc, 'Vendedor': s_ven, 'Barra': s_bar, 'Empacador': s_emp, 'Auxiliar': s_aux, 'Hostes': s_hos}

# ==========================================
# 🧱 FUNCIONES MODULARES PARA RENDERIZAR
# ==========================================

def render_tab_carga():
    col_excel, col_rh = st.columns([1.5, 1.2])
    with col_excel:
        st.subheader("Paso 1: Sube tu Excel Semanal")
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

        # Selectbox en Streamlit
        selected_week = st.selectbox("Selecciona la semana", weeks)

        # Mostrar la semana elegida (opcional)
        st.write(f"Has seleccionado la semana **{selected_week}**")

        st.download_button(label="📥 Descargar Machote de Excel", data=generar_machote(), file_name="Machote_Semanal.xlsx", mime="application/vnd.ms-excel")
        uploaded_file = st.file_uploader("⬆️ **Arrastra o Selecciona tu archivo Excel aquí**", type=["xlsx"])
        if uploaded_file is not None:
            if st.button("⚙️ Leer Datos del Excel", type="primary"):
                try:
                    df_v = pd.read_excel(uploaded_file, sheet_name="Ventas")
                    df_f = pd.read_excel(uploaded_file, sheet_name="Personal_Fijo")
                    df_d = pd.read_excel(uploaded_file, sheet_name="Demanda")
                    st.session_state['preview_v'] = df_v; st.session_state['preview_f'] = df_f; st.session_state['preview_d'] = df_d
                    for _, row in df_v.iterrows():
                        dia = str(row['Día']).strip()
                        if dia in dias_semana: st.session_state.db['ventas'][dia] = float(row['Venta Proyectada ($)'])
                    def es_si(valor): return str(valor).strip().lower() == 'si'
                    for _, row in df_f.iterrows():
                        dia = str(row['Día']).strip()
                        if dia in dias_semana:
                            st.session_state.db['fijos'][dia]['sm'] = es_si(row.get('Sup_Matutino', 'No'))
                            st.session_state.db['fijos'][dia]['si'] = es_si(row.get('Sup_Intermedio', 'No'))
                            st.session_state.db['fijos'][dia]['sv'] = es_si(row.get('Sup_Vespertino', 'No'))
                            st.session_state.db['fijos'][dia]['cm'] = es_si(row.get('Caj_Matutino', 'No'))
                            st.session_state.db['fijos'][dia]['ci'] = es_si(row.get('Caj_Intermedio', 'No'))
                            st.session_state.db['fijos'][dia]['cv'] = es_si(row.get('Caj_Vespertino', 'No'))
                            st.session_state.db['fijos'][dia]['hm'] = es_si(row.get('Hos_Matutino', 'No'))
                            st.session_state.db['fijos'][dia]['hi'] = es_si(row.get('Hos_Intermedio', 'No'))
                            st.session_state.db['fijos'][dia]['hv'] = es_si(row.get('Hos_Vespertino', 'No'))
                            st.session_state.db['fijos'][dia]['em'] = es_si(row.get('Emp_Matutino', 'No'))
                            st.session_state.db['fijos'][dia]['ei'] = es_si(row.get('Emp_Intermedio', 'No'))
                            st.session_state.db['fijos'][dia]['ev'] = es_si(row.get('Emp_Vespertino', 'No'))
                            st.session_state.db['fijos'][dia]['am'] = es_si(row.get('Aux_Matutino', 'No'))
                            st.session_state.db['fijos'][dia]['ai'] = es_si(row.get('Aux_Intermedio', 'No'))
                            st.session_state.db['fijos'][dia]['av'] = es_si(row.get('Aux_Vespertino', 'No'))
                    for d in dias_semana:
                        df_dia = df_d[df_d['Día'].str.strip() == d].reset_index()
                        if not df_dia.empty and len(df_dia) == 5:
                            for i in range(5):
                                st.session_state.db['demanda'][d]['cc'][i] = float(df_dia['Cmds_Cocina'].iloc[i])
                                st.session_state.db['demanda'][d]['ec'][i] = float(df_dia['Extra_Cocina'].iloc[i])
                                st.session_state.db['demanda'][d]['cs'][i] = float(df_dia['Cmds_Salon'].iloc[i])
                                st.session_state.db['demanda'][d]['es'][i] = float(df_dia['Extra_Salon'].iloc[i])
                                st.session_state.db['demanda'][d]['cb'][i] = float(df_dia['Cmds_Barra'].iloc[i])
                                st.session_state.db['demanda'][d]['eb'][i] = float(df_dia['Extra_Barra'].iloc[i])
                    st.session_state['resultados_diarios'] = None 
                    st.success("✅ ¡Datos leídos con éxito! Revisa la vista previa abajo.")
                except Exception as e:
                    st.error(f"⚠️ Error al leer el Excel: {e}")

    with col_rh:
        st.subheader("👥 Paso 2: Personal Contratado")
        st.info("💡 Ingresa tu plantilla actual.")
        descanso_sup = st.selectbox("🏖️ Descanso Supervisor:", dias_semana, index=1)
        st.session_state['descanso_sup'] = descanso_sup
        
        c_rh1, c_rh2 = st.columns(2)
        with c_rh1:
            st.session_state['c_sup'] = st.number_input("⭐️ Supervisor (Contr.)", min_value=0, value=1)
            st.session_state['c_caj'] = st.number_input("🖥️ Caja (Contr.)", min_value=0, value=2)
            st.session_state['c_coc'] = st.number_input("🍳 Cocinero (Contr.)", min_value=0, value=3)
            st.session_state['c_sal'] = st.number_input("🍔 Vendedor (Contr.)", min_value=0, value=4)
        with c_rh2:
            st.session_state['c_bar'] = st.number_input("🍺 Barra (Contr.)", min_value=0, value=2)
            st.session_state['c_emp'] = st.number_input("📦 Empacador (Contr.)", min_value=0, value=2)
            st.session_state['c_aux'] = st.number_input("🧹 Auxiliar (Contr.)", min_value=0, value=2)
            st.session_state['c_hos'] = st.number_input("🛎️ Hostes (Contr.)", min_value=0, value=2)

    if st.session_state['preview_v'] is not None:
        st.divider()
        with st.expander("👀 Vista Previa de tu Excel (Clic para expandir)"):
            c1, c2 = st.columns(2)
            with c1: st.dataframe(st.session_state['preview_v'], use_container_width=True)
            with c2: st.dataframe(st.session_state['preview_f'], use_container_width=True)
            st.dataframe(st.session_state['preview_d'], use_container_width=True)

    st.divider()
    st.subheader("Paso 3: Calcular Optimización")
    if st.button("🚀 CALCULAR PLANTILLA IDEAL (CLICK AQUÍ)", type="primary", use_container_width=True):
        with st.spinner("🚨 ¡ATENCIÓN! CALCULANDO NÓMINA... ESPERA A QUE TERMINE 🚨"):
            resultados_diarios = {}
            costo_total_semana = 0; venta_total_semana = 0; dias_inviables = []
            turnos_semanales = {'Cocina': 0, 'Salon': 0, 'Barra': 0} 
            capacidades = {'Cocina': c_coc, 'Salon': c_sal, 'Barra': c_bar}
            roles = ['Cocina', 'Salon', 'Barra']; turnos = ['M', 'I', 'V']
            
            for d in dias_semana:
                modelo = pl.LpProblem(f"Optimizacion_{d}", pl.LpMinimize)
                vars_personal = pl.LpVariable.dicts(f"Pers_{d}", [(r, t) for r in roles for t in turnos], lowBound=0, cat='Integer')
                modelo += pl.lpSum([vars_personal[(r, t)] for r in roles for t in turnos])
                
                porcentaje_extra = float(esp_pct.get(d, 0.0))
                factor_crecimiento = 1.0 + (porcentaje_extra / 100.0)
                venta_ajustada = st.session_state.db['ventas'][d] * factor_crecimiento
                venta_total_semana += venta_ajustada 
                
                demandas = {
                    'Cocina': [cmd * factor_crecimiento for cmd in st.session_state.db['demanda'][d]['cc']],
                    'Salon':  [cmd * factor_crecimiento for cmd in st.session_state.db['demanda'][d]['cs']],
                    'Barra':  [cmd * factor_crecimiento for cmd in st.session_state.db['demanda'][d]['cb']]
                }
                extras = {
                    'Cocina': st.session_state.db['demanda'][d]['ec'],
                    'Salon':  st.session_state.db['demanda'][d]['es'],
                    'Barra':  st.session_state.db['demanda'][d]['eb']
                }
                
                plot_data_req = {'Cocina': [], 'Salon': [], 'Barra': []}
                plot_data_prov = {'Cocina': [], 'Salon': [], 'Barra': []}
                
                for r in roles:
                    for i in range(5):
                        req_horas = (demandas[r][i] / capacidades[r]) + extras[r][i]
                        if i == 0:   gente = vars_personal[(r, 'M')]
                        elif i == 1: gente = vars_personal[(r, 'M')] + vars_personal[(r, 'I')]
                        elif i == 2: gente = vars_personal[(r, 'M')] + vars_personal[(r, 'I')] + vars_personal[(r, 'V')]
                        elif i == 3: gente = vars_personal[(r, 'I')] + vars_personal[(r, 'V')]
                        elif i == 4: gente = vars_personal[(r, 'V')]
                        modelo += (gente * horas_por_bloque[i]) >= req_horas

                sm_val = st.session_state.db['fijos'][d]['sm']; si_val = st.session_state.db['fijos'][d]['si']; sv_val = st.session_state.db['fijos'][d]['sv']
                if d == st.session_state['descanso_sup']: sm_val, si_val, sv_val = False, False, False 
                
                q_sup = sum([sm_val, si_val, sv_val])
                q_caj = sum([st.session_state.db['fijos'][d]['cm'], st.session_state.db['fijos'][d]['ci'], st.session_state.db['fijos'][d]['cv']])
                q_hos = sum([st.session_state.db['fijos'][d]['hm'], st.session_state.db['fijos'][d]['hi'], st.session_state.db['fijos'][d]['hv']])
                q_emp = sum([st.session_state.db['fijos'][d]['em'], st.session_state.db['fijos'][d]['ei'], st.session_state.db['fijos'][d]['ev']])
                q_aux = sum([st.session_state.db['fijos'][d]['am'], st.session_state.db['fijos'][d]['ai'], st.session_state.db['fijos'][d]['av']])
                
                c_fijo_dia = (q_sup * s_sup) + (q_caj * s_caj) + (q_hos * s_hos) + (q_emp * s_emp) + (q_aux * s_aux)
                presupuesto_diario = venta_ajustada * (st.session_state['tope'] / 100)
                c_var_dia = pl.lpSum([vars_personal[('Cocina', t)] * s_coc + vars_personal[('Salon', t)] * s_ven + vars_personal[('Barra', t)] * s_bar for t in turnos])
                
                modelo += (c_var_dia + c_fijo_dia) <= presupuesto_diario
                status = modelo.solve()
                
                if pl.LpStatus[status] == 'Optimal':
                    c_var_real = pl.value(c_var_dia)
                    c_total_dia = c_var_real + c_fijo_dia
                    costo_total_semana += c_total_dia
                    
                    for r in roles:
                        for i in range(5):
                            plot_data_req[r].append(round((demandas[r][i] / capacidades[r]) + extras[r][i], 1))
                            if i == 0:   g = vars_personal[(r, 'M')].varValue
                            elif i == 1: g = vars_personal[(r, 'M')].varValue + vars_personal[(r, 'I')].varValue
                            elif i == 2: g = vars_personal[(r, 'M')].varValue + vars_personal[(r, 'I')].varValue + vars_personal[(r, 'V')].varValue
                            elif i == 3: g = vars_personal[(r, 'I')].varValue + vars_personal[(r, 'V')].varValue
                            elif i == 4: g = vars_personal[(r, 'V')].varValue
                            plot_data_prov[r].append(round(g * horas_por_bloque[i], 1))
                    
                    resultados_diarios[d] = {
                        'M': [vars_personal[('Cocina','M')].varValue, vars_personal[('Salon','M')].varValue, vars_personal[('Barra','M')].varValue, int(st.session_state.db['fijos'][d]['cm']), int(sm_val), int(st.session_state.db['fijos'][d]['hm']), int(st.session_state.db['fijos'][d]['em']), int(st.session_state.db['fijos'][d]['am'])] ,
                        'I': [vars_personal[('Cocina','I')].varValue, vars_personal[('Salon','I')].varValue, vars_personal[('Barra','I')].varValue, int(st.session_state.db['fijos'][d]['ci']), int(si_val), int(st.session_state.db['fijos'][d]['hi']), int(st.session_state.db['fijos'][d]['ei']), int(st.session_state.db['fijos'][d]['ai'])] ,
                        'V': [vars_personal[('Cocina','V')].varValue, vars_personal[('Salon','V')].varValue, vars_personal[('Barra','V')].varValue, int(st.session_state.db['fijos'][d]['cv']), int(sv_val), int(st.session_state.db['fijos'][d]['hv']), int(st.session_state.db['fijos'][d]['ev']), int(st.session_state.db['fijos'][d]['av'])] ,
                        'Costo': c_total_dia, 'Costo_Fijo': c_fijo_dia, 'Costo_Var': c_var_real, 'Venta_Ajustada': venta_ajustada, 'Es_Especial': porcentaje_extra > 0, 'Pct_Extra': porcentaje_extra,
                        'req': plot_data_req, 'prov': plot_data_prov, 'demanda_bruta': demandas
                    }
                    turnos_semanales['Cocina'] += sum([vars_personal[('Cocina', t)].varValue for t in turnos])
                    turnos_semanales['Salon'] += sum([vars_personal[('Salon', t)].varValue for t in turnos])
                    turnos_semanales['Barra'] += sum([vars_personal[('Barra', t)].varValue for t in turnos])
                else:
                    dias_inviables.append(d)

            if dias_inviables:
                st.error(f"⚠️ **Presupuesto Inviable en:** {', '.join(dias_inviables)}. \n El % de nómina no alcanza. Aumenta el 'Tope Máximo' o asigna un % extra de Día Especial.")
                st.session_state['resultados_diarios'] = None
            else:
                st.session_state['resultados_diarios'] = resultados_diarios
                st.session_state['venta_total_semana_calc'] = venta_total_semana
                st.session_state['costo_total_semana_calc'] = costo_total_semana
                
                plantilla_final = {
                    'Supervisor': ideal_sup_cfg, 'Caja': ideal_caj_cfg,
                    'Cocinero': math.ceil(turnos_semanales['Cocina'] / 6.0),
                    'Vendedor': math.ceil(turnos_semanales['Salon'] / 6.0),
                    'Barra': math.ceil(turnos_semanales['Barra'] / 6.0),
                    'Empacador': ideal_emp_cfg, 'Auxiliar': ideal_aux_cfg, 'Hostes': ideal_hos_cfg
                }
                st.session_state['plantilla_ideal'] = plantilla_final
                st.success("✅ ¡Cálculo Exitoso! Explora los resultados o enciende el switch de impresión a PDF en el menú lateral.")

def render_tab_diario():
    if st.session_state['resultados_diarios'] is None:
        st.warning("👈 Sube tu Excel en la Pestaña 1 y presiona 'Calcular'.")
        return
    dia_seleccionado = st.selectbox("👉 Elige el día a analizar:", dias_semana, key="sel_dia_print")
    res_dia = st.session_state['resultados_diarios'][dia_seleccionado]
    venta_dia = res_dia['Venta_Ajustada']
    pct_dia = (res_dia['Costo'] / venta_dia) * 100 if venta_dia > 0 else 0
    
    st.markdown("---")
    if res_dia['Es_Especial']:
        st.success(f"🎉 **¡DÍA ESPECIAL ACTIVO!** Incremento del **{res_dia['Pct_Extra']:g}%** a la venta y comandas.")
    if dia_seleccionado == st.session_state.get('descanso_sup', ''):
        st.info(f"🏖️ **DESCANSO DEL SUPERVISOR:** Hoy no se presupuestó al ⭐️ Supervisor por ser su día libre.")

    col1, col2, col3 = st.columns(3)
    col1.metric(label=f"💰 Venta Esperada ({dia_seleccionado})", value=f"$ {venta_dia:,.2f}")
    col2.metric(label=f"💸 Costo Nómina", value=f"$ {res_dia['Costo']:,.2f}")
    col3.metric(label=f"📈 % de Nómina", value=f"{pct_dia:.1f} %")
    
    st.info(f"🧐 **Desglose de Nómina:** Costo Fijo: \\$ {res_dia['Costo_Fijo']:,.2f}  |  Costo Variable: \\$ {res_dia['Costo_Var']:,.2f}")
    st.markdown("---")
    
    # --- NUEVO: TABLA DIARIA CON TOTALES ---
    st.subheader(f"📋 Plantilla Asignada para el {dia_seleccionado}")
    
    total_sup_dia = int(res_dia['M'][4]) + int(res_dia['I'][4]) + int(res_dia['V'][4])
    total_caj_dia = int(res_dia['M'][3]) + int(res_dia['I'][3]) + int(res_dia['V'][3])
    total_coc_dia = int(res_dia['M'][0]) + int(res_dia['I'][0]) + int(res_dia['V'][0])
    total_ven_dia = int(res_dia['M'][1]) + int(res_dia['I'][1]) + int(res_dia['V'][1])
    total_bar_dia = int(res_dia['M'][2]) + int(res_dia['I'][2]) + int(res_dia['V'][2])
    total_emp_dia = int(res_dia['M'][6]) + int(res_dia['I'][6]) + int(res_dia['V'][6])
    total_aux_dia = int(res_dia['M'][7]) + int(res_dia['I'][7]) + int(res_dia['V'][7])
    total_hos_dia = int(res_dia['M'][5]) + int(res_dia['I'][5]) + int(res_dia['V'][5])

    filas_diarias = [
        {"Turno": "☀️ Matutino (10-18)", "⭐️ Supervisor": int(res_dia['M'][4]), "🖥️ Caja": int(res_dia['M'][3]), "🍳 Cocinero": int(res_dia['M'][0]), "🍔 Vendedor": int(res_dia['M'][1]), "🍺 Barra": int(res_dia['M'][2]), "📦 Empacador": int(res_dia['M'][6]), "🧹 Auxiliar": int(res_dia['M'][7]), "🛎️ Hostes": int(res_dia['M'][5])},
        {"Turno": "🌤️ Intermedio (14-22)", "⭐️ Supervisor": int(res_dia['I'][4]), "🖥️ Caja": int(res_dia['I'][3]), "🍳 Cocinero": int(res_dia['I'][0]), "🍔 Vendedor": int(res_dia['I'][1]), "🍺 Barra": int(res_dia['I'][2]), "📦 Empacador": int(res_dia['I'][6]), "🧹 Auxiliar": int(res_dia['I'][7]), "🛎️ Hostes": int(res_dia['I'][5])},
        {"Turno": "🌙 Vespertino (17-01)", "⭐️ Supervisor": int(res_dia['V'][4]), "🖥️ Caja": int(res_dia['V'][3]), "🍳 Cocinero": int(res_dia['V'][0]), "🍔 Vendedor": int(res_dia['V'][1]), "🍺 Barra": int(res_dia['V'][2]), "📦 Empacador": int(res_dia['V'][6]), "🧹 Auxiliar": int(res_dia['V'][7]), "🛎️ Hostes": int(res_dia['V'][5])},
        {"Turno": "📌 TOTAL DÍA (TURNOS)", "⭐️ Supervisor": total_sup_dia, "🖥️ Caja": total_caj_dia, "🍳 Cocinero": total_coc_dia, "🍔 Vendedor": total_ven_dia, "🍺 Barra": total_bar_dia, "📦 Empacador": total_emp_dia, "🧹 Auxiliar": total_aux_dia, "🛎️ Hostes": total_hos_dia}
    ]
    
    df_diario = pd.DataFrame(filas_diarias)
    def color_filas_diarias(row):
        if "📌 TOTAL" in str(row['Turno']): return ['background-color: #1F77B4; color: white; font-weight: bold;'] * len(row)
        return [''] * len(row)
        
    st.dataframe(df_diario.style.apply(color_filas_diarias, axis=1), use_container_width=True, hide_index=True)
    
    # --- ANÁLISIS EJECUTIVO DIARIO CON EMOJIS EXPLICADOS ---
    st.markdown("""
    <div style="background-color: #E8F4F8; padding: 15px; border-left: 5px solid #1F77B4; border-radius: 5px; margin-bottom: 20px;">
        <h4 style="margin-top: 0; color: #1F77B4;">🧠 Análisis Ejecutivo del Cálculo Diario</h4>
        <p style="font-size: 14px; color: #333;">
            <b>¿Cómo se llegó a este número hoy?</b><br>
            <b>1. Puestos Operativos (🍳 Cocinero, 🍔 Vendedor, 🍺 Barra):</b> El algoritmo analizó las ventas y comandas esperadas para cada hora del día. Dividió el volumen de trabajo entre la capacidad de cada puesto (ej. comandas por hora de un cocinero) y asignó matemáticamente a las personas justas para cubrir los picos de "Rush", garantizando que el servicio no caiga pero sin gastar un solo peso de más fuera de tu límite de nómina.<br>
            <b>2. Puestos Estructurales (⭐️ Supervisor, 🖥️ Caja, 📦 Empacador, 🧹 Auxiliar, 🛎️ Hostes):</b> Estas posiciones no dependen del volumen de clientes. El sistema simplemente leyó tu "Machote de Excel" para este día y asignó (o descansó) al personal exactamente como tú lo pre-configuraste.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown(f"### 🌋 Gráfico 1: El Pulso del Restaurante (Rush)")
    dem_c = res_dia['demanda_bruta']['Cocina']; dem_s = res_dia['demanda_bruta']['Salon']; dem_b = res_dia['demanda_bruta']['Barra']
    nombres_bloques_cortos = [b[:11] for b in bloques]
    df_rush = pd.DataFrame({'Bloque Horario': nombres_bloques_cortos * 3, 'Comandas': dem_c + dem_s + dem_b, 'Área': ['🍳 Cocina']*5 + ['🍔 Salón']*5 + ['🍺 Barra']*5})
    st.plotly_chart(px.area(df_rush, x='Bloque Horario', y='Comandas', color='Área', color_discrete_map={'🍳 Cocina': '#FF7F0E', '🍔 Salón': '#1F77B4', '🍺 Barra': '#2CA02C'}), use_container_width=True)
    
    st.markdown(f"### ⚖️ Gráfico 2: Cobertura de Personal")
    area_grafico = st.radio("Elige el Área:", ["Cocina", "Salon", "Barra"], horizontal=True, key="sel_area_print")
    df_plot = pd.DataFrame({'Bloque Horario': nombres_bloques_cortos * 2, 'Horas': res_dia['req'][area_grafico] + res_dia['prov'][area_grafico], 'Indicador': ['1. Horas NECESARIAS (Demanda)']*5 + ['2. Horas PROGRAMADAS (Personal)']*5})
    fig_bar = px.bar(df_plot, x='Bloque Horario', y='Horas', color='Indicador', barmode='group', text_auto='.1f', color_discrete_map={'1. Horas NECESARIAS (Demanda)': '#d62728', '2. Horas PROGRAMADAS (Personal)': '#2ca02c'})
    fig_bar.update_layout(legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_bar, use_container_width=True)

def render_tab_semanal():
    if st.session_state['resultados_diarios'] is None:
        st.warning("👈 Sube tu Excel en la Pestaña 1 y presiona 'Calcular'.")
        return
    venta_total_sem = st.session_state['venta_total_semana_calc']
    costo_total_sem = st.session_state['costo_total_semana_calc']
    pct_semanal_real = (costo_total_sem / venta_total_sem) * 100 if venta_total_sem > 0 else 0
    
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric(label="💰 Venta Total Proyectada", value=f"$ {venta_total_sem:,.2f}")
    kpi2.metric(label="💸 Costo Total Nómina", value=f"$ {costo_total_sem:,.2f}")
    kpi3.metric(label="🏆 % Nómina Promedio", value=f"{pct_semanal_real:.1f} %")
    
    st.success(f"🧐 **¡Resultado Exitoso!** El algoritmo armó la plantilla diaria protegiendo tus finanzas y promediando un **{pct_semanal_real:.1f} %**.")
    
    # --- ANÁLISIS EJECUTIVO SEMANAL ---
    st.markdown("""
    <div style="background-color: #FFF3E0; padding: 15px; border-left: 5px solid #FFC107; border-radius: 5px; margin-bottom: 20px;">
        <h4 style="margin-top: 0; color: #FF9800;">🧠 Análisis Ejecutivo Semanal</h4>
        <p style="font-size: 14px; color: #333;">
            <b>¿Cómo se proyecta tu semana completa?</b><br>
            Al evaluar los 7 días en conjunto, el sistema asegura que la rentabilidad global se mantenga intacta, incluso si tienes "Días Especiales" (donde se infló el presupuesto y las comandas temporalmente). <br><br>
            Para la <b>Plantilla Maestra Semanal (Tabla Inferior)</b>, el algoritmo consolida todos los turnos diarios. Esta tabla es tu hoja de ruta final: te dice exactamente a cuántos empleados necesitas convocar cada día y en qué turno, garantizando que el gasto final sea el mostrado arriba.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    costos_lista = [st.session_state['resultados_diarios'][d]['Costo'] for d in dias_semana]
    ventas_lista = [st.session_state['resultados_diarios'][d]['Venta_Ajustada'] for d in dias_semana]
    df_sem = pd.DataFrame({'Día': dias_semana * 2, 'Dinero ($)': ventas_lista + costos_lista, 'Concepto': ['1. Venta Esperada']*7 + ['2. Costo de Nómina']*7})
    fig_sem = px.bar(df_sem, x='Día', y='Dinero ($)', color='Concepto', barmode='group', text_auto='.2s', color_discrete_map={'1. Venta Esperada': '#2ca02c', '2. Costo de Nómina': '#d62728'})
    fig_sem.update_layout(legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_sem, use_container_width=True)
    st.markdown("---")
    
    st.subheader("📋 Tu Plantilla Maestra Semanal")
    filas_maestras = []
    for d in dias_semana:
        res = st.session_state['resultados_diarios'][d]
        nombre_dia = d
        if res['Es_Especial']: nombre_dia += f" ⭐ (+{res['Pct_Extra']:g}%)"
        if d == st.session_state.get('descanso_sup', ''): nombre_dia += " 🏖️(Descanso Sup)"
        
        filas_maestras.append({"Día": nombre_dia, "Turno": "☀️ Matutino", "⭐️ Supervisor": int(res['M'][4]), "🖥️ Caja": int(res['M'][3]), "🍳 Cocinero": int(res['M'][0]), "🍔 Vendedor": int(res['M'][1]), "🍺 Barra": int(res['M'][2]), "📦 Empacador": int(res['M'][6]), "🧹 Auxiliar": int(res['M'][7]), "🛎️ Hostes": int(res['M'][5]), "Costo del Día": f"$ {res['Costo']:,.2f}"})
        filas_maestras.append({"Día": nombre_dia, "Turno": "🌤️ Intermedio", "⭐️ Supervisor": int(res['I'][4]), "🖥️ Caja": int(res['I'][3]), "🍳 Cocinero": int(res['I'][0]), "🍔 Vendedor": int(res['I'][1]), "🍺 Barra": int(res['I'][2]), "📦 Empacador": int(res['I'][6]), "🧹 Auxiliar": int(res['I'][7]), "🛎️ Hostes": int(res['I'][5]), "Costo del Día": "---"})
        filas_maestras.append({"Día": nombre_dia, "Turno": "🌙 Vespertino", "⭐️ Supervisor": int(res['V'][4]), "🖥️ Caja": int(res['V'][3]), "🍳 Cocinero": int(res['V'][0]), "🍔 Vendedor": int(res['V'][1]), "🍺 Barra": int(res['V'][2]), "📦 Empacador": int(res['V'][6]), "🧹 Auxiliar": int(res['V'][7]), "🛎️ Hostes": int(res['V'][5]), "Costo del Día": "---"})
        
    total_sup = sum(f['⭐️ Supervisor'] for f in filas_maestras)
    total_caj = sum(f['🖥️ Caja'] for f in filas_maestras)
    total_coc = sum(f['🍳 Cocinero'] for f in filas_maestras)
    total_ven = sum(f['🍔 Vendedor'] for f in filas_maestras)
    total_bar = sum(f['🍺 Barra'] for f in filas_maestras)
    total_emp = sum(f['📦 Empacador'] for f in filas_maestras)
    total_aux = sum(f['🧹 Auxiliar'] for f in filas_maestras)
    total_hos = sum(f['🛎️ Hostes'] for f in filas_maestras)

    filas_maestras.append({
        "Día": "📌 TOTAL SEMANA (TURNOS)", "Turno": "---", 
        "⭐️ Supervisor": total_sup, "🖥️ Caja": total_caj, "🍳 Cocinero": total_coc, "🍔 Vendedor": total_ven, 
        "🍺 Barra": total_bar, "📦 Empacador": total_emp, "🧹 Auxiliar": total_aux, "🛎️ Hostes": total_hos, 
        "Costo del Día": f"$ {costo_total_sem:,.2f}"
    })

    df_maestra = pd.DataFrame(filas_maestras)
    dias_alternos = ["Domingo", "Martes", "Jueves", "Sábado"]
    def color_filas(row):
        dia_str = str(row['Día'])
        if "📌 TOTAL" in dia_str: return ['background-color: #1F77B4; color: white; font-weight: bold;'] * len(row)
        elif "⭐" in dia_str: return ['background-color: rgba(255, 215, 0, 0.25)'] * len(row) 
        elif any(d in dia_str for d in dias_alternos): return ['background-color: rgba(130, 130, 130, 0.20)'] * len(row) 
        else: return [''] * len(row) 
    
    df_estilizado = df_maestra.style.apply(color_filas, axis=1)
    st.dataframe(df_estilizado, use_container_width=True, hide_index=True, column_config={"Día": st.column_config.TextColumn("Día", width=250)})

def render_tab_ideal():
    if st.session_state['resultados_diarios'] is None:
        st.warning("👈 Sube tu Excel en la Pestaña 1 y presiona 'Calcular'.")
        return
    
    st.subheader("⚖️ Análisis Financiero de Recursos Humanos")
    ideal = st.session_state['plantilla_ideal']
    real = {
        'Supervisor': st.session_state.get('c_sup',0), 'Caja': st.session_state.get('c_caj',0), 'Cocinero': st.session_state.get('c_coc',0),
        'Vendedor': st.session_state.get('c_sal',0), 'Barra': st.session_state.get('c_bar',0), 'Empacador': st.session_state.get('c_emp',0),
        'Auxiliar': st.session_state.get('c_aux',0), 'Hostes': st.session_state.get('c_hos',0)
    }
    
    fuga_semanal = 0; ahorro_semanal = 0
    for puesto in ideal.keys():
        dif = real[puesto] - ideal[puesto]
        impacto = dif * salarios_map[puesto] * 7
        if dif > 0: fuga_semanal += impacto
        elif dif < 0: ahorro_semanal += abs(impacto)
            
    col_fuga, col_ahorro = st.columns(2)
    col_fuga.metric("🔴 FUGA DE DINERO (Exceso de Plantilla)", f"$ {fuga_semanal:,.2f} / sem")
    col_ahorro.metric("🟡 AHORRO RIESGOSO (Falta de Plantilla)", f"$ {ahorro_semanal:,.2f} / sem")
    
    st.write("💡 **Nota Financiera:** Si tienes una **Fuga** 🔴, estás pagando nómina que no necesitas. Si tienes un **Ahorro Riesgoso** 🟡, te ahorras dinero, pero el personal está sobrecargado y el servicio corre peligro. Si tienes un **Balance** 🟢, tu plantilla es perfecta.")
    
    # --- ANÁLISIS EJECUTIVO RH CON NOMBRES EXPLÍCITOS ---
    st.markdown("""
    <div style="background-color: #F3E5F5; padding: 15px; border-left: 5px solid #9C27B0; border-radius: 5px; margin-top: 15px; margin-bottom: 20px;">
        <h4 style="margin-top: 0; color: #9C27B0;">🧠 Análisis Ejecutivo de Contratación (Plantilla Ideal)</h4>
        <p style="font-size: 14px; color: #333;">
            <b>¿Cómo defino a cuántas personas reales debo tener en nómina mensual?</b><br>
            <b>1. Para Operativos (🍳 Cocinero, 🍔 Vendedor, 🍺 Barra):</b> El sistema sumó todos los turnos que te pidió la "Plantilla Maestra Semanal" y los dividió entre 6 días. Al redondear matemáticamente hacia arriba (Regla 6x1), el algoritmo te dice exactamente el número de empleados que necesitas contratar para que tu restaurante cubra todos sus turnos <b>y al mismo tiempo garantices que todos descansen 1 día a la semana.</b><br>
            <b>2. Para Estructurales Fijos (⭐️ Supervisor, 🖥️ Caja, 📦 Empacador, 🧹 Auxiliar, 🛎️ Hostes):</b> El sistema no usa matemáticas de volumen para ellos. Directamente respeta el límite de personal "Ideal" que tú como Director configuraste en el panel lateral, ya que estos puestos dependen de tu formato de negocio (ej. "En esta sucursal solo quiero 2 cajeros fijos").
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📋 Diagnóstico Detallado (Tarjetas de Impacto)")
    
    iconos_puestos = {'Supervisor': '⭐️', 'Caja': '🖥️', 'Cocinero': '🍳', 'Vendedor': '🍔', 'Barra': '🍺', 'Empacador': '📦', 'Auxiliar': '🧹', 'Hostes': '🛎️'}
    
    def crear_tarjeta(puesto, necesitas, tienes, diferencia, costo_dif):
        icono = iconos_puestos[puesto]
        if diferencia < 0:
            bg = "#FFFFE0"; border = "#FFE680"; text = "#B38600" 
            estado = f"Faltan {abs(diferencia)} persona(s)"
            msg_dinero = f"🟡 Ahorro Riesgoso:<br>+\\$ {costo_dif:,.2f} /sem"
        elif diferencia > 0:
            bg = "#FFF0F0"; border = "#FFCCCC"; text = "#CC0000" 
            estado = f"Sobran {diferencia} persona(s)"
            msg_dinero = f"🔴 Fuga:<br>-\\$ {costo_dif:,.2f} /sem"
        else:
            bg = "#F0FFF0"; border = "#CCFFCC"; text = "#008000" 
            estado = "Plantilla Perfecta"
            msg_dinero = f"🟢 Balance:<br>\\$ 0.00"
        
        return f"""
        <div style="background-color: {bg}; border: 1px solid {border}; border-radius: 10px; padding: 15px; min-height: 160px; display: flex; flex-direction: column; justify-content: center; margin-bottom: 15px; box-sizing: border-box;">
            <h4 style="margin: 0 0 10px 0; color: #333; font-size: 17px; line-height: 1.2;">{icono} {puesto}</h4>
            <p style="margin: 0 0 5px 0; font-size: 14px; color: #333; line-height: 1.2;"><b>{estado}</b></p>
            <p style="margin: 0 0 10px 0; font-size: 12px; color: #666; line-height: 1.2;">(Ideal: {necesitas} | Tienes: {tienes})</p>
            <h5 style="margin: 0; color: {text}; font-size: 16px; line-height: 1.4;">{msg_dinero}</h5>
        </div>
        """

    puestos_nombres = list(ideal.keys())
    for i in range(0, len(puestos_nombres), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(puestos_nombres):
                puesto = puestos_nombres[i + j]
                dif = real[puesto] - ideal[puesto]
                costo_dif = abs(dif) * salarios_map[puesto] * 7
                with cols[j]:
                    st.markdown(crear_tarjeta(puesto, ideal[puesto], real[puesto], dif, costo_dif), unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 📊 Comparativo Gráfico")
    nombres_con_icono = [f"{iconos_puestos[p]} {p}" for p in ideal.keys()]
    df_rh = pd.DataFrame({
        'Puesto': nombres_con_icono * 2,
        'Empleados': list(ideal.values()) + list(real.values()),
        'Tipo': ['1. Plantilla IDEAL (Requerida)']*8 + ['2. Plantilla REAL (Contratada)']*8
    })
    fig_rh = px.bar(df_rh, x='Puesto', y='Empleados', color='Tipo', barmode='group', text_auto=True, color_discrete_map={'1. Plantilla IDEAL (Requerida)': '#1f77b4', '2. Plantilla REAL (Contratada)': '#ff7f0e'})
    fig_rh.update_layout(legend_title=None, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig_rh, use_container_width=True)

# ==========================================
# 🚀 EJECUCIÓN PRINCIPAL: ¿MODO NORMAL O MODO IMPRESIÓN PDF?
# ==========================================
if modo_impresion:
    # --- MODO DE EXPORTACIÓN A PDF (TODO APILADO) ---
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>📄 REPORTE EJECUTIVO SIMPLEX</h1>", unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("## 📅 1. Resumen Diario")
    render_tab_diario()
    
    st.markdown("<br><br><br>", unsafe_allow_html=True) 
    st.markdown("## 📊 2. Gran Resumen Semanal")
    render_tab_semanal()
    
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    st.markdown("## ⚖️ 3. Análisis de Recursos Humanos y Finanzas")
    render_tab_ideal()

else:
    # --- MODO INTERACTIVO NORMAL CON PESTAÑAS (CORREGIDO) ---
    tab_carga, tab_diario, tab_semanal, tab_ideal = st.tabs([
        "📥 1. CARGA DE DATOS", 
        "📅 2. RESUMEN DIARIO", 
        "📊 3. GRAN RESUMEN SEMANAL",
        "⚖️ 4. PLANTILLA IDEAL VS REAL"
    ])
    
    with tab_carga:
        render_tab_carga()
    with tab_diario:
        render_tab_diario()
    with tab_semanal:
        render_tab_semanal()
    with tab_ideal:
        render_tab_ideal()