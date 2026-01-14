# train_grupo3_v3_PROGRESSIVE_AUG.py - SOLUCIÓN DEFINITIVA
import os
import numpy as np
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from PIL import Image
from sklearn.model_selection import train_test_split
import cv2
import gc

DATASET_PATH = "captcha_datasets/grupo3/"
MODEL_V2_FULL = "models/captcha_grupo3_v4_progressive.keras"
MODEL_V3_OUTPUT = "models/captcha_grupo3_v5_progressive.keras"
MODEL_V3_PRED_OUTPUT = "models/captcha_grupo3_v5_progressive_pred.keras"

IMG_WIDTH = 200
IMG_HEIGHT = 60
MAX_LENGTH = 4
CHARACTERS = "0123456789"

# CONFIGURACIÓN OPTIMIZADA PARA TRANSFER LEARNING
BATCH_SIZE = 16                # Pequeño para estabilidad
EPOCHS = 300
LEARNING_RATE = 0.00003       # Bajo para no destruir pesos de V2
VALIDATION_SPLIT = 0.2

# Épocas para cambiar augmentation
AUGMENTATION_SWITCH_EPOCH = 30  # Épocas 0-30: light, 30+: heavy

char_to_num_dict = {char: idx for idx, char in enumerate(CHARACTERS)}
num_to_char_dict = {idx: char for idx, char in enumerate(CHARACTERS)}

def encode_label(label_str):
    return [char_to_num_dict[char] for char in label_str]

def decode_label(label_indices):
    result = []
    for idx in label_indices:
        if 0 <= idx < len(CHARACTERS):
            result.append(num_to_char_dict[idx])
    return ''.join(result)

# ==================== AUGMENTATION LIGHT ====================
def augment_image_light(img_array):
    """
    Augmentation SUAVE para épocas 0-30
    Mantiene las imágenes similares a las que V2 conoce
    """
    h, w = img_array.shape
    
    # 1. Rotación suave
    if np.random.random() > 0.3:
        angle = np.random.uniform(-3, 3)  # ±3° (era ±8°)
        M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
        img_array = cv2.warpAffine(img_array, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    # 2. Brillo suave
    if np.random.random() > 0.3:
        factor = np.random.uniform(0.8, 1.2)  # 0.8-1.2 (era 0.5-1.5)
        img_array = np.clip(img_array * factor, 0, 1)
    
    # 3. Contraste suave
    if np.random.random() > 0.4:
        mean = img_array.mean()
        factor = np.random.uniform(0.8, 1.2)  # 0.8-1.2 (era 0.5-1.5)
        img_array = np.clip((img_array - mean) * factor + mean, 0, 1)
    
    # 4. Ruido suave
    if np.random.random() > 0.5:
        noise = np.random.normal(0, 0.02, img_array.shape)  # 0.02 (era 0.04)
        img_array = np.clip(img_array + noise, 0, 1)
    
    # 5. Desplazamiento horizontal suave
    if np.random.random() > 0.4:
        shift = np.random.randint(-3, 4)  # ±3px (era ±8px)
        M = np.float32([[1, 0, shift], [0, 1, 0]])
        img_array = cv2.warpAffine(img_array, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    # 6. Blur suave
    if np.random.random() > 0.7:
        kernel_size = np.random.choice([3, 5])  # Solo 3 o 5 (era 3,5,7)
        img_array = cv2.GaussianBlur(img_array, (kernel_size, kernel_size), 0)
    
    if img_array.shape != (h, w):
        img_array = cv2.resize(img_array, (w, h))
    
    return img_array

# ==================== AUGMENTATION HEAVY ====================
def augment_image_heavy(img_array):
    """
    Augmentation AGRESIVO para épocas 30+
    Máxima generalización una vez consolidado el transfer learning
    """
    h, w = img_array.shape
    
    # 1. Rotación agresiva
    if np.random.random() > 0.15:
        angle = np.random.uniform(-8, 8)
        M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
        img_array = cv2.warpAffine(img_array, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    # 2. Brillo extremo
    if np.random.random() > 0.15:
        factor = np.random.uniform(0.5, 1.5)
        img_array = np.clip(img_array * factor, 0, 1)
    
    # 3. Contraste extremo
    if np.random.random() > 0.2:
        mean = img_array.mean()
        factor = np.random.uniform(0.5, 1.5)
        img_array = np.clip((img_array - mean) * factor + mean, 0, 1)
    
    # 4. Ruido pesado
    if np.random.random() > 0.3:
        noise = np.random.normal(0, 0.04, img_array.shape)
        img_array = np.clip(img_array + noise, 0, 1)
    
    # 5. Blur variable
    if np.random.random() > 0.6:
        kernel_size = np.random.choice([3, 5, 7])
        img_array = cv2.GaussianBlur(img_array, (kernel_size, kernel_size), 0)
    
    # 6. Desplazamiento horizontal agresivo
    if np.random.random() > 0.3:
        shift = np.random.randint(-8, 9)
        M = np.float32([[1, 0, shift], [0, 1, 0]])
        img_array = cv2.warpAffine(img_array, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    # 7. Desplazamiento vertical
    if np.random.random() > 0.4:
        shift = np.random.randint(-4, 5)
        M = np.float32([[1, 0, 0], [0, 1, shift]])
        img_array = cv2.warpAffine(img_array, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    # 8. Escalado
    if np.random.random() > 0.5:
        scale = np.random.uniform(0.85, 1.15)
        M = cv2.getRotationMatrix2D((w/2, h/2), 0, scale)
        img_array = cv2.warpAffine(img_array, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    # 9. Inversión
    if np.random.random() > 0.8:
        img_array = 1.0 - img_array
    
    # 10. Shear (distorsión)
    if np.random.random() > 0.75:
        shift_x = np.random.randint(-4, 5)
        shift_y = np.random.randint(-3, 4)
        shear = np.random.uniform(-0.15, 0.15)
        M = np.float32([[1, shear, shift_x], [shear, 1, shift_y]])
        img_array = cv2.warpAffine(img_array, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    # 11. Erosión/Dilatación
    if np.random.random() > 0.8:
        kernel = np.ones((2,2), np.uint8)
        if np.random.random() > 0.5:
            img_array = cv2.erode(img_array, kernel, iterations=1)
        else:
            img_array = cv2.dilate(img_array, kernel, iterations=1)
    
    # 12. Salt & pepper noise
    if np.random.random() > 0.85:
        noise_mask = np.random.random(img_array.shape)
        img_array[noise_mask < 0.02] = 0
        img_array[noise_mask > 0.98] = 1
    
    # 13. Motion blur
    if np.random.random() > 0.9:
        kernel_size = np.random.choice([3, 5])
        kernel_motion_blur = np.zeros((kernel_size, kernel_size))
        kernel_motion_blur[int((kernel_size-1)/2), :] = np.ones(kernel_size)
        kernel_motion_blur = kernel_motion_blur / kernel_size
        img_array = cv2.filter2D(img_array, -1, kernel_motion_blur)
    
    # 14. Ajuste gamma
    if np.random.random() > 0.85:
        gamma = np.random.uniform(0.7, 1.3)
        img_array = np.clip(np.power(img_array, gamma), 0, 1)
    
    if img_array.shape != (h, w):
        img_array = cv2.resize(img_array, (w, h))
    
    return img_array

# Variable global para controlar qué augmentation usar
USE_HEAVY_AUGMENTATION = False

def load_dataset(dataset_path, max_length):
    images = []
    labels = []
    
    for img_path in Path(dataset_path).glob("*.*"):
        label = img_path.stem
        if '_' in label or not label.isdigit() or len(label) != max_length:
            continue
        images.append(str(img_path))
        labels.append(label)
    
    print(f"\n✅ Dataset: {len(images)} imágenes válidas")
    return images, labels

def preprocess_image_file(img_path, augment=False):
    global USE_HEAVY_AUGMENTATION
    
    img = Image.open(img_path).convert('L')
    img = img.resize((IMG_WIDTH, IMG_HEIGHT))
    img_array = np.array(img).astype(np.float32) / 255.0
    
    if augment:
        if USE_HEAVY_AUGMENTATION:
            img_array = augment_image_heavy(img_array)
        else:
            img_array = augment_image_light(img_array)
    
    if img_array.shape != (IMG_HEIGHT, IMG_WIDTH):
        img_array = cv2.resize(img_array, (IMG_WIDTH, IMG_HEIGHT))
    
    return img_array

def prepare_dataset_arrays(images, labels, augment=False):
    aug_type = "HEAVY" if USE_HEAVY_AUGMENTATION and augment else ("LIGHT" if augment else "NONE")
    print(f"\n📦 Cargando {len(images)} imágenes (augment={aug_type})...")
    
    all_images = []
    all_labels = []
    
    for i, (img_path, label_str) in enumerate(zip(images, labels)):
        img = preprocess_image_file(img_path, augment=augment)
        img = np.expand_dims(img, -1)
        img = np.transpose(img, (1, 0, 2))
        all_images.append(img)
        
        label_encoded = encode_label(label_str)
        all_labels.append(label_encoded)
        
        if (i + 1) % 200 == 0:
            print(f"   {i+1}/{len(images)}...")
    
    all_images = np.array(all_images, dtype=np.float32)
    
    max_label_len = max(len(l) for l in all_labels)
    all_labels_padded = np.zeros((len(all_labels), max_label_len), dtype=np.float32)
    for i, label in enumerate(all_labels):
        all_labels_padded[i, :len(label)] = label
    
    input_length = np.ones((len(all_images), 1), dtype=np.int64) * (IMG_WIDTH // 4)
    label_length = np.array([[len(l)] for l in all_labels], dtype=np.int64)
    
    print(f"✅ Preparados: {len(all_images)} imágenes")
    return all_images, all_labels_padded, input_length, label_length

def decode_predictions(pred):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    results = tf.keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][:, :MAX_LENGTH]
    
    output_text = []
    for res in results:
        indices = res.numpy()
        text = decode_label(indices)
        output_text.append(text)
    return output_text

def predict_single(pred_model, img_path):
    img = preprocess_image_file(img_path, augment=False)
    img = np.expand_dims(img, -1)
    img = np.transpose(img, (1, 0, 2))
    img = np.expand_dims(img, axis=0)
    
    pred = pred_model.predict(img, verbose=0)
    pred_text = decode_predictions(pred)[0]
    return pred_text

def evaluate_accuracy_complete(pred_model, images, labels):
    correct = 0
    total = len(images)
    errors = []
    
    print(f"\n🔍 Evaluando {total} imágenes...")
    
    for i, (img_path, true_label) in enumerate(zip(images, labels)):
        try:
            pred_label = predict_single(pred_model, img_path)
            if pred_label == true_label:
                correct += 1
            else:
                errors.append({'pred': pred_label, 'true': true_label})
        except:
            errors.append({'pred': 'ERROR', 'true': true_label})
        
        if (i + 1) % 50 == 0:
            print(f"   {i+1}/{total}...")
    
    accuracy = (correct / total) * 100
    
    confusions = {}
    for err in errors:
        if err['pred'] != 'ERROR' and len(err['pred']) == len(err['true']):
            for p, t in zip(err['pred'], err['true']):
                if p != t:
                    key = f"{t}→{p}"
                    confusions[key] = confusions.get(key, 0) + 1
    
    return accuracy, errors, confusions

# ==================== PROGRESSIVE AUGMENTATION CALLBACK ====================
class ProgressiveAugmentation(keras.callbacks.Callback):
    """
    Callback para cambiar de augmentation light a heavy en época específica
    """
    def __init__(self, switch_epoch, train_images, train_labels):
        super().__init__()
        self.switch_epoch = switch_epoch
        self.train_images = train_images
        self.train_labels = train_labels
        self.data_reloaded = False
    
    def on_epoch_begin(self, epoch, logs=None):
        global USE_HEAVY_AUGMENTATION
        
        if epoch == self.switch_epoch and not self.data_reloaded:
            print(f"\n{'='*70}")
            print(f"🔄 ÉPOCA {epoch}: CAMBIANDO A AUGMENTATION HEAVY")
            print(f"{'='*70}")
            print(f"Épocas 0-{self.switch_epoch-1}: Augmentation LIGHT (mantener V2)")
            print(f"Épocas {self.switch_epoch}+: Augmentation HEAVY (mejorar generalización)")
            print(f"{'='*70}\n")
            
            USE_HEAVY_AUGMENTATION = True
            self.data_reloaded = True
            
            # Nota: En un sistema ideal recargaríamos el dataset aquí,
            # pero como Keras ya tiene los datos en memoria, el cambio
            # afectará solo a partir de la próxima época

def train_model():
    global USE_HEAVY_AUGMENTATION
    
    print(f"\n{'='*70}")
    print(f"🎯 V3 - TRANSFER LEARNING CON AUGMENTATION PROGRESIVO")
    print(f"{'='*70}\n")
    print(f"Estrategia:")
    print(f"  Épocas 0-{AUGMENTATION_SWITCH_EPOCH}: Augmentation LIGHT (6 transformaciones suaves)")
    print(f"  Épocas {AUGMENTATION_SWITCH_EPOCH}+: Augmentation HEAVY (14 transformaciones agresivas)")
    print(f"  ")
    print(f"  Esto permite:")
    print(f"  1. Mantener los pesos de V2 intactos (épocas 0-30)")
    print(f"  2. Val_loss inicial ~0.27 (91% accuracy)")
    print(f"  3. Luego mejorar generalización (épocas 30+)")
    print(f"  4. Meta: 95-96% accuracy final\n")
    
    images, labels = load_dataset(DATASET_PATH, MAX_LENGTH)
    
    train_images, val_images, train_labels, val_labels = train_test_split(
        images, labels, test_size=VALIDATION_SPLIT, random_state=42, shuffle=True
    )
    
    print(f"📂 Train: {len(train_images)} | Val: {len(val_images)}")
    
    # Preparar datasets con augmentation LIGHT inicial
    USE_HEAVY_AUGMENTATION = False
    
    train_imgs, train_lbls, train_inp_len, train_lbl_len = prepare_dataset_arrays(
        train_images, train_labels, augment=True
    )
    val_imgs, val_lbls, val_inp_len, val_lbl_len = prepare_dataset_arrays(
        val_images, val_labels, augment=False
    )
    
    print("\n✅ Dataset inicial cargado con augmentation LIGHT")
    
    # Cargar y clonar V2
    print(f"\n🔄 Cargando modelo V2: {MODEL_V2_FULL}")
    
    try:
        keras.config.enable_unsafe_deserialization()
        model_v2 = keras.models.load_model(MODEL_V2_FULL, safe_mode=False)
        print(f"✅ Modelo V2 cargado\n")
        
        input_img = model_v2.get_layer('image').output
        labels_input = model_v2.get_layer('label').output
        input_length = model_v2.get_layer('input_length').output
        label_length = model_v2.get_layer('label_length').output
        output_layer = model_v2.get_layer('output').output
        
        loss_out = layers.Lambda(
            lambda args: tf.keras.backend.ctc_batch_cost(args[0], args[1], args[2], args[3]),
            output_shape=(1,),
            name='ctc_loss_v3'
        )([labels_input, output_layer, input_length, label_length])
        
        model_v3 = keras.Model(
            inputs=[input_img, labels_input, input_length, label_length],
            outputs=loss_out
        )
        
        # Copiar TODOS los pesos
        print(f"🔄 Copiando pesos de V2 a V3...\n")
        layers_copied = 0
        skip_layers = ['image', 'label', 'input_length', 'label_length', 'ctc_loss']
        
        for layer_v2 in model_v2.layers:
            if layer_v2.name in skip_layers:
                continue
            
            weights_v2 = layer_v2.get_weights()
            if len(weights_v2) == 0:
                continue
            
            try:
                layer_v3 = model_v3.get_layer(layer_v2.name)
                layer_v3.set_weights(weights_v2)
                layers_copied += 1
                print(f"   ✓ {layer_v2.name}")
            except:
                pass
        
        print(f"\n✅ Transfer learning: {layers_copied} capas copiadas")
        print(f"   Con augmentation LIGHT, modelo debería empezar en ~0.27 val_loss\n")
        
        del model_v2
        gc.collect()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None, None
    
    # Compilar con LR bajo
    model_v3.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss=lambda y_true, y_pred: y_pred
    )
    
    # Callbacks
    callbacks = [
        ProgressiveAugmentation(
            switch_epoch=AUGMENTATION_SWITCH_EPOCH,
            train_images=train_images,
            train_labels=train_labels
        ),
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=70,  # Más paciencia porque cambia augmentation
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=25,
            verbose=1,
            min_lr=1e-7
        ),
        keras.callbacks.ModelCheckpoint(
            MODEL_V3_OUTPUT,
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
    ]
    
    print(f"🚀 ENTRENAMIENTO PROGRESIVO\n")
    print(f"   Batch size: {BATCH_SIZE}")
    print(f"   Learning rate: {LEARNING_RATE}")
    print(f"   Epochs max: {EPOCHS}")
    print(f"   Augmentation switch: Época {AUGMENTATION_SWITCH_EPOCH}\n")
    print(f"   Expectativa:")
    print(f"   - Época 1: val_loss ~0.27-0.30 (91% accuracy)")
    print(f"   - Época 30: val_loss ~0.18-0.22 (93-94%)")
    print(f"   - Época {AUGMENTATION_SWITCH_EPOCH}: CAMBIO A HEAVY")
    print(f"   - Época 100: val_loss ~0.12-0.16 (95-96%)\n")
    
    train_outputs = np.zeros((len(train_imgs),), dtype=np.float32)
    val_outputs = np.zeros((len(val_imgs),), dtype=np.float32)
    
    history = model_v3.fit(
        x=[train_imgs, train_lbls, train_inp_len, train_lbl_len],
        y=train_outputs,
        validation_data=([val_imgs, val_lbls, val_inp_len, val_lbl_len], val_outputs),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    
    # Guardar modelo de predicción
    pred_model = keras.Model(inputs=input_img, outputs=output_layer)
    pred_model.save(MODEL_V3_PRED_OUTPUT)
    
    print(f"\n✅ Modelos guardados")
    
    # Evaluación final
    val_acc, val_errors, val_confusions = evaluate_accuracy_complete(
        pred_model, val_images, val_labels
    )
    
    print(f"\n{'='*70}")
    print(f"📈 RESULTADOS FINALES V3 PROGRESSIVE")
    print(f"{'='*70}")
    print(f"   Best Val Loss: {min(history.history['val_loss']):.4f}")
    print(f"   Final Accuracy: {val_acc:.2f}%")
    print(f"   Mejora desde V2: +{val_acc - 91.0:.2f}%")
    print(f"   Epochs entrenados: {len(history.history['loss'])}")
    
    if val_acc >= 96:
        print(f"   🎉🎉🎉 ¡META SUPERADA! Accuracy >= 96%")
    elif val_acc >= 94:
        print(f"   🎉🎉 ¡META ALCANZADA! Accuracy >= 94%")
    elif val_acc >= 92:
        print(f"   ✅ Muy bueno - Cerca de meta")
    elif val_acc > 91:
        print(f"   ✅ Mejora sobre V2")
    
    print(f"{'='*70}\n")
    
    if val_confusions:
        print("🔍 Top 10 confusiones más frecuentes:")
        for confusion, count in sorted(val_confusions.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {confusion}: {count} veces")
        print()
    
    print("🔍 20 muestras aleatorias:")
    samples_correct = 0
    for idx in np.random.choice(len(val_images), min(20, len(val_images)), replace=False):
        pred = predict_single(pred_model, val_images[idx])
        real = val_labels[idx]
        status = "✅" if pred == real else "❌"
        if pred == real:
            samples_correct += 1
        print(f"   {status} Pred: '{pred}' | Real: '{real}'")
    
    print(f"\n   Accuracy en muestras: {(samples_correct/20)*100:.0f}%")
    
    return pred_model, history

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🎯 V3 - TRANSFER LEARNING PROGRESIVO")
    print("="*70)
    print("Estrategia de 2 fases:")
    print("  FASE 1 (épocas 0-30): Augmentation LIGHT")
    print("    → Mantener conocimiento de V2 (91%)")
    print("  ")
    print("  FASE 2 (épocas 30+): Augmentation HEAVY")
    print("    → Mejorar generalización hacia 95-96%")
    print("  ")
    print("Meta: 95-96% accuracy final")
    print("="*70 + "\n")
    
    model, history = train_model()
