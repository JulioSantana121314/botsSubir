import os
import numpy as np
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from PIL import Image
from sklearn.model_selection import train_test_split
import cv2

# ==================== CONFIG ====================
CAPTCHA_NAME = "grupo2_v4_progressive"
DATASET_PATH = "./captcha_datasets/grupo2/"

# ✅ Base correcta (tu v2 pred)
BASE_PRED_MODEL_PATH = "models/captcha_grupo2_v3_progressive.keras"

IMG_WIDTH = 200
IMG_HEIGHT = 60
MAX_LENGTH = 4
CHARACTERS = "0123456789"

BATCH_SIZE = 16
EPOCHS = 250
LEARNING_RATE = 0.00003
VALIDATION_SPLIT = 0.2

AUG_SWITCH_EPOCH = 25  # 0..24 LIGHT, 25+ HEAVY

MODEL_DIR = "models/"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, f"captcha_{CAPTCHA_NAME}.keras")
PRED_MODEL_PATH = MODEL_PATH.replace(".keras", "_pred.keras")

char_to_num_dict = {char: idx for idx, char in enumerate(CHARACTERS)}
num_to_char_dict = {idx: char for idx, char in enumerate(CHARACTERS)}

USE_HEAVY_AUG = False


def encode_label(label_str):
    return [char_to_num_dict[char] for char in label_str]


def decode_label(label_indices):
    result = []
    for idx in label_indices:
        if 0 <= idx < len(CHARACTERS):
            result.append(num_to_char_dict[idx])
    return ''.join(result)


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

    if np.random.random() > 0.6:
        noise = np.random.normal(0, 0.015, img.shape)
        img = np.clip(img + noise, 0, 1)

    if np.random.random() > 0.65:
        shift = np.random.randint(-3, 4)
        M = np.float32([[1, 0, shift], [0, 1, 0]])
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    if img.shape != (h, w):
        img = cv2.resize(img, (w, h))

    return img


def augment_heavy(img):
    h, w = img.shape

    if np.random.random() > 0.2:
        angle = np.random.uniform(-8, 8)
        M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0)
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    if np.random.random() > 0.25:
        factor = np.random.uniform(0.6, 1.4)
        img = np.clip(img * factor, 0, 1)

    if np.random.random() > 0.35:
        mean = img.mean()
        c = np.random.uniform(0.7, 1.3)
        img = np.clip((img - mean) * c + mean, 0, 1)

    if np.random.random() > 0.35:
        noise = np.random.normal(0, 0.03, img.shape)
        img = np.clip(img + noise, 0, 1)

    if np.random.random() > 0.7:
        k = np.random.choice([3, 5])
        img = cv2.GaussianBlur(img, (k, k), 0)

    if np.random.random() > 0.55:
        shift = np.random.randint(-6, 7)
        M = np.float32([[1, 0, shift], [0, 1, 0]])
        img = cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)

    if np.random.random() > 0.85:
        img = 1.0 - img

    if img.shape != (h, w):
        img = cv2.resize(img, (w, h))

    return img


# ==================== PREPROCESAMIENTO ====================
def preprocess_image_file(img_path, augment=False):
    img = Image.open(img_path).convert('L')
    img = img.resize((IMG_WIDTH, IMG_HEIGHT))
    img = np.array(img).astype(np.float32) / 255.0

    if augment:
        img = augment_heavy(img) if USE_HEAVY_AUG else augment_light(img)

    return img


# ==================== DATASET ====================
def load_dataset(dataset_path, max_length):
    images, labels = [], []
    for img_path in Path(dataset_path).glob("*.*"):
        label = img_path.stem
        if "_" in label:
            continue
        if not label.isdigit():
            continue
        if len(label) != max_length:
            continue
        images.append(str(img_path))
        labels.append(label)

    print(f"\n✅ Dataset: {len(images)} imágenes válidas")
    return images, labels


def prepare_dataset_arrays(images, labels, augment=False):
    aug_name = "HEAVY" if (augment and USE_HEAVY_AUG) else ("LIGHT" if augment else "NONE")
    print(f"\n📦 Cargando {len(images)} imágenes (augment={aug_name})...")

    all_images = []
    all_labels = []

    for i, (img_path, label_str) in enumerate(zip(images, labels)):
        img = preprocess_image_file(img_path, augment=augment)
        img = np.expand_dims(img, -1)
        img = np.transpose(img, (1, 0, 2))  # (W,H,1)
        all_images.append(img)
        all_labels.append(encode_label(label_str))

        if (i + 1) % 200 == 0:
            print(f"   {i+1}/{len(images)}...")

    all_images = np.array(all_images, dtype=np.float32)

    max_label_len = max(len(l) for l in all_labels)
    all_labels_padded = np.zeros((len(all_labels), max_label_len), dtype=np.float32)
    for i, lab in enumerate(all_labels):
        all_labels_padded[i, :len(lab)] = lab

    input_length = np.ones((len(all_images), 1), dtype=np.int64) * (IMG_WIDTH // 4)
    label_length = np.array([[len(l)] for l in all_labels], dtype=np.int64)

    print(f"✅ Preparados: {len(all_images)} imágenes")
    return all_images, all_labels_padded, input_length, label_length


# ==================== MODELO (CLON DE TU ORIGINAL “V2” DE EJEMPLO) ====================
def build_model_like_original(num_chars):
    input_img = layers.Input(shape=(IMG_WIDTH, IMG_HEIGHT, 1), name="image", dtype="float32")
    labels_in = layers.Input(name="label", shape=(None,), dtype="float32")
    input_length = layers.Input(name='input_length', shape=[1], dtype='int64')
    label_length = layers.Input(name='label_length', shape=[1], dtype='int64')

    # CNN: 32/64/128 (como tu script original)
    x = layers.Conv2D(32, (3, 3), activation="relu", padding="same")(input_img)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)

    x = layers.Conv2D(64, (3, 3), activation="relu", padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)

    x = layers.Conv2D(128, (3, 3), activation="relu", padding="same")(x)
    x = layers.BatchNormalization()(x)

    # Reshape
    new_shape = ((IMG_WIDTH // 4), (IMG_HEIGHT // 4) * 128)
    x = layers.Reshape(target_shape=new_shape)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)

    # RNN: BiLSTM 256/128 (como tu script original)
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


# ==================== TRANSFER (GARANTIZADO PARA ARQUITECTURAS IGUALES) ====================
def _layer_signature(layer):
    ws = layer.get_weights()
    shapes = tuple(w.shape for w in ws) if ws else tuple()
    return (layer.__class__.__name__, shapes)


def transfer_weights_from_v2pred(src_pred, dst_pred):
    """
    Primero intenta por nombre, luego por firma/orden.
    Para tu caso (arquitectura igual), el fallback por firma/orden suele copiar todo.
    """
    # 1) por nombre (solo la capa output está nombrada)
    copied_by_name = 0
    for dst_layer in dst_pred.layers:
        try:
            src_layer = src_pred.get_layer(dst_layer.name)
            ws = src_layer.get_weights()
            if not ws:
                continue
            dw = dst_layer.get_weights()
            if len(ws) != len(dw):
                continue
            ok = all(a.shape == b.shape for a, b in zip(ws, dw))
            if ok:
                dst_layer.set_weights(ws)
                copied_by_name += 1
        except Exception:
            pass
    print(f"[TL] Copied by name: {copied_by_name}")

    # 2) por firma/orden en capas con pesos
    src_w = [l for l in src_pred.layers if len(l.get_weights()) > 0]
    dst_w = [l for l in dst_pred.layers if len(l.get_weights()) > 0]

    copied = 0
    for s, d in zip(src_w, dst_w):
        if _layer_signature(s) == _layer_signature(d):
            d.set_weights(s.get_weights())
            copied += 1

    print(f"[TL] Copied by zip(signature): {copied}")
    print(f"[TL] Src weighted layers: {len(src_w)} | Dst weighted layers: {len(dst_w)}")

    return copied_by_name + copied


# ==================== CALLBACK SWITCH AUG ====================
class ProgressiveAugmentation(keras.callbacks.Callback):
    def on_epoch_begin(self, epoch, logs=None):
        global USE_HEAVY_AUG
        if (not USE_HEAVY_AUG) and epoch >= AUG_SWITCH_EPOCH:
            USE_HEAVY_AUG = True
            print("\n" + "="*70)
            print(f"🔄 Switch augmentation → HEAVY (epoch {epoch})")
            print("="*70 + "\n")


# ==================== PRED / EVAL ====================
def decode_predictions(pred):
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    results = tf.keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][:, :MAX_LENGTH]
    return [decode_label(r.numpy()) for r in results]


def predict_single(pred_model, img_path):
    img = preprocess_image_file(img_path, augment=False)
    img = np.expand_dims(img, -1)
    img = np.transpose(img, (1, 0, 2))
    img = np.expand_dims(img, axis=0)
    pred = pred_model.predict(img, verbose=0)
    return decode_predictions(pred)[0]


def evaluate_accuracy(pred_model, images, labels, n=300):
    correct = 0
    total = min(n, len(images))
    for img_path, true_label in zip(images[:total], labels[:total]):
        try:
            if predict_single(pred_model, img_path) == true_label:
                correct += 1
        except:
            pass
    return (correct / total) * 100


# ==================== TRAIN ====================
def train_model():
    global USE_HEAVY_AUG

    print(f"\n{'='*70}")
    print(f"🎯 ENTRENANDO {CAPTCHA_NAME.upper()} (desde v2 + AUG PROGRESIVO)")
    print(f"{'='*70}\n")

    images, labels = load_dataset(DATASET_PATH, MAX_LENGTH)
    train_images, val_images, train_labels, val_labels = train_test_split(
        images, labels, test_size=VALIDATION_SPLIT, random_state=42, shuffle=True
    )

    print(f"\n📂 Train: {len(train_images)} | Val: {len(val_images)}")
    print(f"🧠 Base pred model (v2): {BASE_PRED_MODEL_PATH}")
    print(f"🔧 LR={LEARNING_RATE}, batch={BATCH_SIZE}, switch_epoch={AUG_SWITCH_EPOCH}\n")

    USE_HEAVY_AUG = False
    train_imgs, train_lbls, train_inp_len, train_lbl_len = prepare_dataset_arrays(train_images, train_labels, augment=True)
    val_imgs, val_lbls, val_inp_len, val_lbl_len = prepare_dataset_arrays(val_images, val_labels, augment=False)

    model_full, model_pred = build_model_like_original(len(CHARACTERS))

    # Transfer learning desde v2_pred
    if os.path.exists(BASE_PRED_MODEL_PATH):
        src_pred = keras.models.load_model(BASE_PRED_MODEL_PATH, compile=False, safe_mode = False)
        copied = transfer_weights_from_v2pred(src_pred, model_pred)
        if copied == 0:
            print("[TL] ⚠️ No se copió nada. Eso indica que tu v2_pred no coincide en arquitectura/shapes.")
    else:
        print(f"⚠️ No existe {BASE_PRED_MODEL_PATH}. Entrenando desde cero.")

    model_full.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss=lambda y_true, y_pred: y_pred
    )

    callbacks = [
        ProgressiveAugmentation(),
        keras.callbacks.EarlyStopping(monitor="val_loss", patience=70, restore_best_weights=True, verbose=1),
        keras.callbacks.ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=25, verbose=1, min_lr=1e-7),
        keras.callbacks.ModelCheckpoint(MODEL_PATH, monitor='val_loss', save_best_only=True, verbose=1),
    ]

    print("\n🚀 Entrenando...\n")

    train_outputs = np.zeros((len(train_imgs),), dtype=np.float32)
    val_outputs = np.zeros((len(val_imgs),), dtype=np.float32)

    history = model_full.fit(
        x=[train_imgs, train_lbls, train_inp_len, train_lbl_len],
        y=train_outputs,
        validation_data=([val_imgs, val_lbls, val_inp_len, val_lbl_len], val_outputs),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )

    model_pred.save(PRED_MODEL_PATH)
    print(f"\n✅ Guardado:\n- {MODEL_PATH}\n- {PRED_MODEL_PATH}\n")

    print("📊 Evaluando (rápido)...")
    val_acc = evaluate_accuracy(model_pred, val_images, val_labels, n=300)
    train_acc = evaluate_accuracy(model_pred, train_images, train_labels, n=300)

    print(f"\n{'='*70}")
    print(f"📈 RESULTADOS")
    print(f"{'='*70}")
    print(f"   Best Val Loss: {min(history.history['val_loss']):.4f}")
    print(f"   Train Accuracy (sample): {train_acc:.1f}%")
    print(f"   Val Accuracy (sample): {val_acc:.1f}%")
    print(f"   Epochs: {len(history.history['loss'])}")
    print(f"{'='*70}\n")

    return model_pred, history


if __name__ == "__main__":
    train_model()
