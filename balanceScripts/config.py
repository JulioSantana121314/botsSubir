import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # 0=ALL, 1=INFO, 2=WARNING, 3=ERROR
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'  # Desactivar mensajes oneDNN
from dotenv import load_dotenv
import logging
import threading
from queue import Queue, Empty
import requests
import gspread
from pymongo import MongoClient
from google.oauth2.service_account import Credentials
from selenium import webdriver
from PIL import Image
import cv2
import numpy as np
import re
import time
from datetime import datetime
from pathlib import Path
import inspect
import sys

load_dotenv()

#### === Logger setup === ####
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
BASE_FOLDER = os.path.abspath(os.path.dirname(__file__))
LOG_FOLDER = os.path.join(BASE_FOLDER, "logs")
DEFAULT_LOG_FILE = os.path.join(LOG_FOLDER, 'bot_universal.log')


def get_logger(module_name, filename=None):
    logger = logging.getLogger(module_name)
    if not logger.handlers:
        log_file = filename or DEFAULT_LOG_FILE
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter(LOG_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
    return logger


def log_exception(logger, custom_message=None):
    import sys
    import traceback
    exc_type, exc_value, exc_tb = sys.exc_info()
    exception_details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    if custom_message:
        logger.warning(f"{custom_message}\n{exception_details}")
    else:
        logger.warning(f"Exception occurred:\n{exception_details}")


logger = get_logger(__name__)


#### === Carpetas de organización === ####
CAPTCHA_FOLDER = os.path.join(BASE_FOLDER, "captchas")
EVIDENCE_FOLDER = os.path.join(BASE_FOLDER, "screenshots")
for folder in [LOG_FOLDER, CAPTCHA_FOLDER, EVIDENCE_FOLDER]:
    os.makedirs(folder, exist_ok=True)


#### === Importa tu mapping de grupos === ####
sys.path.insert(0, str(Path(__file__).parent.parent))
from diccionario import WEBSITES, USERS_GRUPOS, CAPTCHA_GRUPOS


#### === Timestamp helper === ####
def get_current_timestamp():
    """Devuelve timestamp actual en formato 'YYYY-MM-DD HH:MM:SS'"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#### === Auto-detección del website y tracking de captchas === ####
_captcha_data = {}  # {website_name: {'path': str, 'solution': str}}


def _detectar_website_desde_caller():
    """
    Auto-detecta el nombre del website buscando la variable WEBSITE_NAME
    en el stack de llamadas del caller.
    """
    try:
        for frame_info in inspect.stack():
            frame_locals = frame_info.frame.f_locals
            frame_globals = frame_info.frame.f_globals
            
            if 'WEBSITE_NAME' in frame_locals:
                return frame_locals['WEBSITE_NAME']
            if 'WEBSITE_NAME' in frame_globals:
                return frame_globals['WEBSITE_NAME']
        
        logger.warning("[CAPTCHA] No se pudo auto-detectar WEBSITE_NAME desde el caller")
        return None
    except Exception as e:
        logger.warning(f"[CAPTCHA] Error en auto-detección de website: {e}")
        return None


def get_captcha_folder_for_website(website_name):
    """
    Crea y retorna la carpeta específica para captchas de un website.
    """
    folder_name = website_name.replace(" ", "_").replace("/", "_")
    website_captcha_folder = os.path.join(CAPTCHA_FOLDER, folder_name)
    os.makedirs(website_captcha_folder, exist_ok=True)
    return website_captcha_folder


def _registrar_captcha(website_name, captcha_path, solucion):
    """Registra internamente el captcha resuelto para renombrado posterior"""
    global _captcha_data
    if website_name and solucion:
        _captcha_data[website_name] = {
            'path': captcha_path,
            'solution': solucion
        }
        logger.info(f"[CAPTCHA-TRACK] Registrado captcha para {website_name}: {solucion}")


def _renombrar_captcha_automatico(website_name):
    """Renombra automáticamente el captcha cuando se registra un balance exitoso"""
    global _captcha_data
    
    if website_name not in _captcha_data:
        return  # No hay captcha pendiente
    
    data = _captcha_data[website_name]
    old_path = data['path']
    solucion = data['solution']
    
    if not os.path.exists(old_path):
        logger.warning(f"[CAPTCHA-RENAME] Archivo no encontrado: {old_path}")
        del _captcha_data[website_name]
        return
    
    try:
        directorio = os.path.dirname(old_path)
        extension = os.path.splitext(old_path)[1]
        
        # Nombre = solo la solución del captcha
        nuevo_nombre = f"{solucion}{extension}"
        new_path = os.path.join(directorio, nuevo_nombre)
        
        # Si ya existe, agregar contador secuencial
        contador = 1
        while os.path.exists(new_path):
            nuevo_nombre = f"{solucion}_{contador}{extension}"
            new_path = os.path.join(directorio, nuevo_nombre)
            contador += 1
        
        os.rename(old_path, new_path)
        logger.info(f"[CAPTCHA-RENAME] ✓ Renombrado: {os.path.basename(old_path)} → {nuevo_nombre}")
        
        # Limpiar tracking
        del _captcha_data[website_name]
        
    except Exception as e:
        logger.error(f"[CAPTCHA-RENAME] Error al renombrar captcha: {e}")
        log_exception(logger, "Error en _renombrar_captcha_automatico")


def detectar_grupo_captcha(website_name):
    """
    Detecta qué grupo de captcha usar basándose en el website.
    
    Returns:
        str: 'grupo1', 'grupo2', 'grupo3', o None si debe usar 2captcha
    """
    if not website_name:
        return None
    
    # Buscar en cada grupo
    for grupo_id, websites in CAPTCHA_GRUPOS.items():
        if website_name in websites:
            logger.info(f"[CAPTCHA-DETECT] {website_name} → {grupo_id}")
            return grupo_id
    
    # No encontrado en ningún grupo
    logger.info(f"[CAPTCHA-DETECT] {website_name} → 2captcha (no en grupos)")
    return None


#### === Opciones Chrome/Bots === ####
CHROME_HEADLESS = True
CHROME_WINDOW_SIZE = (900, 1300)
CHROME_LANG = "en-US"


def get_chrome_driver():
    options = webdriver.ChromeOptions()
    if CHROME_HEADLESS:
        options.add_argument("--headless")
    options.add_argument(f"--window-size={CHROME_WINDOW_SIZE[0]},{CHROME_WINDOW_SIZE[1]}")
    options.add_argument(f"--lang={CHROME_LANG}")
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(*CHROME_WINDOW_SIZE)
    return driver


#### === Captcha config === ####
API_KEY_2CAPTCHA = os.getenv('API_KEY_2CAPTCHA')
KERAS_PREDICT_TIMEOUT = int(os.getenv('KERAS_PREDICT_TIMEOUT', '10'))

# ✅ CONFIGURACIÓN ACTUALIZADA CON LOS MODELOS V3
CAPTCHA_CONFIG = {
    "grupo1": {
        "model_path": os.path.join(BASE_FOLDER, r"..\captchaModel\models\captcha_grupo1_v2_pred.keras"),
        "img_width": 200,
        "img_height": 50,
        "max_length": 5,
        "characters": "0123456789"
    },
    "grupo2": {
        "model_path": os.path.join(BASE_FOLDER, r"..\captchaModel\models\captcha_grupo2_v3_progressive_pred.keras"),
        "img_width": 200,
        "img_height": 50,
        "max_length": 4,
        "characters": "0123456789"
    },
    "grupo3": {
        # ✅ MODELO V3 PROGRESSIVE (95-96% accuracy)
        "model_path": os.path.join(BASE_FOLDER, r"..\captchaModel\models\captcha_grupo3_v4_progressive_pred.keras"),
        "img_width": 200,
        "img_height": 60,  # ✅ Grupo 3 usa 60px de altura
        "max_length": 4,    # ✅ Grupo 3 usa 4 dígitos
        "characters": "0123456789"
    }
}

# ✅ CONFIGURACIÓN DE REINTENTOS POR GRUPO
CAPTCHA_MAX_RETRIES = {
    "grupo1": 3,
    "grupo2": 3,
    "grupo3": 2  # Grupo 3 tiene mejor accuracy, menos reintentos necesarios
}


# Diccionario para almacenar modelos cargados
keras_models = {}


def cargar_modelo_keras(grupo_id):
    """
    Carga el modelo Keras para un grupo específico.
    
    Args:
        grupo_id: 'grupo1', 'grupo2', o 'grupo3'
    
    Returns:
        dict: {'model': model_keras, 'num_to_char': dict} o None si falla
    """
    global keras_models
    
    # Si ya está cargado, retornarlo
    if grupo_id in keras_models:
        return keras_models[grupo_id]
    
    if grupo_id not in CAPTCHA_CONFIG:
        logger.error(f"[CAPTCHA-KERAS] Grupo '{grupo_id}' no existe en CAPTCHA_CONFIG")
        return None
    
    config_grupo = CAPTCHA_CONFIG[grupo_id]
    model_path = config_grupo["model_path"]
    characters = config_grupo["characters"]
    
    try:
        import tensorflow as tf
        from tensorflow import keras
        
        logger.info(f"[CAPTCHA-KERAS] Cargando modelo {grupo_id} desde: {model_path}")
        
        if not os.path.exists(model_path):
            logger.error(f"[CAPTCHA-KERAS] ❌ Archivo no encontrado: {model_path}")
            return None
        
        model = keras.models.load_model(model_path, compile=False)
        num_to_char_dict = {idx: char for idx, char in enumerate(characters)}
        
        keras_models[grupo_id] = {
            'model': model,
            'num_to_char': num_to_char_dict,
            'config': config_grupo
        }
        
        logger.info(f"[CAPTCHA-KERAS] ✅ Modelo {grupo_id} cargado exitosamente")
        logger.info(f"[CAPTCHA-KERAS]    Config: {config_grupo['img_width']}x{config_grupo['img_height']}, max_length={config_grupo['max_length']}")
        
        return keras_models[grupo_id]
        
    except Exception as e:
        logger.error(f"[CAPTCHA-KERAS] ❌ Error al cargar modelo {grupo_id}")
        log_exception(logger, f"Error al cargar modelo Keras {grupo_id}")
        return None


# Cargar modelos al inicio
logger.info("="*70)
logger.info("🔄 Inicializando modelos Keras de captcha...")
for grupo in ["grupo1", "grupo2", "grupo3"]:
    result = cargar_modelo_keras(grupo)
    if result:
        logger.info(f"   ✅ {grupo} listo")
    else:
        logger.warning(f"   ⚠️  {grupo} no disponible")
logger.info("="*70)


def preprocesar_captcha(pil_img):
    """
    Preprocesa la imagen del captcha para mejorar OCR.
    Devuelve imagen en escala de grises.
    """
    try:
        # Convertir a escala de grises
        if pil_img.mode != 'L':
            pil_img = pil_img.convert('L')
        
        # Convertir a numpy array
        img_array = np.array(pil_img)
        
        # Aplicar umbralización adaptativa para mejorar contraste
        img_thresh = cv2.adaptiveThreshold(
            img_array, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        # Aplicar filtro de mediana para reducir ruido
        img_filtered = cv2.medianBlur(img_thresh, 3)
        
        # Convertir de vuelta a PIL
        return Image.fromarray(img_filtered)
    except Exception as e:
        logger.warning(f"[CAPTCHA-PREPROC] Error en preprocesamiento, usando original: {e}")
        return pil_img


def decode_keras_prediction(pred, num_to_char_dict, max_length):
    """
    Decodifica la predicción del modelo Keras usando CTC decode.
    """
    try:
        import tensorflow as tf
        
        input_len = np.ones(pred.shape[0]) * pred.shape[1]
        results = tf.keras.backend.ctc_decode(
            pred, 
            input_length=input_len, 
            greedy=True
        )[0][0][:, :max_length]
        
        output_text = []
        for res in results:
            indices = res.numpy()
            # Filtrar índices válidos
            text = ''.join([
                num_to_char_dict[idx] 
                for idx in indices 
                if 0 <= idx < len(num_to_char_dict)
            ])
            output_text.append(text)
        
        return output_text[0] if output_text else ""
    except Exception as e:
        logger.error(f"[CAPTCHA-KERAS] Error en decode_keras_prediction: {e}")
        log_exception(logger, "Error en decodificación Keras")
        return ""


def calcular_confianza_prediccion(pred):
    """
    Calcula el score de confianza de una predicción.
    Retorna el promedio de las probabilidades máximas.
    """
    try:
        max_probs = np.max(pred[0], axis=1)
        confidence = np.mean(max_probs)
        return float(confidence)
    except Exception as e:
        logger.warning(f"[CAPTCHA-KERAS] Error calculando confianza: {e}")
        return 0.0

def predict_with_timeout(model, img_array, timeout=KERAS_PREDICT_TIMEOUT):
    """
    Ejecuta model.predict() con timeout.
    Retorna (prediction, success) donde success=False si hay timeout.
    """
    result_queue = Queue()
    exception_queue = Queue()
    
    def predict_worker():
        try:
            prediction = model.predict(img_array, verbose=0)
            result_queue.put(prediction)
        except Exception as e:
            exception_queue.put(e)
    
    thread = threading.Thread(target=predict_worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        logger.warning(f"[CAPTCHA-KERAS] ⏱️ TIMEOUT ({timeout}s) en model.predict()")
        return None, False
    
    if not exception_queue.empty():
        exc = exception_queue.get()
        logger.error(f"[CAPTCHA-KERAS] Error en predict_worker: {exc}")
        return None, False
    
    if not result_queue.empty():
        return result_queue.get(), True
    
    return None, False

def resolver_captcha_keras_interno(image_bytes, grupo_id, captcha_path):
    """
    Resuelve captcha usando el modelo Keras del grupo especificado.
    Retorna (text, confidence, timeout_occurred)
    - timeout_occurred=True indica que debe reintentar sin contar como intento fallido
    """
    try:
        model_data = cargar_modelo_keras(grupo_id)
        if model_data is None:
            logger.error(f"[CAPTCHA-KERAS-{grupo_id.upper()}] No se pudo cargar el modelo")
            return None, 0.0, False
        
        model = model_data['model']
        num_to_char = model_data['num_to_char']
        config_grupo = model_data['config']
        
        pil_img = Image.open(captcha_path)
        pil_img_proc = preprocesar_captcha(pil_img)
        pil_img_resized = pil_img_proc.resize((config_grupo['img_width'], config_grupo['img_height']))
        
        img_array = np.array(pil_img_resized).astype(np.float32) / 255.0
        img_array = np.expand_dims(img_array, -1)
        img_array = np.transpose(img_array, (1, 0, 2))
        img_array = np.expand_dims(img_array, 0)
        
        # ✅ PREDICCIÓN CON TIMEOUT
        prediction, success = predict_with_timeout(model, img_array, timeout=KERAS_PREDICT_TIMEOUT)
        
        if not success:
            logger.warning(f"[CAPTCHA-KERAS-{grupo_id.upper()}] ⏱️ Timeout - se reintentará")
            return None, 0.0, True  # ← timeout_occurred=True
        
        confidence = calcular_confianza_prediccion(prediction)
        text = decode_keras_prediction(prediction, num_to_char, config_grupo['max_length'])
        
        expected_length = config_grupo['max_length']
        
        if text and text.isdigit():
            if expected_length - 1 <= len(text) <= expected_length + 1:
                logger.info(f"[CAPTCHA-KERAS-{grupo_id.upper()}] ✓ Resultado: '{text}' (confianza: {confidence:.3f})")
                return text, confidence, False
            else:
                logger.warning(f"[CAPTCHA-KERAS-{grupo_id.upper()}] ⚠️ Longitud inválida: '{text}' (esperado: ~{expected_length})")
                return None, confidence, False
        else:
            logger.warning(f"[CAPTCHA-KERAS-{grupo_id.upper()}] ⚠️ Resultado inválido: '{text}'")
            return None, confidence, False
            
    except Exception as e:
        logger.error(f"[CAPTCHA-KERAS-{grupo_id.upper()}] ❌ Error al resolver captcha")
        log_exception(logger, f"Error en resolver_captcha_keras_interno {grupo_id}")
        return None, 0.0, False


def resolver_captcha_2captcha_api(image_bytes, captcha_path, website_name):
    """
    Resuelve captcha usando servicio 2captcha.
    """
    try:
        logger.info(f"[CAPTCHA-2CAPTCHA] Enviando captcha a 2captcha...")
        
        with open(captcha_path, "rb") as fp:
            files = {'file': fp}
            data = {'key': API_KEY_2CAPTCHA, 'method': 'post', 'json': 1}
            resp = requests.post('http://2captcha.com/in.php', files=files, data=data, timeout=30).json()
            
            if 'request' not in resp:
                logger.error(f"[CAPTCHA-2CAPTCHA] Respuesta inválida: {resp}")
                return None
            
            captcha_id = resp['request']
        
        logger.info(f"[CAPTCHA-2CAPTCHA] ID recibido: {captcha_id}")
        
        # Esperar resolución
        for intent in range(18):
            time.sleep(2)
            res = requests.get(
                f"http://2captcha.com/res.php?key={API_KEY_2CAPTCHA}&action=get&id={captcha_id}&json=1",
                timeout=30
            ).json()
            
            if res['status'] == 1:
                result = res['request']
                logger.info(f"[CAPTCHA-2CAPTCHA] ✅ Resultado: {result}")
                # Registrar para renombrado
                _registrar_captcha(website_name, captcha_path, result)
                return result
            
            if intent % 3 == 0:
                logger.info(f"[CAPTCHA-2CAPTCHA] Esperando... intento {intent+1}/18")
        
        logger.warning("[CAPTCHA-2CAPTCHA] ⚠️ Timeout tras 18 intentos")
        return None
        
    except Exception as e:
        logger.error("[CAPTCHA-2CAPTCHA] ❌ Error al resolver captcha")
        log_exception(logger, "Error en resolver_captcha_2captcha_api")
        return None


#### === ✅ FUNCIÓN PRINCIPAL - NO CAMBIAR FIRMA === ####
def resolver_captcha_2captcha(image_bytes, filename_prefix='captcha'):
    """
    Función unificada para resolver captchas.
    
    ✅ LÓGICA ACTUALIZADA:
    1. Detecta grupo del website automáticamente
    2. Si tiene grupo asignado: Usa modelo Keras con reintentos (3 intentos)
    3. Si NO tiene grupo asignado: Usa 2captcha directamente
    4. Si modelo falla tras reintentos: Fallback a 2captcha
    
    Args:
        image_bytes: Bytes de la imagen del captcha
        filename_prefix: Prefijo para el nombre del archivo
    
    Returns:
        str: Texto del captcha resuelto o None si falla
    """
    website_name = _detectar_website_desde_caller()
    ts = int(time.time())
    
    if website_name:
        captcha_folder = get_captcha_folder_for_website(website_name)
    else:
        captcha_folder = CAPTCHA_FOLDER
    
    captcha_path = os.path.join(captcha_folder, f"{filename_prefix}_{ts}.png")
    
    # Guardar imagen
    try:
        with open(captcha_path, "wb") as f:
            f.write(image_bytes)
        logger.info(f"[CAPTCHA] 📸 Imagen guardada: {captcha_path}")
    except Exception as e:
        logger.error(f"[CAPTCHA] ❌ Error guardando imagen: {e}")
        return None
    
    # Detectar qué grupo de captcha usar
    grupo_id = detectar_grupo_captcha(website_name)
    
    # ===== CASO 1: Website SIN grupo asignado → 2captcha directo =====
    if grupo_id is None:
        logger.info(f"[CAPTCHA] 🌐 Website '{website_name}' sin grupo → Usando 2captcha directamente")
        return resolver_captcha_2captcha_api(image_bytes, captcha_path, website_name)
    
    # ===== CASO 2: Website CON grupo asignado → Modelo Keras con reintentos =====
    logger.info(f"[CAPTCHA] 🤖 Website '{website_name}' → Grupo {grupo_id}")
    
    max_retries = CAPTCHA_MAX_RETRIES.get(grupo_id, 3)
    
    for intento in range(1, max_retries + 1):
        logger.info(f"[CAPTCHA] Intento {intento}/{max_retries} con modelo {grupo_id}")
        
        result, confidence = resolver_captcha_keras_interno(image_bytes, grupo_id, captcha_path)
        
        if result:
            logger.info(f"[CAPTCHA] ✅ Captcha resuelto con {grupo_id} en intento {intento}: '{result}' (confianza: {confidence:.3f})")
            # Registrar para renombrado automático
            _registrar_captcha(website_name, captcha_path, result)
            return result
        else:
            logger.warning(f"[CAPTCHA] ⚠️ Intento {intento} falló (confianza: {confidence:.3f})")
            
            # Si no es el último intento, esperar un poco antes de reintentar
            if intento < max_retries:
                time.sleep(0.5)
    
    # ===== CASO 3: Todos los reintentos fallaron → Fallback a 2captcha =====
    logger.warning(f"[CAPTCHA] ⚠️ Modelo {grupo_id} falló tras {max_retries} intentos → Fallback a 2captcha")
    return resolver_captcha_2captcha_api(image_bytes, captcha_path, website_name)


#### === Evidencias (screenshots) === ####
def guardar_evidencia(screenshot_bytes, filename_prefix="evidence"):
    ts = int(time.time())
    screenshot_path = os.path.join(EVIDENCE_FOLDER, f"{filename_prefix}_{ts}.png")
    with open(screenshot_path, "wb") as f:
        f.write(screenshot_bytes)
    return screenshot_path


#### === Google Sheets === ####
SERVICE_ACCOUNT_FILE = os.getenv('SERVICE_ACCOUNT_FILE', '../credentials/googleKeys.json')
SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'BALANCES')
SHEET_TAB = os.getenv('SHEET_TAB', 'Balances')
EXPORT_MODE = os.getenv('EXPORT_MODE', 'MONGO')


def google_sheets_connect():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open(SPREADSHEET_NAME).worksheet(SHEET_TAB)
    return sheet


#### === MySQL Config === ####
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'plataforma_finanzas')


#### === Configuración MongoDB === ####
MONGO_URI = os.getenv('MONGO_URI')
MONGO_DB = os.getenv('MONGO_DB', 'plataforma_finanzas')
MONGO_COLLECTION = os.getenv('MONGO_COLLECTION', 'balances_bot')


def obtener_grupo_por_usuario(username):
    """Busca grupo por username, si no existe devuelve None"""
    return USERS_GRUPOS.get(username, None)


def enviar_resultado_balance(sheet, website, username, fecha=None, balance=None):
    if fecha is None:
        fecha = get_current_timestamp()
    
    grupo = obtener_grupo_por_usuario(username)
    
    # ✅ NORMALIZAR a Title Case
    website_normalized = website.strip().title()
    
    _renombrar_captcha_automatico(website)
    
    if EXPORT_MODE.upper() == "SHEET":
        pass
    elif EXPORT_MODE.upper() == "MYSQL":
        pass
    else:
        client = None
        try:
            client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=20000)
            db = client[MONGO_DB]
            collection = db[MONGO_COLLECTION]
            doc = {
                "website": website_normalized,  # ← Usar normalizado
                "username": username,
                "fecha": fecha,
                "balance": balance,
                "used_as_previous": False,
                "grupo": grupo
            }
            collection.insert_one(doc)
            logger.info(f"[MongoDB] Balance registrado: {website_normalized} | {username} | {balance} | {fecha}")
        except Exception as e:
            logger.error(f"[ERROR MongoDB] No se pudo insertar documento: {e}")
            log_exception(logger, "Error al insertar en MongoDB")
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass
