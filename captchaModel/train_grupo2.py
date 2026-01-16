import os
import site

# ✅ CONFIGURACIÓN CUDA 11 OBLIGATORIA para TensorFlow 2.10
for sp in site.getsitepackages():
    nvidia_path = os.path.join(sp, 'nvidia')
    if os.path.exists(nvidia_path):
        for subdir in os.listdir(nvidia_path):
            bin_path = os.path.join(nvidia_path, subdir, 'bin')
            if os.path.exists(bin_path):
                try:
                    os.add_dll_directory(bin_path)
                except:
                    pass
                os.environ['PATH'] = bin_path + os.pathsep + os.environ.get('PATH', '')

import numpy as np
from pathlib import Path
import tensorflow as tf

# Configura GPU con memory growth
gpus = tf.config.list_physical_devices('GPU')
if gpus:
    for gpu in gpus:
        tf.config.experimental.set_memory_growth(gpu, True)
    print(f"✅ GPU activa: {gpus[0].name}")
else:
    print("⚠️ GPU no detectada - usando CPU")

from tensorflow import keras
from tensorflow.keras import layers
from PIL import Image
from sklearn.model_selection import train_test_split
import cv2

# ==================== CONFIG ====================
CAPTCHA_NAME = "grupo2_v1"
DATASET_PATH = "./captcha_datasets/grupo2/"

BASE_PRED_MODEL_PATH = ""

IMG_WIDTH = 200
IMG_HEIGHT = 60
MAX_LENGTH = 4
CHARACTERS = "0123456789"

BATCH_SIZE = 64  # ✅ Aumentado de 32 → 64 para más velocidad en GPU
EPOCHS = 250
LEARNING_RATE = 0.0001  # ✅ Aumentado porque batch_size es mayor
VALIDATION_SPLIT = 0.2

AUG_SWITCH_EPOCH = 20

MODEL_DIR = "models/"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, f"captcha_{CAPTCHA_NAME}.h5")
PRED_MODEL_PATH = MODEL_PATH.replace(".h5", "_pred.h5")

char_to_num_dict = {char: idx for idx, char in enumerate(CHARACTERS)}
num_to_char_dict = {idx: char for idx, char in enumerate(CHARACTERS)}

USE_HEAVY_AUG = False

def encode_label(label_str):
    return [char_to_num_dict[char] for char in label_str]

def decode_label(label_indices):
    return ''.join([num_to_char_dict[idx] for idx in label_indices if 0 <= idx < len(CHARACTERS)])

# ==================== AUGMENTATION ====================
def augment_light(img):
    h, w = img.shape
    
    if np.random.random() > 0.5:
        angle = np.random.uniform(-3, 3)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    if np.random.random() > 0.5:
        factor = np.random.uniform(0.85, 1.15)
        img = np.clip(img * factor, 0, 1)
    
    return img

def augment_heavy(img):
    h, w = img.shape
    
    if np.random.random() > 0.3:
        angle = np.random.uniform(-8, 8)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    if np.random.random() > 0.4:
        factor = np.random.uniform(0.65, 1.35)
        img = np.clip(img * factor, 0, 1)
    
    if np.random.random() > 0.5:
        noise = np.random.normal(0, 0.025, img.shape)
        img = np.clip(img + noise, 0, 1)
    
    if np.random.random() > 0.6:
        shift = np.random.randint(-5, 6)
        M = np.float32([[1, 0, shift], [0, 1, 0]])
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)
    
    return img

# ==================== PREPROCESAMIENTO ====================
def preprocess_image_file(img_path, augment=False):
    img = Image.open(img_path).convert('L').resize((IMG_WIDTH, IMG_HEIGHT), Image.BILINEAR)
    img = np.array(img, dtype=np.float32) / 255.0
    
    if augment:
        img = augment_heavy(img) if USE_HEAVY_AUG else augment_light(img)
    
    return img

# ==================== DATASET ====================
def load_dataset(dataset_path, max_length):
    images, labels = [], []
    for img_path in Path(dataset_path).glob("*.*"):
        label = img_path.stem
        
        if "_" in label:
            label = label.split('_')[0]
        
        if not label.isdigit() or len(label) != max_length:
            continue
        
        images.append(str(img_path))
        labels.append(label)
    
    print(f"✅ Dataset: {len(images)} imágenes")
    return images, labels

def prepare_dataset_arrays(images, labels, augment=False):
    aug_name = "HEAVY" if (augment and USE_HEAVY_AUG) else ("LIGHT" if augment else "NONE")
    print(f"📦 Procesando {len(images)} imágenes (aug={aug_name})...", end='', flush=True)
    
    all_images = np.zeros((len(images), IMG_WIDTH, IMG_HEIGHT, 1), dtype=np.float32)
    all_labels = []
    
    for i, (img_path, label_str) in enumerate(zip(images, labels)):
        img = preprocess_image_file(img_path, augment=augment)
        img = np.expand_dims(img, -1)
        img = np.transpose(img, (1, 0, 2))
        all_images[i] = img
        all_labels.append(encode_label(label_str))
    
    max_label_len = max(len(l) for l in all_labels)
    all_labels_padded = np.zeros((len(all_labels), max_label_len), dtype=np.float32)
    for i, lab in enumerate(all_labels):
        all_labels_padded[i, :len(lab)] = lab
    
    input_length = np.full((len(all_images), 1), IMG_WIDTH // 4, dtype=np.int64)
    label_length = np.array([[len(l)] for l in all_labels], dtype=np.int64)
    
    print(" ✅")
    return all_images, all_labels_padded, input_length, label_length

# ==================== MODELO ====================
def build_model_like_original(num_chars):
    input_img = layers.Input(shape=(IMG_WIDTH, IMG_HEIGHT, 1), name="image", dtype="float32")
    labels_in = layers.Input(name="label", shape=(None,), dtype="float32")
    input_length = layers.Input(name='input_length', shape=[1], dtype='int64')
    label_length = layers.Input(name='label_length', shape=[1], dtype='int64')
    
    x = layers.Conv2D(32, (3, 3), activation="relu", padding="same")(input_img)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    
    x = layers.Conv2D(64, (3, 3), activation="relu", padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    
    x = layers.Conv2D(128, (3, 3), activation="relu", padding="same")(x)
    x = layers.BatchNormalization()(x)
    
    new_shape = ((IMG_WIDTH // 4), (IMG_HEIGHT // 4) * 128)
    x = layers.Reshape(target_shape=new_shape)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    
    x = layers.Bidirectional(layers.LSTM(256, return_sequences=True, dropout=0.2))(x)
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=0.2))(x)
    
    output = layers.Dense(num_chars + 1, activation="softmax", name="output")(x)
    
    loss_out = layers.Lambda(
        lambda args: tf.keras.backend.ctc_batch_cost(args[0], args[1], args[2], args[3]),
        output_shape=(1,),
        name='ctc_loss'
    )([labels_in, output, input_length, label_length])
    
    model_full = keras.models.Model([input_img, labels_in, input_length, label_length], loss_out)
    model_pred = keras.models.Model(input_img, output)
    
    return model_full, model_pred

# ==================== CALLBACK ====================
class ProgressiveAugmentation(keras.callbacks.Callback):
    def on_epoch_begin(self, epoch, logs=None):
        global USE_HEAVY_AUG
        if (not USE_HEAVY_AUG) and epoch >= AUG_SWITCH_EPOCH:
            USE_HEAVY_AUG = True
            print(f"\n🔄 HEAVY augmentation activada (epoch {epoch})")

# ==================== PRED / EVAL ====================
def decode_predictions(pred):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    results = tf.keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][:, :MAX_LENGTH]
    return [decode_label(r.numpy()) for r in results]

def evaluate_accuracy(pred_model, images, labels, n=100):  # ✅ Reducido a 100 para más velocidad
    correct = sum(1 for img, lbl in zip(images[:n], labels[:n]) 
                  if decode_predictions(pred_model.predict(
                      np.expand_dims(np.transpose(np.expand_dims(preprocess_image_file(img, False), -1), (1,0,2)), 0), 
                      verbose=0))[0] == lbl)
    return (correct / n) * 100

# ==================== TRAIN ====================
def train_model():
    global USE_HEAVY_AUG
    
    print(f"\n{'='*70}")
    print(f"🎯 {CAPTCHA_NAME.upper()} - GPU Training")
    print(f"{'='*70}\n")
    
    images, labels = load_dataset(DATASET_PATH, MAX_LENGTH)
    
    train_images, val_images, train_labels, val_labels = train_test_split(
        images, labels, test_size=VALIDATION_SPLIT, random_state=42, shuffle=True
    )
    print(f"Train: {len(train_images)} | Val: {len(val_images)}\n")
    
    USE_HEAVY_AUG = False
    train_imgs, train_lbls, train_inp_len, train_lbl_len = prepare_dataset_arrays(train_images, train_labels, augment=True)
    val_imgs, val_lbls, val_inp_len, val_lbl_len = prepare_dataset_arrays(val_images, val_labels, augment=False)
    
    print("\n🔨 Construyendo modelo...")
    model_full, model_pred = build_model_like_original(len(CHARACTERS))
    
    model_full.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss=lambda y_true, y_pred: y_pred
    )
    
    callbacks = [
        ProgressiveAugmentation(),
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=50, restore_best_weights=True, verbose=1),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=20, verbose=1, min_lr=1e-7),
        keras.callbacks.ModelCheckpoint(MODEL_PATH, monitor='val_loss', save_best_only=True, verbose=1),
    ]
    
    train_outputs = np.zeros(len(train_imgs), dtype=np.float32)
    val_outputs = np.zeros(len(val_imgs), dtype=np.float32)
    
    print("🚀 Entrenando...\n")
    
    history = model_full.fit(
        x=[train_imgs, train_lbls, train_inp_len, train_lbl_len],
        y=train_outputs,
        validation_data=([val_imgs, val_lbls, val_inp_len, val_lbl_len], val_outputs),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=2  # ✅ Cambio a verbose=2 (menos output, más rápido)
    )
    
    model_pred.save(PRED_MODEL_PATH)
    print(f"\n✅ Guardado: {PRED_MODEL_PATH}")
    
    print("\n📊 Evaluando...")
    val_acc = evaluate_accuracy(model_pred, val_images, val_labels, n=100)
    train_acc = evaluate_accuracy(model_pred, train_images, train_labels, n=100)
    
    print(f"\n{'='*70}")
    print(f"📈 RESULTADOS")
    print(f"{'='*70}")
    print(f"   Best Val Loss: {min(history.history['val_loss']):.4f}")
    print(f"   Train Acc: {train_acc:.1f}%")
    print(f"   Val Acc: {val_acc:.1f}%")
    print(f"   Epochs: {len(history.history['loss'])}")
    print(f"{'='*70}\n")
    
    return model_pred, history

if __name__ == "__main__":
    train_model()
