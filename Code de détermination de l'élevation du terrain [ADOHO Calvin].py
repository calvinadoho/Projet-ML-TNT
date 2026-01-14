import requests
import geopandas as gpd
import folium
from shapely.geometry import Polygon, LineString
import pandas as pd
from geopy.distance import geodesic

# Fonction pour interroger Open-Elevation API et récupérer l'altitude
def get_altitude_from_open_elevation(lat, lon):
    open_elevation_url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
    
    response = requests.get(open_elevation_url)
    
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            return data['results'][0]['elevation']  # Altitude en mètres
        else:
            return None
    else:
        print("Erreur Open-Elevation API:", response.status_code)
        return None

# Fonction pour interroger Overpass API et récupérer les obstacles avec hauteur
def get_osm_obstacles(lat, lon, radius=500):
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    query = f"""
    [out:json];
    (
      way["building"](around:{radius},{lat},{lon});
      way["natural"="wood"](around:{radius},{lat},{lon});
      way["landuse"="forest"](around:{radius},{lat},{lon});
    );
    out body;
    >;
    out skel qt;
    """
    
    response = requests.get(overpass_url, params={'data': query})
    
    if response.status_code == 200:
        return response.json()
    else:
        print("Erreur API:", response.status_code)
        return None

# Fonction pour extraire les obstacles sous forme de polygones avec hauteur et autres informations
def parse_osm_data(osm_data, antenna_coords, reception_coords):
    nodes = {}
    features = []
    
    for element in osm_data["elements"]:
        if element["type"] == "node":
            nodes[element["id"]] = (element["lat"], element["lon"])
    
    for element in osm_data["elements"]:
        if element["type"] == "way":
            coords = [nodes[node_id] for node_id in element["nodes"] if node_id in nodes]
            if len(coords) > 2:
                polygon = Polygon(coords)
                
                # Récupération de la hauteur via Open-Elevation
                avg_lat = sum([coord[0] for coord in coords]) / len(coords)
                avg_lon = sum([coord[1] for coord in coords]) / len(coords)
                height = get_altitude_from_open_elevation(avg_lat, avg_lon)
                
                # Récupération de la distance par rapport à l'antenne et au récepteur
                dist_antenna = geodesic((avg_lat, avg_lon), antenna_coords).meters
                dist_reception = geodesic((avg_lat, avg_lon), (reception_coords[0] + 10, reception_coords[1])).meters
                
                # Récupérer le type de surface et la forme
                surface_type = element["tags"].get("surface", "Non spécifié")
                building_type = element["tags"].get("building", "Non spécifié")
                
                # Ajouter les informations dans la liste des obstacles
                features.append({
                    "type": "Obstacle",
                    "geometry": polygon,
                    "height": height,
                    "coordinates": (avg_lat, avg_lon),
                    "surface": surface_type,
                    "building_type": building_type,
                    "distance_to_antenna": dist_antenna,
                    "distance_to_reception": dist_reception
                })
    
    return gpd.GeoDataFrame(features, geometry="geometry")

# Fonction pour filtrer les obstacles qui croisent la ligne de visée
def filter_obstacles_between(antenna, reception, obstacles_gdf):
    line_of_sight = LineString([antenna, reception])  # Ligne droite entre l'antenne et le point de réception
    filtered_obstacles = obstacles_gdf[obstacles_gdf.intersects(line_of_sight)]  # On garde ceux qui croisent la ligne
    return filtered_obstacles

# Fonction pour visualiser les obstacles filtrés avec des symboles explicatifs
def visualize_filtered_obstacles(antenna, reception, obstacles_gdf):
    m = folium.Map(location=[(antenna[0] + reception[0]) / 2, (antenna[1] + reception[1]) / 2], zoom_start=15)

    # Ajouter les points de l’antenne et du récepteur
    folium.Marker(antenna, popup="Antenne TNT", icon=folium.Icon(color="red")).add_to(m)
    folium.Marker(reception, popup="Point de Réception", icon=folium.Icon(color="green")).add_to(m)

    # Ajouter la ligne de visée
    folium.PolyLine([antenna, reception], color="black", weight=2.5, opacity=1).add_to(m)

    # Ajouter les obstacles avec symboles et informations
    for _, row in obstacles_gdf.iterrows():
        height_info = f"Hauteur : {row['height']}m" if row["height"] else "Hauteur inconnue"
        type_info = f"Type : {row['building_type']}"  # Ajouter le type d'obstacle
        surface_info = f"Surface : {row['surface']}"  # Ajouter le type de surface
        dist_antenna_info = f"Distance antenne : {row['distance_to_antenna']}m"
        dist_reception_info = f"Distance réception : {row['distance_to_reception']}m"
        
        # Déterminer l'icône en fonction de la hauteur
        icon_color = "blue"  # Couleur par défaut
        icon_icon = "info-sign"  # Icône par défaut
        if row['height'] is not None:
            if row['height'] < 5:
                icon_color = "green"
            elif row['height'] < 10:
                icon_color = "orange"
            else:
                icon_color = "red"
                icon_icon = "exclamation-sign"  # Icône différente pour les obstacles très hauts

        # Utiliser un cercle pour représenter les obstacles
        folium.CircleMarker(
            location=[row['geometry'].centroid.y, row['geometry'].centroid.x],  # Centrer sur le polygone
            radius=10,
            color=icon_color,
            fill=True,
            fill_opacity=0.6,
            popup=f"{height_info}\n{type_info}\n{surface_info}\n{dist_antenna_info}\n{dist_reception_info}"
        ).add_to(m)

    return m

# 📌 Exemple avec une antenne et un point de réception
antenna_coords = (11.123456, 2.954658)  # 📡 Coordonnées de l’antenne TNT
reception_coords = (11.12129, 2.92991)  # 📍 Coordonnées du point de réception

osm_data = get_osm_obstacles(*reception_coords)  # Récupérer obstacles autour du point de réception
if osm_data:
    obstacles_gdf = parse_osm_data(osm_data, antenna_coords, reception_coords)
    
    # Vérifier si des obstacles ont été trouvés
    if obstacles_gdf.empty:
        print("Aucun obstacle trouvé.")
    else:
        print(f"{len(obstacles_gdf)} obstacles trouvés.")

    # Filtrer uniquement les obstacles entre l'antenne et le point de réception
    filtered_obstacles = filter_obstacles_between(antenna_coords, reception_coords, obstacles_gdf)
    
    # Afficher la carte avec les obstacles filtrés et leur hauteur
    map_filtered_obstacles = visualize_filtered_obstacles(antenna_coords, reception_coords, filtered_obstacles)
    map_filtered_obstacles.save("c:/Users/pc/Documents/TIFF/OSM_explicit.html")
    print("Carte explicative enregistrée sous 'OSM_explicit.html'. Ouvrez ce fichier dans un navigateur.")

    # Sauvegarder les données dans un fichier Excel
    obstacles_gdf['height'] = obstacles_gdf['height'].fillna('Inconnue')
    obstacles_gdf['surface'] = obstacles_gdf['surface'].fillna('Non spécifié')
    obstacles_gdf['building_type'] = obstacles_gdf['building_type'].fillna('Non spécifié')

    # Créer le tableau pour Excel
    table_data = obstacles_gdf[['height', 'coordinates', 'surface', 'building_type', 'distance_to_antenna', 'distance_to_reception']].copy()
    table_data['coordinates'] = table_data['coordinates'].apply(lambda x: f"{x[0]}, {x[1]}")  # Convertir les coordonnées en chaîne de caractères

    # Sauvegarder sous format Excel
    table_data.to_excel("c:/Users/pc/Documents/TIFF/obstacles_data.xlsx", index=False)
    print("Données des obstacles enregistrées dans 'obstacles_data.xlsx'.")
