import pandas as pd
import requests
import os
from io import BytesIO
from PIL import Image
from geopy.distance import geodesic

# Configuration de l'API Google Maps
API_KEY = "INSERT API_KEY"
BASE_URL = "https://maps.googleapis.com/maps/api/staticmap"

# Charger les fichiers Excel
def load_excel(file_path):
    df = pd.read_excel(file_path)
    
    # Remplacer les virgules par des points et convertir en float
    if 'Latitude' in df.columns and 'Longitude' in df.columns:
        df['Latitude'] = df['Latitude'].astype(str).str.replace(',', '.').astype(float)
        df['Longitude'] = df['Longitude'].astype(str).str.replace(',', '.').astype(float)
    if 'Lat' in df.columns and 'Long' in df.columns:
        df['Lat'] = df['Lat'].astype(str).str.replace(',', '.').astype(float)
        df['Long'] = df['Long'].astype(str).str.replace(',', '.').astype(float)
    return df


# Calcul de la distance entre deux points (haversine)
def find_nearest_emitter(receivers, emitters):
    mapping = []
    for _, recv in receivers.iterrows():
        recv_coords = (recv['Lat'], recv['Long'])
        nearest_emitter = min(emitters.iterrows(), key=lambda e: geodesic(recv_coords, (e[1]['Latitude'], e[1]['Longitude'])).meters)
        mapping.append({
            "Lat": recv['Lat'],
            "Long": recv['Long'],
            "Nearest_Emitter_Code": nearest_emitter[1]['Code'],
            "Nearest_Emitter_Latitude": nearest_emitter[1]['Latitude'],
            "Nearest_Emitter_Longitude": nearest_emitter[1]['Longitude']
        })
    return pd.DataFrame(mapping)

# Génération des images Google Maps
def get_google_maps_image(lat, lon, zoom=19, size=(640, 640)):
    params = {
        "center": f"{lat},{lon}",
        "zoom": zoom,
        "size": f"{size[0]}x{size[1]}",
        "key": API_KEY
    }
    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        return Image.open(BytesIO(response.content))  # Utilisation de BytesIO ici
    else:
        print(f"Erreur lors du téléchargement de l'image : {response.status_code}, {response.text}")
    return None


# Génération des images entre l'émetteur et le récepteur
def capture_path_images(start, end, step=0.0005):
    lat1, lon1 = start
    lat2, lon2 = end
    dx = (lat2 - lat1) * step
    dy = (lon2 - lon1) * step
    images = []
    lat, lon = lat1, lon1
    while abs(lat - lat2) > step or abs(lon - lon2) > step:
        img = get_google_maps_image(lat, lon)
        if img:
            images.append(img)
        lat += dx
        lon += dy
    return images

# Fusionner les images en une mosaïque
def create_mosaic(images):
    widths, heights = zip(*(i.size for i in images))
    total_width = sum(widths)
    max_height = max(heights)
    mosaic = Image.new('RGB', (total_width, max_height))
    x_offset = 0
    for img in images:
        mosaic.paste(img, (x_offset, 0))
        x_offset += img.width
    return mosaic

# Pipeline principale
def process_maps(emitter_file, receiver_file, output_dir="C:/Users/pc/Documents/TIFF/mosaique/"):
    os.makedirs(output_dir, exist_ok=True)
    
    # Charger les fichiers émetteurs et récepteurs
    emitters = load_excel(emitter_file)
    if emitters is None:
        return  # Quitter si les émetteurs ne sont pas valides
    
    receivers = load_excel(receiver_file)
    if receivers is None:
        return  # Quitter si les récepteurs ne sont pas valides
    
    # Trouver le récepteur le plus proche pour chaque émetteur
    nearest_df = find_nearest_emitter(receivers, emitters)
    
    # Mise à jour des récepteurs avec la référence de l'émetteur le plus proche
    updated_receivers = receivers.merge(nearest_df, on=["Lat", "Long"], how="left")
    updated_receivers.to_excel("C:/Users/pc/Documents/TIFF/database(csv)/updated_receivers.xlsx", index=False)
    
    for _, row in nearest_df.iterrows():
        # Utilisation des références pour capturer les images
        images = capture_path_images((row['Lat'], row['Long']), (row['Nearest_Emitter_Latitude'], row['Nearest_Emitter_Longitude']))
        if images:
            # Créer la mosaïque à partir des images capturées
            mosaic = create_mosaic(images)
            file_name = f"{output_dir}_cotonou.png"
            mosaic.save(file_name)
            print(f"Mosaïque enregistrée : {file_name}")

# Exemple d'utilisation
process_maps("C:/Users/pc/Documents/TIFF/database(csv)/TXBenin2_.xlsx", "C:/Users/pc/Documents/TIFF/database(csv)/merged_data_azimut.xlsx")

