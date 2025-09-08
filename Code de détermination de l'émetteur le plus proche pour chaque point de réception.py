import pandas as pd
import requests
import math
import os
from geopy.distance import geodesic

# Configuration de l'API Google Maps
API_KEY = "AIzaSyCwzw4HN5lG5Rp-fY_lgys4zAO27yL8Fog"
BASE_URL = "https://maps.googleapis.com/maps/api/staticmap"

# Charger les fichiers Excel
def load_excel(file_path):
    df = pd.read_excel(file_path)
    # Remplacer les virgules par des points et convertir en float
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        df['Latitude'] = df['Latitude'].astype(str).str.replace(',', '.').astype(float)
        df['Longitude'] = df['Longitude'].astype(str).str.replace(',', '.').astype(float)
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        df['Latitude'] = df['Latitude'].astype(str).str.replace(',', '.').astype(float)
        df['Longitude'] = df['Longitude'].astype(str).str.replace(',', '.').astype(float)
    return df

# Calcul de la distance entre deux points (haversine)
def find_nearest_emitter(receivers, emitters):
    mapping = []
    for _, recv in receivers.iterrows():
        recv_coords = (recv['Latitude'], recv['Longitude'])
        nearest_emitter = min(emitters.iterrows(), key=lambda e: geodesic(recv_coords, (e[1]['Latitude'], e[1]['Longitude'])).meters)
        mapping.append({
            "Latitude": recv['Latitude'],
            "Longitude": recv['Longitude'],
            "ID_Emetteur_Associe": nearest_emitter[1]['Code'],
            "Nearest_Emitter_Latitude": nearest_emitter[1]['Latitude'],
            "Nearest_Emitter_Longitude": nearest_emitter[1]['Longitude']
        })
    return pd.DataFrame(mapping)


# Pipeline principale
def process_maps(emitter_file, receiver_file, output_dir="output"):
    os.makedirs(output_dir, exist_ok=True)
    emitters = load_excel(emitter_file)
    receivers = load_excel(receiver_file)
    nearest_df = find_nearest_emitter(receivers, emitters)
    updated_receivers = receivers.merge(nearest_df, on=["Latitude", "Longitude"], how="left")
    updated_receivers.to_excel("C:/Users/pc/Documents/TIFF/recepteur.xlsx", index=False)
    

# Exemple d'utilisation
process_maps("C:/Users/pc/Documents/TIFF/émetteur.xlsx", "C:/Users/pc/Documents/TIFF/récepteur.xlsx")
