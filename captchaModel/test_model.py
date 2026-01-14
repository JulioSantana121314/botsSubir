# test_grupo3_v3.py - Script para probar modelo V3 Progressive
import os
import numpy as np
from pathlib import Path
import tensorflow as tf
from tensorflow import keras
from PIL import Image
import random

# ==================== CONFIGURACIÓN ====================
MODEL_PATH = "models/captcha_grupo3_v3_progressive_pred.keras"
TEST_IMAGES_PATH = "captcha_datasets/grupo3/"  # O carpeta específica de test

IMG_WIDTH = 200
IMG_HEIGHT = 60
MAX_LENGTH = 4
CHARACTERS = "0123456789"

char_to_num_dict = {char: idx for idx, char in enumerate(CHARACTERS)}
num_to_char_dict = {idx: char for idx, char in enumerate(CHARACTERS)}

def decode_label(label_indices):
    result = []
    for idx in label_indices:
        if 0 <= idx < len(CHARACTERS):
            result.append(num_to_char_dict[idx])
    return ''.join(result)

def preprocess_image_file(img_path):
    """Preprocesar imagen sin augmentation"""
    img = Image.open(img_path).convert('L')
    img = img.resize((IMG_WIDTH, IMG_HEIGHT))
    img_array = np.array(img).astype(np.float32) / 255.0
    
    # Expandir dimensiones y transponer
    img_array = np.expand_dims(img_array, -1)
    img_array = np.transpose(img_array, (1, 0, 2))
    
    return img_array

def preprocess_image_bytes(img_bytes):
    """Preprocesar imagen desde bytes (para producción)"""
    from io import BytesIO
    img = Image.open(BytesIO(img_bytes)).convert('L')
    img = img.resize((IMG_WIDTH, IMG_HEIGHT))
    img_array = np.array(img).astype(np.float32) / 255.0
    
    img_array = np.expand_dims(img_array, -1)
    img_array = np.transpose(img_array, (1, 0, 2))
    
    return img_array

def decode_predictions(pred):
    """Decodificar predicciones CTC"""
    input_len = np.ones(pred.shape[0]) * pred.shape[1]
    results = tf.keras.backend.ctc_decode(pred, input_length=input_len, greedy=True)[0][0][:, :MAX_LENGTH]
    
    output_text = []
    for res in results:
        indices = res.numpy()
        text = decode_label(indices)
        output_text.append(text)
    return output_text

def predict_single(model, img_path):
    """Predecir un solo captcha desde archivo"""
    img = preprocess_image_file(img_path)
    img = np.expand_dims(img, axis=0)
    
    pred = model.predict(img, verbose=0)
    pred_text = decode_predictions(pred)[0]
    
    return pred_text

def predict_batch(model, img_paths):
    """Predecir múltiples captchas (más rápido)"""
    images = []
    for img_path in img_paths:
        img = preprocess_image_file(img_path)
        images.append(img)
    
    images = np.array(images, dtype=np.float32)
    
    pred = model.predict(images, verbose=0)
    pred_texts = decode_predictions(pred)
    
    return pred_texts

def get_confidence_score(model, img_path):
    """Calcular score de confianza de la predicción"""
    img = preprocess_image_file(img_path)
    img = np.expand_dims(img, axis=0)
    
    pred = model.predict(img, verbose=0)
    
    # Calcular confianza como promedio de probabilidades máximas
    max_probs = np.max(pred[0], axis=1)
    confidence = np.mean(max_probs)
    
    pred_text = decode_predictions(pred)[0]
    
    return pred_text, confidence

def test_dataset(model, dataset_path, sample_size=None):
    """Evaluar modelo en dataset completo o muestra"""
    print(f"\n{'='*70}")
    print(f"📊 EVALUACIÓN DEL MODELO")
    print(f"{'='*70}\n")
    
    # Cargar imágenes
    images = []
    labels = []
    
    for img_path in Path(dataset_path).glob("*.*"):
        label = img_path.stem
        
        # Filtrar solo captchas válidos (4 dígitos)
        if '_' in label or not label.isdigit() or len(label) != MAX_LENGTH:
            continue
        
        images.append(str(img_path))
        labels.append(label)
    
    print(f"✅ Dataset cargado: {len(images)} imágenes")
    
    # Si se especifica sample_size, tomar muestra aleatoria
    if sample_size and sample_size < len(images):
        indices = random.sample(range(len(images)), sample_size)
        images = [images[i] for i in indices]
        labels = [labels[i] for i in indices]
        print(f"📦 Usando muestra de {sample_size} imágenes\n")
    else:
        print()
    
    # Evaluar
    correct = 0
    total = len(images)
    errors = []
    predictions_detail = []
    
    print(f"🔍 Evaluando {total} imágenes...\n")
    
    for i, (img_path, true_label) in enumerate(zip(images, labels)):
        try:
            pred_label, confidence = get_confidence_score(model, img_path)
            
            is_correct = pred_label == true_label
            
            if is_correct:
                correct += 1
            else:
                errors.append({
                    'path': img_path,
                    'pred': pred_label,
                    'true': true_label,
                    'confidence': confidence
                })
            
            predictions_detail.append({
                'path': img_path,
                'pred': pred_label,
                'true': true_label,
                'correct': is_correct,
                'confidence': confidence
            })
            
            if (i + 1) % 50 == 0:
                print(f"   {i+1}/{total}...")
                
        except Exception as e:
            print(f"❌ Error en {img_path}: {e}")
            errors.append({
                'path': img_path,
                'pred': 'ERROR',
                'true': true_label,
                'confidence': 0.0
            })
    
    accuracy = (correct / total) * 100
    
    # Calcular confusiones
    confusions = {}
    for err in errors:
        if err['pred'] != 'ERROR' and len(err['pred']) == len(err['true']):
            for p, t in zip(err['pred'], err['true']):
                if p != t:
                    key = f"{t}→{p}"
                    confusions[key] = confusions.get(key, 0) + 1
    
    # Calcular confianza promedio
    avg_confidence_correct = np.mean([p['confidence'] for p in predictions_detail if p['correct']])
    avg_confidence_incorrect = np.mean([p['confidence'] for p in predictions_detail if not p['correct']])
    
    # Mostrar resultados
    print(f"\n{'='*70}")
    print(f"📈 RESULTADOS")
    print(f"{'='*70}")
    print(f"   Total imágenes:        {total}")
    print(f"   Correctas:             {correct}")
    print(f"   Incorrectas:           {total - correct}")
    print(f"   Accuracy:              {accuracy:.2f}%")
    print(f"   ")
    print(f"   Confianza (correctas): {avg_confidence_correct:.4f}")
    print(f"   Confianza (incorrectas): {avg_confidence_incorrect:.4f}")
    print(f"{'='*70}\n")
    
    if confusions:
        print("🔍 Top 10 confusiones más frecuentes:")
        for confusion, count in sorted(confusions.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {confusion}: {count} veces")
        print()
    
    # Mostrar ejemplos aleatorios
    print("📋 20 ejemplos aleatorios:")
    sample_predictions = random.sample(predictions_detail, min(20, len(predictions_detail)))
    
    for p in sample_predictions:
        status = "✅" if p['correct'] else "❌"
        print(f"   {status} Pred: '{p['pred']}' | Real: '{p['true']}' | Confianza: {p['confidence']:.3f}")
    
    # Mostrar errores con baja confianza (potencialmente difíciles)
    if errors:
        print("\n⚠️  Top 10 errores con MENOR confianza (captchas difíciles):")
        errors_sorted = sorted(errors, key=lambda x: x.get('confidence', 0))[:10]
        for err in errors_sorted:
            print(f"   Pred: '{err['pred']}' | Real: '{err['true']}' | Confianza: {err.get('confidence', 0):.3f}")
            print(f"      Archivo: {Path(err['path']).name}")
        print()
    
    return accuracy, errors, predictions_detail

def test_single_image(model, img_path):
    """Probar una sola imagen con detalles"""
    print(f"\n{'='*70}")
    print(f"🔍 PRUEBA DE IMAGEN INDIVIDUAL")
    print(f"{'='*70}\n")
    print(f"   Archivo: {Path(img_path).name}")
    
    # Obtener label real del nombre del archivo
    true_label = Path(img_path).stem
    if '_' in true_label:
        true_label = true_label.split('_')[0]
    
    # Predecir
    pred_label, confidence = get_confidence_score(model, img_path)
    
    is_correct = pred_label == true_label if true_label.isdigit() else None
    
    print(f"   Label real:      {true_label}")
    print(f"   Predicción:      {pred_label}")
    print(f"   Confianza:       {confidence:.4f}")
    
    if is_correct is not None:
        status = "✅ CORRECTA" if is_correct else "❌ INCORRECTA"
        print(f"   Resultado:       {status}")
    
    print(f"{'='*70}\n")
    
    return pred_label, confidence

def batch_predict_directory(model, input_dir, output_file="predictions.txt"):
    """Predecir todos los captchas en un directorio y guardar resultados"""
    print(f"\n{'='*70}")
    print(f"📁 PREDICCIÓN EN LOTE")
    print(f"{'='*70}\n")
    
    # Cargar todas las imágenes
    image_files = []
    for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp']:
        image_files.extend(Path(input_dir).glob(ext))
    
    if not image_files:
        print(f"❌ No se encontraron imágenes en {input_dir}")
        return
    
    print(f"✅ Encontradas {len(image_files)} imágenes")
    print(f"🔄 Prediciendo...\n")
    
    results = []
    
    for i, img_path in enumerate(image_files):
        try:
            pred_label, confidence = get_confidence_score(model, str(img_path))
            results.append({
                'file': img_path.name,
                'prediction': pred_label,
                'confidence': confidence
            })
            
            if (i + 1) % 50 == 0:
                print(f"   {i+1}/{len(image_files)}...")
                
        except Exception as e:
            print(f"❌ Error en {img_path.name}: {e}")
            results.append({
                'file': img_path.name,
                'prediction': 'ERROR',
                'confidence': 0.0
            })
    
    # Guardar resultados
    with open(output_file, 'w') as f:
        f.write("Archivo,Predicción,Confianza\n")
        for r in results:
            f.write(f"{r['file']},{r['prediction']},{r['confidence']:.4f}\n")
    
    print(f"\n✅ Resultados guardados en: {output_file}")
    print(f"   Total predicciones: {len(results)}")
    print(f"   Errores: {sum(1 for r in results if r['prediction'] == 'ERROR')}")
    
    # Estadísticas de confianza
    confidences = [r['confidence'] for r in results if r['prediction'] != 'ERROR']
    if confidences:
        print(f"   Confianza promedio: {np.mean(confidences):.4f}")
        print(f"   Confianza mínima: {np.min(confidences):.4f}")
        print(f"   Confianza máxima: {np.max(confidences):.4f}")
    
    print(f"{'='*70}\n")
    
    return results

def main():
    print("\n" + "="*70)
    print("🎯 TEST MODELO V3 PROGRESSIVE - Grupo 3")
    print("="*70)
    
    # Cargar modelo
    print(f"\n🔄 Cargando modelo: {MODEL_PATH}")
    
    if not os.path.exists(MODEL_PATH):
        print(f"❌ ERROR: Modelo no encontrado en {MODEL_PATH}")
        print(f"\nModelos disponibles:")
        models_dir = Path("models")
        if models_dir.exists():
            for model_file in models_dir.glob("*.keras"):
                print(f"   - {model_file}")
        return
    
    try:
        model = keras.models.load_model(MODEL_PATH)
        print(f"✅ Modelo cargado correctamente\n")
    except Exception as e:
        print(f"❌ Error cargando modelo: {e}")
        return
    
    # Menú de opciones
    while True:
        print("="*70)
        print("OPCIONES:")
        print("="*70)
        print("1. Evaluar dataset completo")
        print("2. Evaluar muestra aleatoria (rápido)")
        print("3. Probar imagen individual")
        print("4. Predicción en lote (directorio → archivo)")
        print("5. Probar 10 imágenes aleatorias")
        print("6. Salir")
        print("="*70)
        
        opcion = input("\nSelecciona una opción (1-6): ").strip()
        
        if opcion == "1":
            # Evaluar dataset completo
            accuracy, errors, details = test_dataset(model, TEST_IMAGES_PATH)
            
        elif opcion == "2":
            # Evaluar muestra
            sample_size = int(input("Tamaño de muestra (ej: 100): "))
            accuracy, errors, details = test_dataset(model, TEST_IMAGES_PATH, sample_size=sample_size)
            
        elif opcion == "3":
            # Imagen individual
            img_path = input("Ruta de la imagen: ").strip()
            if os.path.exists(img_path):
                test_single_image(model, img_path)
            else:
                print(f"❌ Archivo no encontrado: {img_path}")
            
        elif opcion == "4":
            # Predicción en lote
            input_dir = input("Directorio de imágenes: ").strip()
            output_file = input("Archivo de salida (default: predictions.txt): ").strip()
            if not output_file:
                output_file = "predictions.txt"
            
            if os.path.exists(input_dir):
                batch_predict_directory(model, input_dir, output_file)
            else:
                print(f"❌ Directorio no encontrado: {input_dir}")
            
        elif opcion == "5":
            # 10 imágenes aleatorias
            images = list(Path(TEST_IMAGES_PATH).glob("*.*"))
            images = [img for img in images if img.suffix.lower() in ['.png', '.jpg', '.jpeg', '.bmp']]
            
            if len(images) >= 10:
                sample_images = random.sample(images, 10)
                
                print(f"\n{'='*70}")
                print(f"🎲 10 IMÁGENES ALEATORIAS")
                print(f"{'='*70}\n")
                
                for img_path in sample_images:
                    true_label = img_path.stem
                    if '_' in true_label:
                        true_label = true_label.split('_')[0]
                    
                    pred_label, confidence = get_confidence_score(model, str(img_path))
                    
                    is_correct = pred_label == true_label if true_label.isdigit() and len(true_label) == 4 else None
                    status = "✅" if is_correct else ("❌" if is_correct is False else "❓")
                    
                    print(f"{status} {img_path.name}")
                    print(f"   Real: {true_label} | Pred: {pred_label} | Conf: {confidence:.3f}\n")
            else:
                print(f"❌ No hay suficientes imágenes en {TEST_IMAGES_PATH}")
            
        elif opcion == "6":
            print("\n👋 ¡Hasta luego!")
            break
        
        else:
            print("❌ Opción inválida")
        
        print()

if __name__ == "__main__":
    main()
