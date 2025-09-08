import pandas as pd
import numpy as np
import requests
from geopy.distance import geodesic

# Charger un fichier Excel et convertir les coordonnées
def load_excel(file_path):
    df = pd.read_excel(file_path)
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        df['Latitude'] = df['Latitude'].astype(str).str.replace(',', '.').astype(float)
        df['Longitude'] = df['Longitude'].astype(str).str.replace(',', '.').astype(float)
    df = df.dropna(subset=['Latitude', 'Longitude'])
    return df

# Récupérer les bâtiments dans un rayon donné autour d'un point
def get_buildings(lat, lon, radius=500):
    url = f"https://overpass.kumi.systems/api/interpreter?data=[out:json];(way(around:{radius},{lat},{lon})[building];);out center;"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        buildings = [(el["center"]["lat"], el["center"]["lon"]) for el in data.get("elements", []) if "center" in el]
        
        print(f"🔹 {len(buildings)} bâtiments détectés autour de ({lat}, {lon})")
        return buildings
    except Exception as e:
        print(f"Erreur avec Overpass API : {e}")
        return []

# Vérifier si un bâtiment bloque la ligne de visée
def is_building_blocking(emitter, receiver, building):
    lat_min, lat_max = sorted([emitter[0], receiver[0]])
    lon_min, lon_max = sorted([emitter[1], receiver[1]])
    
    # Vérification stricte avec une interpolation linéaire
    if lat_min <= building[0] <= lat_max and lon_min <= building[1] <= lon_max:
        return True
    return False

# Calculer les distances et Nb
def calculate_distances(emitter, receiver, buildings):
    B = geodesic(emitter, receiver).meters
    blocking_buildings = [b for b in buildings if is_building_blocking(emitter, receiver, b)]
    
    if blocking_buildings:
        first_building = min(blocking_buildings, key=lambda b: geodesic(emitter, b).meters)
        D = geodesic(emitter, first_building).meters
    else:
        D = B
    
    print(f"➡ Nb: {len(blocking_buildings)}, D: {D:.2f}m, B: {B:.2f}m")
    return len(blocking_buildings), D, B

# Charger les fichiers
emitters = load_excel("C:/Users/Andi/OneDrive/Desktop/combi/émetteur (1).xlsx")
receivers = load_excel("C:/Users/Andi/OneDrive/Desktop/combi/récepteur (1).xlsx")

results = []

for _, recv in receivers.iterrows():
    recv_coords = (recv['Latitude'], recv['Longitude'])
    
    if emitters.empty:
        print(f"⚠ Aucun émetteur trouvé pour le récepteur {recv_coords}")
        continue
    
    nearest_emitter = min(emitters.itertuples(index=False), key=lambda e: geodesic(recv_coords, (e.Latitude, e.Longitude)).meters)
    emitter_coords = (nearest_emitter.Latitude, nearest_emitter.Longitude)
    
    buildings = get_buildings(*emitter_coords, radius=1000)
    Nb, D, B = calculate_distances(emitter_coords, recv_coords, buildings)
    
    results.append({
        "lat_emission": nearest_emitter.Latitude,
        "lon_emission": nearest_emitter.Longitude,
        "lat_reception": recv['Latitude'],
        "lon_reception": recv['Longitude'],
        "Nb": Nb,
        "D": D,
        "B": B
    })

# Sauvegarde
df_results = pd.DataFrame(results)
df_results.to_excel("C:/Users/Andi/OneDrive/Desktop/combi/hauteurmax.xlsx", index=False)
print("Calcul terminé. Résultats enregistrés dans hauteurmax.xlsx")