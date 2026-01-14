import os
import numpy as np
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
from PIL import Image
from sklearn.model_selection import train_test_split

# ==================== CONFIG SIMPLIFICADA ====================
CAPTCHA_NAME = "grupo3"
DATASET_PATH = "./captcha_datasets/grupo3/"
IMG_WIDTH = 200
IMG_HEIGHT = 60
MAX_LENGTH = 4
CHARACTERS = "0123456789"

BATCH_SIZE = 16
EPOCHS = 100
LEARNING_RATE = 0.0001
VALIDATION_SPLIT = 0.2

MODEL_DIR = "models/"
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_PATH = os.path.join(MODEL_DIR, f"captcha_{CAPTCHA_NAME}_simple.keras")

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

# ==================== PREPROCESAMIENTO MINIMALISTA ====================
def preprocess_image_file(img_path):
    """
    Preprocesamiento MÍNIMO - solo resize y normalización
    """
    img = Image.open(img_path).convert('L')  # Solo grayscale
    img = img.resize((IMG_WIDTH, IMG_HEIGHT))
    img = np.array(img).astype(np.float32) / 255.0
    return img

# ==================== CARGA ====================
def load_dataset(dataset_path, max_length):
    images = []
    labels = []
    
    for img_path in Path(dataset_path).glob("*.*"):
        label = img_path.stem
        
        if '_' in label:
            continue
        
        if not label.isdigit():
            continue
        if len(label) != max_length:
            continue
        
        images.append(str(img_path))
        labels.append(label)
    
    print(f"\n✅ Dataset: {len(images)} imágenes válidas")
    return images, labels

def prepare_dataset_arrays(images, labels):
    print(f"\n📦 Cargando {len(images)} imágenes...")
    all_images = []
    all_labels = []
    
    for i, (img_path, label_str) in enumerate(zip(images, labels)):
        img = preprocess_image_file(img_path)
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

# ==================== MODELO INTERMEDIO ====================
def build_model(num_chars):
    input_img = layers.Input(shape=(IMG_WIDTH, IMG_HEIGHT, 1), name="image", dtype="float32")
    labels = layers.Input(name="label", shape=(None,), dtype="float32")
    input_length = layers.Input(name='input_length', shape=[1], dtype='int64')
    label_length = layers.Input(name='label_length', shape=[1], dtype='int64')
    
    # CNN intermedio (no muy profundo)
    x = layers.Conv2D(64, (3, 3), activation="relu", padding="same")(input_img)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    
    x = layers.Conv2D(128, (3, 3), activation="relu", padding="same")(x)
    x = layers.BatchNormalization()(x)
    x = layers.MaxPooling2D((2, 2))(x)
    
    x = layers.Conv2D(256, (3, 3), activation="relu", padding="same")(x)
    x = layers.BatchNormalization()(x)
    
    # Reshape
    new_shape = ((IMG_WIDTH // 4), (IMG_HEIGHT // 4) * 256)
    x = layers.Reshape(target_shape=new_shape)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    
    # RNN simple
    x = layers.Bidirectional(layers.LSTM(128, return_sequences=True, dropout=0.2))(x)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True, dropout=0.2))(x)
    
    # Output
    output = layers.Dense(num_chars + 1, activation="softmax", name="output")(x)
    
    # CTC loss
    loss_out = layers.Lambda(
        lambda args: tf.keras.backend.ctc_batch_cost(args[0], args[1], args[2], args[3]),
        output_shape=(1,),
        name='ctc_loss'
    )([labels, output, input_length, label_length])
    
    model = keras.models.Model(
        inputs=[input_img, labels, input_length, label_length], 
        outputs=loss_out
    )
    
    return model, input_img, output

# ==================== PREDICCIÓN ====================
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
    img = preprocess_image_file(img_path)
    img = np.expand_dims(img, -1)
    img = np.transpose(img, (1, 0, 2))
    img = np.expand_dims(img, axis=0)
    
    pred = pred_model.predict(img, verbose=0)
    pred_text = decode_predictions(pred)[0]
    return pred_text

def evaluate_accuracy(pred_model, images, labels):
    correct = 0
    total = min(50, len(images))
    for img_path, true_label in zip(images[:total], labels[:total]):
        try:
            pred_label = predict_single(pred_model, img_path)
            if pred_label == true_label:
                correct += 1
        except:
            pass
    return (correct / total) * 100

# ==================== ENTRENAMIENTO ====================
def train_model():
    print(f"\n{'='*70}")
    print(f"🎯 ENTRENANDO MODELO SIMPLE: {CAPTCHA_NAME.upper()}")
    print(f"{'='*70}\n")
    
    images, labels = load_dataset(DATASET_PATH, MAX_LENGTH)
    
    if len(images) < 100:
        print("⚠️  Dataset muy pequeño.")
        return None, None
    
    train_images, val_images, train_labels, val_labels = train_test_split(
        images, labels, test_size=VALIDATION_SPLIT, random_state=42, shuffle=True
    )
    
    print(f"\n📂 Train: {len(train_images)} | Val: {len(val_images)}")
    
    train_imgs, train_lbls, train_inp_len, train_lbl_len = prepare_dataset_arrays(
        train_images, train_labels
    )
    val_imgs, val_lbls, val_inp_len, val_lbl_len = prepare_dataset_arrays(
        val_images, val_labels
    )
    
    model, input_img, output_layer = build_model(len(CHARACTERS))
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=LEARNING_RATE),
        loss=lambda y_true, y_pred: y_pred
    )
    
    print(f"\n🏗️  Arquitectura:")
    model.summary()
    
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=15,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=5,
            verbose=1,
            min_lr=1e-7
        ),
        keras.callbacks.ModelCheckpoint(
            MODEL_PATH,
            monitor='val_loss',
            save_best_only=True,
            verbose=1
        )
    ]
    
    print(f"\n🚀 Entrenando...\n")
    
    train_outputs = np.zeros((len(train_imgs),), dtype=np.float32)
    val_outputs = np.zeros((len(val_imgs),), dtype=np.float32)
    
    history = model.fit(
        x=[train_imgs, train_lbls, train_inp_len, train_lbl_len],
        y=train_outputs,
        validation_data=([val_imgs, val_lbls, val_inp_len, val_lbl_len], val_outputs),
        batch_size=BATCH_SIZE,
        epochs=EPOCHS,
        callbacks=callbacks,
        verbose=1
    )
    
    pred_model = keras.models.Model(inputs=input_img, outputs=output_layer)
    pred_model.save(MODEL_PATH.replace('.keras', '_pred.keras'))
    
    print(f"\n✅ Modelos guardados")
    
    print("\n📊 Evaluando...")
    val_acc = evaluate_accuracy(pred_model, val_images, val_labels)
    train_acc = evaluate_accuracy(pred_model, train_images, train_labels)
    
    print(f"\n{'='*70}")
    print(f"📈 RESULTADOS")
    print(f"{'='*70}")
    print(f"   Val Loss: {min(history.history['val_loss']):.4f}")
    print(f"   Train Accuracy: {train_acc:.1f}%")
    print(f"   Val Accuracy: {val_acc:.1f}%")
    print(f"   Epochs: {len(history.history['loss'])}")
    print(f"{'='*70}\n")
    
    print("🔍 Muestras de validación:")
    for i in np.random.choice(len(val_images), min(10, len(val_images)), replace=False):
        pred = predict_single(pred_model, val_images[i])
        real = val_labels[i]
        status = "✅" if pred == real else "❌"
        print(f"   {status} Pred: '{pred}' | Real: '{real}'")
    
    return pred_model, history

if __name__ == "__main__":
    model, history = train_model()
