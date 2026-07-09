import pandas as pd
import gradio as gr

# 1. LEER EL CSV LOCAL (Solo lectura)
ARCHIVO_CSV = "marvel_rivals_52.csv"
try:
    df_rivals = pd.read_csv(ARCHIVO_CSV)
except FileNotFoundError:
    print(f"❌ Error: No se encontró el archivo '{ARCHIVO_CSV}'.")
    exit()

# Listas base con los personajes limpios
DUELIST_BASE = sorted(df_rivals[df_rivals["Rol"] == "Duelist"]["Personaje"].dropna().tolist())
VANGUARD_BASE = sorted(df_rivals[df_rivals["Rol"] == "Vanguard"]["Personaje"].dropna().tolist())
STRATEGIST_BASE = sorted(df_rivals[df_rivals["Rol"] == "Strategist"]["Personaje"].dropna().tolist())

# Deadpool comodín en las listas base
if "Deadpool" not in VANGUARD_BASE: VANGUARD_BASE.append("Deadpool")
if "Deadpool" not in STRATEGIST_BASE: STRATEGIST_BASE.append("Deadpool")
VANGUARD_BASE.sort()
STRATEGIST_BASE.sort()

# Mapeos de consulta rápida
ROLES_MAP = dict(zip(df_rivals["Personaje"], df_rivals["Rol"]))
TEAMUP1_MAP = dict(zip(df_rivals["Personaje"], df_rivals["Team_Up_1"]))
TEAMUP2_MAP = dict(zip(df_rivals["Personaje"], df_rivals["Team_Up_2"]))
ROLES_MAP["Deadpool"] = "Duelist"  

def analizar_composicion(d1, d2, v1, v2, s1, s2):
    seleccionados = [p for p in [d1, d2, v1, v2, s1, s2] if p and p != ""]
    
    if not seleccionados:
        return "<p style='color: gray;'>Completa al menos un slot para ver el mapa completo de sinergias.</p>"

    # 1. IDENTIFICAR TEAM-UPS ACTIVOS
    teamups_activos = {"Duelist": [], "Vanguard": [], "Strategist": []}
    categorias = {"Duelist": [d1, d2], "Vanguard": [v1, v2], "Strategist": [s1, s2]}
    
    for rol_seccion, heroes in categorias.items():
        for p in heroes:
            if not p or p == "": continue
            t1 = TEAMUP1_MAP.get(p)
            t2 = TEAMUP2_MAP.get(p)
            
            if (t1 and t1 in seleccionados) or (t2 and t2 in seleccionados):
                aliados_en_equipo = [a for a in [t1, t2] if a in seleccionados]
                socios_str = " & ".join(aliados_en_equipo)
                teamups_activos[rol_seccion].append(f"<li><b>{p}</b> ➔ Activo por <b>{socios_str}</b></li>")

    # 2. ANÁLISIS GLOBAL: RECOMENDACIONES BIDIRECCIONALES
    pendientes_recibe = {"Duelist": set(), "Vanguard": set(), "Strategist": set()}
    pendientes_otorga = {"Duelist": set(), "Vanguard": set(), "Strategist": set()}

    for p in seleccionados:
        t1 = TEAMUP1_MAP.get(p)
        t2 = TEAMUP2_MAP.get(p)
        for compañero in [t1, t2]:
            if compañero and compañero not in seleccionados:
                rol_comp = ROLES_MAP.get(compañero, "Desconocido")
                if rol_comp in pendientes_recibe:
                    pendientes_recibe[rol_comp].add((compañero, p))

        quienes_lo_necesitan = df_rivals[
            (df_rivals["Team_Up_1"] == p) | (df_rivals["Team_Up_2"] == p)
        ]["Personaje"].tolist()
        
        for cazador in quienes_lo_necesitan:
            if cazador not in seleccionados:
                rol_cazador = ROLES_MAP.get(cazador, "Desconocido")
                if rol_cazador in pendientes_otorga:
                    pendientes_otorga[rol_cazador].add((cazador, p))

    # --- CONSTRUCCIÓN DEL HTML ---
    html_salida = ""
    html_salida += "<h2>🔥 Sinergias Activas en el Equipo</h2>"
    for rol in ["Duelist", "Vanguard", "Strategist"]:
        html_salida += f"<h4>⚔️ Sección {rol}</h4>"
        if teamups_activos[rol]:
            html_salida += "<ul>" + "".join(teamups_activos[rol]) + "</ul>"
        else:
            html_salida += "<p style='color: gray; font-style: italic; margin-left: 20px;'>Sin sinergias activas en esta sección.</p>"
            
    html_salida += "<hr style='border: 1px solid #ccc; margin: 20px 0;'>"
    html_salida += "<h2>💡 Opciones Disponibles para Slots Vacíos</h2>"
    
    for rol in ["Duelist", "Vanguard", "Strategist"]:
        html_salida += f"<h3>➕ Candidatos para el Rol: {rol.upper()}</h3>"
        lineas_rol = []
        for comp, dueño in sorted(pendientes_recibe[rol]):
            lineas_rol.append(f"<li>Agregar a <b>{comp}</b> ➔ <i>(<b>{dueño}</b> consigue team up)</i></li>")
        for cazador, dueño in sorted(pendientes_otorga[rol]):
            lineas_rol.append(f"<li>Agregar a <b>{cazador}</b> ➔ <i>(Obtiene team up gracias a <b>{dueño}</b>)</i></li>")
            
        if lineas_rol:
            html_salida += "<ul>" + "".join(lineas_rol) + "</ul>"
        else:
            html_salida += "<p style='color: gray; font-style: italic; margin-left: 20px;'>No hay combinaciones detectadas para este rol.</p>"

    return html_salida

# --- FUNCIÓN DE FILTRADO DINÁMICO CORREGIDA DE RAÍZ ---
def actualizar_disponibles(d1, d2, v1, v2, s1, s2):
    # Identificar todos los seleccionados en el momento
    ocupados = {p for p in [d1, d2, v1, v2, s1, s2] if p and p != ""}
    
    # Cada dropdown filtra basándose en lo que está ocupado globalmente,
    # pero PERMITE su propio valor actual para que no se rompa al redibujar.
    nuevos_d1 = [""] + [p for p in DUELIST_BASE if p not in ocupados or p == d1]
    nuevos_d2 = [""] + [p for p in DUELIST_BASE if p not in ocupados or p == d2]
    
    nuevos_v1 = [""] + [p for p in VANGUARD_BASE if p not in ocupados or p == v1]
    nuevos_v2 = [""] + [p for p in VANGUARD_BASE if p not in ocupados or p == v2]
    
    nuevos_s1 = [""] + [p for p in STRATEGIST_BASE if p not in ocupados or p == s1]
    nuevos_s2 = [""] + [p for p in STRATEGIST_BASE if p not in ocupados or p == s2]
    
    # Devolvemos cada lista asignada estrictamente a su slot individual
    return (
        gr.Dropdown(choices=nuevos_d1, value=d1),
        gr.Dropdown(choices=nuevos_d2, value=d2),
        gr.Dropdown(choices=nuevos_v1, value=v1),
        gr.Dropdown(choices=nuevos_v2, value=v2),
        gr.Dropdown(choices=nuevos_s1, value=s1),
        gr.Dropdown(choices=nuevos_s2, value=s2)
    )

# --- INTERFAZ WEB ---
with gr.Blocks(title="Marvel Rivals Team-Up") as app:
    gr.Markdown("# 🎮 Marvel Rivals Team-Up Dashboard")
    gr.Markdown("Estructura tu equipo. Los personajes seleccionados se removerán de las otras casillas dinámicamente.")
    
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### 🔴 SECCIÓN: DUELISTS (DPS)")
            with gr.Row():
                d1 = gr.Dropdown(choices=[""] + DUELIST_BASE, label="Slot 1", value="", interactive=True)
                d2 = gr.Dropdown(choices=[""] + DUELIST_BASE, label="Slot 2", value="", interactive=True)
                
            gr.Markdown("### 🔵 SECCIÓN: VANGUARDS (TANKS)")
            with gr.Row():
                v1 = gr.Dropdown(choices=[""] + VANGUARD_BASE, label="Slot 1", value="", interactive=True)
                v2 = gr.Dropdown(choices=[""] + VANGUARD_BASE, label="Slot 2", value="", interactive=True)
                
            gr.Markdown("### 🟢 SECCIÓN: STRATEGISTS (HEALERS)")
            with gr.Row():
                s1 = gr.Dropdown(choices=[""] + STRATEGIST_BASE, label="Slot 1", value="", interactive=True)
                s2 = gr.Dropdown(choices=[""] + STRATEGIST_BASE, label="Slot 2", value="", interactive=True)
                
            btn_calcular = gr.Button("⚙️ Analizar Conexiones Completas", variant="primary")
            
        with gr.Column(scale=1):
            salida_panel = gr.HTML(value="<p style='color: gray;'>Selecciona personajes y presiona Analizar.</p>")

    todos_los_inputs = [d1, d2, v1, v2, s1, s2]

    # Eventos de cambio cruzados con el filtro por rol corregido
    for componente in todos_los_inputs:
        componente.change(
            fn=actualizar_disponibles,
            inputs=todos_los_inputs,
            outputs=todos_los_inputs
        )

    # Botón ejecutor
    btn_calcular.click(
        fn=analizar_composicion,
        inputs=todos_los_inputs,
        outputs=[salida_panel]
    )

if __name__ == "__main__":
    app.launch(inbrowser=True)