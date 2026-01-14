import os
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from PIL import Image, ImageEnhance
import cv2

DATASET_PATH = "./captcha_datasets/grupo3/"

def preprocesar_captcha_grupo3(pil_img):
    """
    Preprocesamiento del script de entrenamiento
    """
    try:
        if pil_img.mode != 'RGB':
            pil_img = pil_img.convert('RGB')
        
        img_array = np.array(pil_img)
        
        # 1. Aumentar contraste
        enhancer = ImageEnhance.Contrast(pil_img)
        pil_img = enhancer.enhance(2.0)
        
        # 2. Convertir a escala de grises
        gray = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)
        
        # 3. Aplicar blur
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # 4. Threshold adaptativo
        thresh = cv2.adaptiveThreshold(
            blurred, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            15, 5
        )
        
        # 5. Operaciones morfológicas
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        # 6. Invertir
        final = cv2.bitwise_not(cleaned)
        
        return Image.fromarray(final)
    
    except Exception as e:
        print(f"Error: {e}")
        return pil_img.convert('L')

# Comparar ANTES vs DESPUÉS del preprocesamiento
images = list(Path(DATASET_PATH).glob("*.png"))[:12]

fig, axes = plt.subplots(4, 6, figsize=(18, 12))

for i, img_path in enumerate(images):
    # Original
    img_original = Image.open(img_path)
    axes[i//3, (i%3)*2].imshow(img_original)
    axes[i//3, (i%3)*2].set_title(f"Original: {img_path.stem}", fontsize=8)
    axes[i//3, (i%3)*2].axis('off')
    
    # Procesada
    img_procesada = preprocesar_captcha_grupo3(img_original)
    axes[i//3, (i%3)*2+1].imshow(img_procesada, cmap='gray')
    axes[i//3, (i%3)*2+1].set_title(f"Procesada: {img_path.stem}", fontsize=8)
    axes[i//3, (i%3)*2+1].axis('off')

plt.tight_layout()
plt.savefig('comparacion_preprocesamiento.png', dpi=150, bbox_inches='tight')
print("✅ Guardado en: comparacion_preprocesamiento.png")
print("\n🔍 Verifica si los números son LEGIBLES después del preprocesamiento")
print("   Si los números desaparecen o se distorsionan mucho = ese es el problema")
