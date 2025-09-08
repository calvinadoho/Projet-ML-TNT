import pandas as pd
import requests

# API Open-Elevation
OPEN_ELEVATION_URL = "https://api.open-elevation.com/api/v1/lookup"

# Charger le fichier Excel
def load_excel(file_path):
    df = pd.read_excel(file_path)
    return df

# Récupérer l'altitude via l'API Open-Elevation
def get_altitude(lat, lon):
    response = requests.get(OPEN_ELEVATION_URL, params={"locations": f"{lat},{lon}"})
    if response.status_code == 200:
        data = response.json()
        return data["results"][0]["elevation"]
    else:
        print(f"Erreur lors de la récupération de l'altitude pour ({lat}, {lon})")
        return None

# Mettre à jour le fichier Excel avec l'altitude
def update_excel_with_altitude(file_path):
    df = load_excel(file_path)

    # Vérifier si les colonnes nécessaires existent
    required_columns = ["Latitude", "Longitude"]
    if not all(col in df.columns for col in required_columns):
        print("Les colonnes Latitude et Longitude sont requises dans le fichier Excel.")
        return
    
    # Calcul de l'altitude pour chaque point
    df["Altitude"] = df.apply(lambda row: get_altitude(row["Latitude"], row["Longitude"]), axis=1)

    # Sauvegarde du fichier Excel mis à jour
    output_file = file_path.replace(".xlsx", "_altitude.xlsx")
    df.to_excel(output_file, index=False)
    print(f"Fichier mis à jour avec l'altitude enregistré sous : {output_file}")

# Exemple d'utilisation
file_path = "C:/Users/pc/Documents/TIFF/récepteur.xlsx"  # Remplacez par le chemin réel de votre fichier Excel
update_excel_with_altitude(file_path)
