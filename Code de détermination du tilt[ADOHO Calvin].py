import os
import numpy as np
import pandas as pd
from torchvision import models, transforms
from PIL import Image
import torch

# Define the path to the folder containing the PNG patches
patches_folder = 'C:/Users/pc/Documents/TIFF/P1COTO'

# Define a list to store the results
results = []

# Load the pre-trained ResNet50 model from PyTorch
model = models.resnet50(pretrained=True)
model.eval()  # Set the model to evaluation mode

# Define the preprocessing transformations for ResNet50
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# Class mapping for the output of ResNet50 (modify as per your classes)
class_mapping = {
    0: 'urbaine',
    1: 'forêt',
    2: 'rurale',
    3: 'eau',
    # Add more classes if needed
}

# Loop through all image files in the folder
for filename in os.listdir(patches_folder):
    if filename.endswith(".jpg"):
        # Load and preprocess the image
        img_path = os.path.join(patches_folder, filename)
        img = Image.open(img_path)
        img = transform(img)  # Apply the transformations

        # Add a batch dimension
        img = img.unsqueeze(0)

        # Make a prediction
        with torch.no_grad():  # Disable gradient calculations
            predictions = model(img)

        # Get the predicted class index
        predicted_class_index = torch.argmax(predictions, dim=1).item()

        # Get the zone type using the class mapping
        zone_type = class_mapping.get(predicted_class_index, 'inconnu')  # 'inconnu' for unknown classes

        # Append the results to the list
        results.append({'filename': filename, 'zone_type': zone_type})

# Create a Pandas DataFrame from the results
df = pd.DataFrame(results)

# Save the DataFrame to a CSV file
csv_output_path = 'C:/Users/pc/Documents/TIFF/predictions.csv'
df.to_csv(csv_output_path, index=False)

print(f"Predictions saved to: {csv_output_path}")
