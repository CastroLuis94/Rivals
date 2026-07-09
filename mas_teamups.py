import pandas as pd

def analizar_team_ups(csv_path):
    try:
        # Cargar el archivo CSV
        df = pd.read_csv(csv_path)
        
        # Normalizar 'Star-Lord' a 'Star Lord' en las columnas de Team_Up por consistencia
        for col in ['Team_Up_1', 'Team_Up_2']:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip().replace('Star-Lord', 'Star Lord')
        
        # Contar apariciones en cada columna (remover valores nulos o vacíos)
        counts_1 = df['Team_Up_1'].value_counts()
        counts_2 = df['Team_Up_2'].value_counts()
        
        # Sumar ambos conteos alineando los personajes
        total_counts = counts_1.add(counts_2, fill_value=0).astype(int)
        
        # Filtrar valores basura que puedan venir de filas vacías (como 'nan' o 'None')
        valores_basura = ['nan', 'none', '', 'nan ']
        total_counts = total_counts.drop(labels=[x for x in valores_basura if x in total_counts.index], errors='ignore')
        
        # Ordenar de mayor a menor
        total_counts = total_counts.sort_values(ascending=False)
        
        # Imprimir resultados en consola
        print("\n🏆 RANKING DE PERSONAJES CON MÁS APARICIONES EN TEAM-UPS 🏆")
        print("=" * 60)
        for rank, (personaje, apariciones) in enumerate(total_counts.items(), 1):
            print(f"{rank:>2}. {personaje:<25} -> {apariciones} apariciones")
            
    except KeyError:
        print("❌ Error: Asegúrate de que el CSV tenga las columnas 'Team_Up_1' y 'Team_Up_2'.")
    except FileNotFoundError:
        print(f"❌ Error: No se encontró el archivo en la ruta '{csv_path}'.")

# Ejecutar el script (cambiá el nombre si tu archivo se llama distinto)
if __name__ == "__main__":
    analizar_team_ups("marvel_rivals_52.csv")