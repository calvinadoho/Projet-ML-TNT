import requests
import pandas as pd
import rasterio
import numpy as np
import os

# Clé API OpenTopography (remplacez par votre clé)
API_KEY = '642099804d006a64b39b2d760ea7e1f6'

def download_strm_image(lat, lon, output_path):
    """
    Télécharge une image STRM pour une localisation GPS donnée en utilisant l'API OpenTopography.
    
    Args:
        lat (float): Latitude de la localisation.
        lon (float): Longitude de la localisation.
        output_path (str): Chemin où sauvegarder l'image STRM téléchargée.
    """
    # Définir les paramètres de la requête API
    url = "https://portal.opentopography.org/API/globaldem"
    params = {
        'demtype': 'SRTMGL3',  # Type de données STRM (SRTM Global 3 arc-second)
        'south': lat - 0.1,    # Limite sud de la zone
        'north': lat + 0.1,    # Limite nord de la zone
        'west': lon - 0.1,     # Limite ouest de la zone
        'east': lon + 0.1,     # Limite est de la zone
        'outputFormat': 'GTiff',  # Format de sortie (GeoTIFF)
        'API_Key': API_KEY      # Clé API
    }
    
    # Faire la requête à l'API
    response = requests.get(url, params=params)
    
    # Vérifier si la requête a réussi
    if response.status_code == 200:
        # Sauvegarder l'image STRM
        with open(output_path, 'wb') as f:
            f.write(response.content)
        print(f"Image STRM téléchargée avec succès : {output_path}")
    else:
        print(f"Erreur lors du téléchargement de l'image STRM : {response.status_code}")
        print(response.text)

def get_elevation(lat, lon, dataset):
    """
    Récupère l'élévation à partir des coordonnées GPS.
    
    Args:
        lat (float): Latitude de la localisation.
        lon (float): Longitude de la localisation.
        dataset (rasterio.DatasetReader): Dataset STRM ouvert avec rasterio.
    
    Returns:
        float: Élévation en mètres.
    """
    # Convertir les coordonnées GPS en indices de pixel
    py, px = dataset.index(lon, lat)
    # Lire l'élévation à ce point
    elevation = dataset.read(1, window=((py, py+1), (px, px+1)))
    return elevation[0][0]

def calculate_slope(dataset):
    """
    Calcule la pente à partir des données d'élévation.
    
    Args:
        dataset (rasterio.DatasetReader): Dataset STRM ouvert avec rasterio.
    
    Returns:
        numpy.ndarray: Pente en degrés.
    """
    # Calculer la pente à partir des données d'élévation
    elevation = dataset.read(1)
    x, y = np.gradient(elevation)
    slope = np.degrees(np.arctan(np.sqrt(x**2 + y**2)))  # Convertir en degrés
    return slope

def calculate_roughness(dataset):
    """
    Calcule la rugosité à partir des données d'élévation.
    
    Args:
        dataset (rasterio.DatasetReader): Dataset STRM ouvert avec rasterio.
    
    Returns:
        float: Rugosité en mètres.
    """
    # Calculer la rugosité à partir des données d'élévation
    elevation = dataset.read(1)
    roughness = np.std(elevation)
    return roughness

def main():
    # Lire le fichier Excel
    df = pd.read_excel('GPS.xlsx')
    
    # Créer une liste pour stocker les résultats
    results = []
    
    for index, row in df.iterrows():
        lat, lon = row['Latitude'], row['Longitude']
        output_path = f'strm_image_{index}.tif'
        
        # Télécharger l'image STRM
        download_strm_image(lat, lon, output_path)
        
        # Ouvrir l'image STRM téléchargée
        if os.path.exists(output_path):
            with rasterio.open(output_path) as dataset:
                elevation = get_elevation(lat, lon, dataset)
                slope = calculate_slope(dataset)
                roughness = calculate_roughness(dataset)
                
                # Ajouter les résultats à la liste
                results.append({
                    'Latitude': lat,
                    'Longitude': lon,
                    'Elevation (m)': elevation,
                    'Slope (degrees)': np.mean(slope),  # Moyenne de la pente
                    'Roughness (m)': roughness
                })
                
                # Afficher les résultats
                print(f"Location {index}: Latitude={lat}, Longitude={lon}")
                print(f"Elevation: {elevation} m")
                print(f"Slope: {np.mean(slope):.2f} degrees")
                print(f"Roughness: {roughness:.2f} m")
                print()
        else:
            print(f"Image STRM non trouvée pour la localisation {index}")
    
    # Créer un DataFrame à partir des résultats
    results_df = pd.DataFrame(results)
    
    # Sauvegarder les résultats dans un fichier Excel
    results_df.to_excel('results.xlsx', index=False)
    print("Résultats sauvegardés dans 'results.xlsx'")

if __name__ == "__main__":
    main()