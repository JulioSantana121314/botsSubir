import os
from PIL import Image
import numpy as np
from pathlib import Path

# Tus captchas reales
REAL_CAPTCHAS = "../balanceScripts/captchas/grupo3Test/"  # o el folder que uses
IMG_WIDTH = 200
IMG_HEIGHT = 60

real_imgs = list(Path(REAL_CAPTCHAS).glob("*.png"))[:10]

for img_path in real_imgs:
    # Preprocesar EXACTAMENTE como en entrenamiento
    img = Image.open(img_path).convert('L').resize((IMG_WIDTH, IMG_HEIGHT), Image.BILINEAR)
    img_array = np.array(img, dtype=np.float32) / 255.0
    
    # Visualizar
    import matplotlib.pyplot as plt
    plt.imshow(img_array, cmap='gray')
    plt.title(f"Real: {img_path.stem}")
    plt.show()
    
    print(f"Shape: {img_array.shape}, Min: {img_array.min():.3f}, Max: {img_array.max():.3f}")
