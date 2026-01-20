# Script: resize_training_dataset.py
from PIL import Image
import os
from pathlib import Path

INPUT_FOLDER = "./captcha_datasets/grupo3/"
OUTPUT_FOLDER = "./captcha_datasets/grupo3_200x62/"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

for img_path in Path(INPUT_FOLDER).glob("*.png"):
    img = Image.open(img_path)
    
    # Reescalar de 132x41 → 200x62 (tamaño real del website)
    img_resized = img.resize((200, 62), Image.LANCZOS)
    
    # Guardar con mismo nombre
    output_path = Path(OUTPUT_FOLDER) / img_path.name
    img_resized.save(output_path)
    
    if len(list(Path(OUTPUT_FOLDER).glob("*.png"))) % 100 == 0:
        print(f"Procesadas: {len(list(Path(OUTPUT_FOLDER).glob('*.png')))}")

print(f"✅ Dataset reescalado: {OUTPUT_FOLDER}")
