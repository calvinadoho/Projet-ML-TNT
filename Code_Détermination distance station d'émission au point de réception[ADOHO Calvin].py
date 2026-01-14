import pandas as pd
import numpy as np
import folium
from math import radians, sin, cos, sqrt, atan2
import os

def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Rayon de la Terre en km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # Distance en km

def calculer_distances_et_afficher_carte(fichier_excel):
    # Vérifier si le fichier existe
    if not os.path.exists(fichier_excel):
        raise FileNotFoundError(f"Le fichier {fichier_excel} n'existe pas.")

    # Charger les données
    df = pd.read_excel(fichier_excel)
    
    # Vérifier les colonnes requises
    colonnes_requises = ["Lat_Pyl", "Long_Pyl", "Lat", "Long"]
    if not all(col in df.columns for col in colonnes_requises):
        raise ValueError(f"Les colonnes requises {colonnes_requises} sont absentes du fichier.")

    # Séparer pylônes et points
    df_pylones = df.dropna(subset=["Lat_Pyl", "Long_Pyl"])
    df_points = df.dropna(subset=["Lat", "Long"])
    
    # Vérifier s'il y a au moins un pylône
    if df_pylones.empty:
        raise ValueError("Aucune donnée de pylône détectée dans le fichier.")

    # Fonction pour trouver le pylône le plus proche
    def trouver_pylone_proche(row):
        lat_p, lon_p = row["Lat"], row["Long"]
        distances = [haversine(lat_p, lon_p, lat_t, lon_t) for lat_t, lon_t in zip(df_pylones["Lat_Pyl"], df_pylones["Long_Pyl"])]
        index_min = np.argmin(distances)
        return distances[index_min], df_pylones.iloc[index_min]["Lat_Pyl"], df_pylones.iloc[index_min]["Long_Pyl"]

    # Appliquer la fonction à chaque point
    resultats = df_points.apply(trouver_pylone_proche, axis=1, result_type="expand")
    df_points[["Distance_km", "Lat_Pyl_Proche", "Long_Pyl_Proche"]] = resultats
    
    # Sauvegarder les résultats
    output_file = fichier_excel.replace(".xlsx", "_distances.xlsx")
    df_points.to_excel(output_file, index=False)
    print(f"Fichier enregistré : {output_file}")

    # Générer la carte Folium
    carte = folium.Map(location=[df_points["Lat"].mean(), df_points["Long"].mean()], zoom_start=12)

    # Ajouter les pylônes (en rouge)
    for _, pylone in df_pylones.iterrows():
        folium.Marker(
            location=[pylone["Lat_Pyl"], pylone["Long_Pyl"]],
            icon=folium.Icon(color="red", icon="cloud"),
            popup=f"Pylône ({pylone['Lat_Pyl']}, {pylone['Long_Pyl']})"
        ).add_to(carte)

    # Ajouter les points de réception (en bleu) et tracer les lignes vers leur pylône le plus proche
    for _, point in df_points.iterrows():
        folium.Marker(
            location=[point["Lat"], point["Long"]],
            icon=folium.Icon(color="blue", icon="info-sign"),
            popup=f"Point ({point['Lat']}, {point['Long']})\nDistance: {point['Distance_km']:.2f} km"
        ).add_to(carte)

        # Ajouter une ligne entre le point et le pylône le plus proche
        folium.PolyLine(
            locations=[(point["Lat"], point["Long"]), (point["Lat_Pyl_Proche"], point["Long_Pyl_Proche"])],
            color="green",
            weight=2.5,
            opacity=0.7
        ).add_to(carte)

    # Sauvegarder la carte en HTML
    map_file = fichier_excel.replace(".xlsx", "_carte.html")
    carte.save(map_file)
    print(f"Carte enregistrée : {map_file}")

    return output_file, map_file

# Exemple d'utilisation
fichier_excel = "c:/Users/pc/Documents/TIFF/data_kandi_with_altitude.xlsx"
calculer_distances_et_afficher_carte(fichier_excel)
