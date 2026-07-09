import csv
from itertools import combinations

def cargar_datos(filepath):
    personajes = {}
    with open(filepath, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            p = row['Personaje'].strip()
            if not p:
                continue
            
            if p == "Star-Lord": p = "Star Lord"
            
            t1 = row.get('Team_Up_1', '').strip()
            t2 = row.get('Team_Up_2', '').strip()
            if t1 == "Star-Lord": t1 = "Star Lord"
            if t2 == "Star-Lord": t2 = "Star Lord"
            
            personajes[p] = {
                'Rol': row['Rol'].strip(),
                'Team_Up_1': t1 if t1 else None,
                'Team_Up_2': t2 if t2 else None
            }
    return personajes

def calcular_team_ups(combo, datos):
    nombres_equipo = set(combo)
    total_team_ups = 0
    detalles_sinergias = []

    for p in combo:
        t1 = datos[p]['Team_Up_1']
        t2 = datos[p]['Team_Up_2']
        
        if (t1 and t1 in nombres_equipo) or (t2 and t2 in nombres_equipo):
            total_team_ups += 1
            aliados = [a for a in [t1, t2] if a in nombres_equipo]
            detalles_sinergias.append(f"{p} (➔ {', '.join(aliados)})")
            
    return total_team_ups, detalles_sinergias

def buscar_mejores_equipos(datos, top_n=30):
    pool_personajes = list(datos.keys())
    mejores_combos = []

    print("Calculando combinaciones óptimas considerando la flexibilidad de Deadpool...")
    
    for combo in combinations(pool_personajes, 6):
        # Contamos la base sin contar a Deadpool temporalmente si está en el combo
        tiene_deadpool = "Deadpool" in combo
        
        d_count = sum(1 for p in combo if p != "Deadpool" and datos[p]['Rol'] == 'Duelist')
        v_count = sum(1 for p in combo if p != "Deadpool" and datos[p]['Rol'] == 'Vanguard')
        s_count = sum(1 for p in combo if p != "Deadpool" and datos[p]['Rol'] == 'Strategist')
        
        deadpool_rol_asignado = None
        
        # LÓGICA COMODÍN: Asignar a Deadpool al rol donde más rinda estructuralmente
        if tiene_deadpool:
            if s_count < 2:
                # Prioridad 1: Si faltan healers para el mínimo legal de la búsqueda, va como Strategist
                s_count += 1
                deadpool_rol_asignado = 'Strategist'
            elif d_count == 1 and v_count == 2 and s_count == 2:
                # Prioridad 2: Si completa un 2-2-2 metiéndose como Duelist
                d_count += 1
                deadpool_rol_asignado = 'Duelist'
            elif d_count == 2 and v_count == 1 and s_count == 2:
                # Prioridad 3: Si completa un 2-2-2 metiéndose como Vanguard
                v_count += 1
                deadpool_rol_asignado = 'Vanguard'
            else:
                # Fallback: Default a su rol principal listado (Duelist) si no altera el meta-score
                d_count += 1
                deadpool_rol_assigned_base = datos["Deadpool"]['Rol']
                deadpool_rol_asignado = deadpool_rol_assigned_base if deadpool_rol_assigned_base else 'Duelist'
        
        # Filtro obligatorio: Mínimo 2 healers
        if s_count < 2:
            continue
            
        score, sinergias = calcular_team_ups(combo, datos)
        es_222 = (d_count == 2 and v_count == 2 and s_count == 2)
        
        mejores_combos.append({
            'equipo': combo,
            'score': score,
            'es_222': es_222,
            'distribucion': f"{d_count}-{v_count}-{s_count}",
            'deadpool_rol': deadpool_rol_asignado,
            'sinergias': sinergias
        })
        
    # Doble sort: primero por score de teamups, después da prioridad a la estructura 2-2-2
    mejores_combos.sort(key=lambda x: (-x['score'], -int(x['es_222'])))
    
    return mejores_combos[:top_n]

def imprimir_resultados(top_equipos, datos, archivo_salida=None):
    import sys
    orig_stdout = sys.stdout
    
    if archivo_salida:
        f = open(archivo_salida, 'w', encoding='utf-8')
        sys.stdout = f

    print("\n" + "="*65)
    print(" 🏆 TOP 30 COMBOS MÁXIMO TEAM-UPS (CON DEADPOOL COMODÍN) 🏆 ")
    print("="*65)
    
    for idx, item in enumerate(top_equipos, 1):
        equipo = item['equipo']
        deadpool_rol = item['deadpool_rol']
        
        # Clasificar dinámicamente respetando dónde cayó Deadpool en este combo
        duelists = []
        vanguards = []
        strategists = []
        
        for p in equipo:
            if p == "Deadpool":
                if deadpool_rol == 'Duelist': duelists.append("Deadpool (Flex 🔴)")
                elif deadpool_rol == 'Vanguard': vanguards.append("Deadpool (Flex 🔵)")
                elif deadpool_rol == 'Strategist': strategists.append("Deadpool (Flex 🟢)")
            else:
                rol = datos[p]['Rol']
                if rol == 'Duelist': duelists.append(p)
                elif rol == 'Vanguard': vanguards.append(p)
                elif rol == 'Strategist': strategists.append(p)
        
        etiqueta_222 = "✨ [META 2-2-2]" if item['es_222'] else f"📊 [COMP: {item['distribucion']}]"
        
        print(f"\n🔥 [TOP {idx}] Sinergias Activas: {item['score']} | {etiqueta_222}")
        print(f"─" * 55)
        print(f" 🔴 DUELISTS ({len(duelists)}):    {', '.join(duelists) if duelists else 'Ninguno'}")
        print(f" 🔵 VANGUARDS ({len(vanguards)}):   {', '.join(vanguards) if vanguards else 'Ninguno'}")
        print(f" 🟢 STRATEGISTS ({len(strategists)}): {', '.join(strategists)}")
        print(f" 🧩 Héroes buffados: {', '.join(item['sinergias'])}")
        print(f"─" * 55)

    if archivo_salida:
        sys.stdout = orig_stdout
        f.close()
        print(f"✅ ¡Archivo '{archivo_salida}' generado con éxito usando UTF-8 nativo!")

if __name__ == "__main__":
    archivo_csv = "marvel_rivals_52.csv" 
    
    try:
        datos_rivals = cargar_datos(archivo_csv)
        top_30 = buscar_mejores_equipos(datos_rivals, top_n=30)
        imprimir_resultados(top_30, datos_rivals, archivo_salida="max_teamups.txt")
        
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo '{archivo_csv}'.")