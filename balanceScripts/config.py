import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'


# ✅ SETUP CUDA 11 ANTES DE IMPORTAR TENSORFLOW
import site
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


from dotenv import load_dotenv
import logging
import threading
from queue import Queue, Empty
import requests
import gspread
from pymongo import MongoClient
from google.oauth2.service_account import Credentials
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from PIL import Image
import cv2
import numpy as np
import gc
import re
import time
from datetime import datetime
from pathlib import Path
import inspect
import sys


load_dotenv()


#### === Logger setup optimizado === ####
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(message)s'
BASE_FOLDER = os.path.abspath(os.path.dirname(__file__))
LOG_FOLDER = os.path.join(BASE_FOLDER, "logs")
DEFAULT_LOG_FILE = os.path.join(LOG_FOLDER, 'bot_universal.log')

VERBOSE_LOGGING = False


def get_logger(module_name, filename=None):
    """
    Crea logger con configuración optimizada.
    ✅ Logs separados por website automáticamente
    
    Args:
        module_name: Nombre del módulo (ej: "MILKY WAY_bot", "ORION STARS_bot")
        filename: Ruta completa del archivo de log (opcional)
    """
    logger = logging.getLogger(module_name)
    
    # ✅ Evitar duplicar handlers si ya existe
    if logger.handlers:
        return logger
    
    # ✅ Si no se especifica filename, crear uno basado en module_name
    if filename is None:
        # Extraer nombre limpio del website (remover "_bot" si existe)
        website_name = module_name.replace("_bot", "").replace(" ", "_")
        filename = os.path.join(LOG_FOLDER, f"{website_name}.log")
    
    # File handler (archivo de log específico)
    file_handler = logging.FileHandler(filename, encoding='utf-8')
    file_formatter = logging.Formatter(LOG_FORMAT)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Console handler (sigue mostrando en consola)
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter(LOG_FORMAT)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    logger.setLevel(LOG_LEVEL)
    
    return logger


def log_exception(logger, custom_message=None):
    """Log excepciones con traceback completo"""
    import traceback
    exc_type, exc_value, exc_tb = sys.exc_info()
    exception_details = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    if custom_message:
        logger.error(f"{custom_message}\n{exception_details}")
    else:
        logger.error(f"Exception occurred:\n{exception_details}")


logger = get_logger(__name__)


#### === Carpetas de organización === ####
CAPTCHA_FOLDER = os.path.join(BASE_FOLDER, "captchas")
EVIDENCE_FOLDER = os.path.join(BASE_FOLDER, "screenshots")
for folder in [LOG_FOLDER, CAPTCHA_FOLDER, EVIDENCE_FOLDER]:
    os.makedirs(folder, exist_ok=True)


#### === Importa tu mapping de grupos === ####
sys.path.insert(0, str(Path(__file__).parent.parent))
from diccionario import WEBSITES, CAPTCHA_GRUPOS, obtener_grupo


#### === Timestamp helper === ####
def get_current_timestamp():
    """Devuelve timestamp actual en formato 'YYYY-MM-DD HH:MM:SS'"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


#### === Auto-detección del website y tracking de captchas === ####
_captcha_data = {}


def _detectar_website_desde_caller():
    """Auto-detecta el nombre del website buscando la variable WEBSITE_NAME."""
    try:
        for frame_info in inspect.stack():
            frame_locals = frame_info.frame.f_locals
            frame_globals = frame_info.frame.f_globals
            
            if 'WEBSITE_NAME' in frame_locals:
                return frame_locals['WEBSITE_NAME']
            if 'WEBSITE_NAME' in frame_globals:
                return frame_globals['WEBSITE_NAME']
        
        if VERBOSE_LOGGING:
            logger.warning("[CAPTCHA] No se pudo auto-detectar WEBSITE_NAME")
        return None
    except Exception as e:
        if VERBOSE_LOGGING:
            logger.warning(f"[CAPTCHA] Error en auto-detección: {e}")
        return None


def get_captcha_folder_for_website(website_name):
    """Crea y retorna la carpeta específica para captchas de un website."""
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
        if VERBOSE_LOGGING:
            logger.debug(f"[CAPTCHA] Registrado: {website_name} → {solucion}")


def _renombrar_captcha_automatico(website_name):
    """Renombra automáticamente el captcha cuando se registra un balance exitoso"""
    global _captcha_data
    
    if website_name not in _captcha_data:
        return
    
    data = _captcha_data[website_name]
    old_path = data['path']
    solucion = data['solution']
    
    if not os.path.exists(old_path):
        if VERBOSE_LOGGING:
            logger.warning(f"[CAPTCHA] Archivo no encontrado: {old_path}")
        del _captcha_data[website_name]
        return
    
    try:
        directorio = os.path.dirname(old_path)
        extension = os.path.splitext(old_path)[1]
        
        nuevo_nombre = f"{solucion}{extension}"
        new_path = os.path.join(directorio, nuevo_nombre)
        
        contador = 1
        while os.path.exists(new_path):
            nuevo_nombre = f"{solucion}_{contador}{extension}"
            new_path = os.path.join(directorio, nuevo_nombre)
            contador += 1
        
        os.rename(old_path, new_path)
        if VERBOSE_LOGGING:
            logger.debug(f"[CAPTCHA] Renombrado: {os.path.basename(old_path)} → {nuevo_nombre}")
        
        del _captcha_data[website_name]
        
    except Exception as e:
        logger.error(f"[CAPTCHA] Error al renombrar: {e}")


def detectar_grupo_captcha(website_name):
    """
    Detecta qué grupo de captcha usar basándose en el website.
    ✅ Solo loguea si VERBOSE_LOGGING está activado
    """
    if not website_name:
        return None
    
    for grupo_id, websites in CAPTCHA_GRUPOS.items():
        if website_name in websites:
            if VERBOSE_LOGGING:
                logger.debug(f"[CAPTCHA] {website_name} → {grupo_id}")
            return grupo_id
    
    if VERBOSE_LOGGING:
        logger.debug(f"[CAPTCHA] {website_name} → 2captcha")
    return None


#### === Opciones Chrome/Bots === ####
CHROME_HEADLESS = True
CHROME_WINDOW_SIZE = (900, 1300)
CHROME_LANG = "en-US"


def get_chrome_driver():
    """Crea driver de Chrome optimizado para bajo consumo de memoria."""
    options = webdriver.ChromeOptions()
    
    if CHROME_HEADLESS:
        options.add_argument("--headless=new")
    
    options.add_argument(f"--window-size={CHROME_WINDOW_SIZE[0]},{CHROME_WINDOW_SIZE[1]}")
    options.add_argument(f"--lang={CHROME_LANG}")
    
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-infobars")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-logging")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_argument("--disk-cache-size=1")
    options.add_argument("--media-cache-size=1")
    options.add_argument("--disable-application-cache")
    
    options.add_experimental_option('excludeSwitches', ['enable-logging', 'enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(60)
        driver.implicitly_wait(2)
        driver.set_window_size(*CHROME_WINDOW_SIZE)
        return driver
    except Exception as e:
        logger.error(f"[CHROME] Error al iniciar driver: {e}")
        raise


#### === Captcha config === ####
API_KEY_2CAPTCHA = os.getenv('API_KEY_2CAPTCHA')
KERAS_PREDICT_TIMEOUT = int(os.getenv('KERAS_PREDICT_TIMEOUT', '10'))


CAPTCHA_CONFIG = {
    "grupo1": {
        "model_path": os.path.join(os.path.dirname(BASE_FOLDER), "captchaModel", "models", "captcha_grupo1_v1_pred.h5"),
        "img_width": 200,
        "img_height": 50,
        "max_length": 5,
        "characters": "0123456789"
    },
    "grupo2": {
        "model_path": os.path.join(os.path.dirname(BASE_FOLDER), "captchaModel", "models", "captcha_grupo2_v1_pred.h5"),
        "img_width": 200,
        "img_height": 60,
        "max_length": 4,
        "characters": "0123456789"
    },
    "grupo3": {
        "model_path": os.path.join(os.path.dirname(BASE_FOLDER), "captchaModel", "models", "captcha_grupo3_v2_62px_pred.h5"),
        "img_width": 200,
        "img_height": 62,
        "max_length": 4,
        "characters": "0123456789"
    }
}


CAPTCHA_MAX_RETRIES = {
    "grupo1": 3,
    "grupo2": 3,
    "grupo3": 2
}


keras_models = {}


def cargar_modelo_keras(grupo_id):
    """
    Carga el modelo Keras SOLO cuando se necesita (lazy loading).
    ✅ Log simplificado: solo muestra cuando carga por primera vez
    """
    global keras_models
    
    if grupo_id in keras_models:
        return keras_models[grupo_id]
    
    if grupo_id not in CAPTCHA_CONFIG:
        logger.error(f"[KERAS] Grupo '{grupo_id}' no existe")
        return None
    
    config_grupo = CAPTCHA_CONFIG[grupo_id]
    model_path = config_grupo["model_path"]
    characters = config_grupo["characters"]
    
    try:
        import tensorflow as tf
        from tensorflow import keras
        
        logger.info(f"[KERAS] Cargando {grupo_id}...")
        
        if not os.path.exists(model_path):
            logger.error(f"[KERAS] Archivo no encontrado: {model_path}")
            return None
        
        gpus = tf.config.list_physical_devices('GPU')
        if gpus:
            try:
                for gpu in gpus:
                    tf.config.experimental.set_memory_growth(gpu, True)
                if VERBOSE_LOGGING:
                    logger.debug(f"[KERAS] GPU configurada")
            except RuntimeError as e:
                if VERBOSE_LOGGING:
                    logger.warning(f"[KERAS] No se pudo configurar GPU: {e}")
        
        model = keras.models.load_model(model_path, compile=False)
        num_to_char_dict = {idx: char for idx, char in enumerate(characters)}
        
        keras_models[grupo_id] = {
            'model': model,
            'num_to_char': num_to_char_dict,
            'config': config_grupo
        }
        
        logger.info(f"[KERAS] ✓ {grupo_id} listo")
        
        return keras_models[grupo_id]
        
    except Exception as e:
        logger.error(f"[KERAS] Error cargando {grupo_id}: {e}")
        return None


logger.info("="*70)
logger.info("✓ Sistema iniciado (modelos Keras: carga bajo demanda)")
logger.info("="*70)


def decode_keras_prediction(pred, num_to_char_dict, max_length):
    """Decodifica la predicción del modelo Keras usando CTC decode."""
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
            text = ''.join([
                num_to_char_dict[idx] 
                for idx in indices 
                if 0 <= idx < len(num_to_char_dict)
            ])
            output_text.append(text)
        
        return output_text[0] if output_text else ""
    except Exception as e:
        logger.error(f"[CAPTCHA] Error decodificando: {e}")
        return ""


def calcular_confianza_prediccion(pred):
    """Calcula el score de confianza de una predicción."""
    try:
        max_probs = np.max(pred[0], axis=1)
        confidence = np.mean(max_probs)
        return float(confidence)
    except Exception as e:
        if VERBOSE_LOGGING:
            logger.warning(f"[CAPTCHA] Error calculando confianza: {e}")
        return 0.0


def predict_with_timeout(model, img_array, timeout=KERAS_PREDICT_TIMEOUT):
    """Ejecuta model.predict() con timeout y limpieza de recursos."""
    result_queue = Queue()
    exception_queue = Queue()
    
    def predict_worker():
        try:
            prediction = model.predict(img_array, verbose=0)
            result_queue.put(prediction)
        except Exception as e:
            exception_queue.put(e)
        finally:
            # ✅ Limpiar backend TF en el thread
            import tensorflow as tf
            tf.keras.backend.clear_session()
    
    thread = threading.Thread(target=predict_worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout)
    
    if thread.is_alive():
        if VERBOSE_LOGGING:
            logger.warning(f"[CAPTCHA] Timeout en predicción ({timeout}s)")
        del thread
        gc.collect()
        return None, False
    
    if not exception_queue.empty():
        exc = exception_queue.get()
        logger.error(f"[CAPTCHA] Error en predicción: {exc}")
        del thread
        return None, False
    
    result = None
    if not result_queue.empty():
        result = result_queue.get()
    
    del thread
    return (result, True) if result is not None else (None, False)


def resolver_captcha_keras_interno(image_bytes, grupo_id, captcha_path):
    """
    Resuelve captcha usando el modelo Keras del grupo especificado.
    ✅ Solo loguea resultados importantes
    """
    pil_img = None
    pil_img_resized = None
    img_array = None
    prediction = None
    
    try:
        model_data = cargar_modelo_keras(grupo_id)
        if model_data is None:
            logger.error(f"[CAPTCHA] No se pudo cargar modelo {grupo_id}")
            return None, 0.0, False
        
        model = model_data['model']
        num_to_char = model_data['num_to_char']
        config_grupo = model_data['config']
        
        # ✅ CAMBIO CRÍTICO: Sin preprocesamiento, resize directo con BILINEAR
        pil_img = Image.open(captcha_path).convert('L')
        pil_img_resized = pil_img.resize(
            (config_grupo['img_width'], config_grupo['img_height']),
            Image.BILINEAR  # ✅ EXPLÍCITO
        )
        
        img_array = np.array(pil_img_resized).astype(np.float32) / 255.0
        img_array = np.expand_dims(img_array, -1)
        img_array = np.transpose(img_array, (1, 0, 2))
        img_array = np.expand_dims(img_array, 0)
        
        prediction, success = predict_with_timeout(model, img_array, timeout=KERAS_PREDICT_TIMEOUT)
        
        if not success:
            return None, 0.0, True
        
        confidence = calcular_confianza_prediccion(prediction)
        text = decode_keras_prediction(prediction, num_to_char, config_grupo['max_length'])
        
        # ✅ DEBUG: Guardar imagen PROCESADA (no original)
        if grupo_id == "grupo3":
            debug_folder = os.path.join(os.path.dirname(captcha_path), "debug_predictions")
            os.makedirs(debug_folder, exist_ok=True)
            
            debug_path = os.path.join(
                debug_folder, 
                f"pred_{text}_conf{confidence:.2f}_{int(time.time())}.png"
            )
            # ✅ GUARDAR la imagen PROCESADA (200x62)
            pil_img_resized.save(debug_path)
            logger.info(f"[DEBUG] Guardado: {os.path.basename(debug_path)}")
        
        expected_length = config_grupo['max_length']
        
        if text and text.isdigit():
            if expected_length - 1 <= len(text) <= expected_length + 1:
                logger.info(f"[CAPTCHA] ✓ Resuelto: {text} (conf: {confidence:.2f})")
                return text, confidence, False
            else:
                if VERBOSE_LOGGING:
                    logger.warning(f"[CAPTCHA] Longitud inválida: {text}")
                return None, confidence, False
        else:
            if VERBOSE_LOGGING:
                logger.warning(f"[CAPTCHA] Resultado inválido: {text}")
            return None, confidence, False
            
    except Exception as e:
        logger.error(f"[CAPTCHA] Error: {e}")
        return None, 0.0, False
    
    finally:
        # ✅ LIMPIAR TODO + TensorFlow backend
        del pil_img, pil_img_resized, img_array, prediction
        import tensorflow as tf
        tf.keras.backend.clear_session()
        gc.collect()


def resolver_captcha_2captcha_api(image_bytes, captcha_path, website_name):
    """
    Resuelve captcha usando servicio 2captcha.
    ✅ Solo loguea inicio y resultado final
    """
    try:
        logger.info(f"[2CAPTCHA] Enviando...")
        
        with open(captcha_path, "rb") as fp:
            files = {'file': fp}
            data = {'key': API_KEY_2CAPTCHA, 'method': 'post', 'json': 1}
            resp = requests.post('http://2captcha.com/in.php', files=files, data=data, timeout=30).json()
            
            if 'request' not in resp:
                logger.error(f"[2CAPTCHA] Respuesta inválida: {resp}")
                return None
            
            captcha_id = resp['request']
        
        for intent in range(18):
            time.sleep(2)
            res = requests.get(
                f"http://2captcha.com/res.php?key={API_KEY_2CAPTCHA}&action=get&id={captcha_id}&json=1",
                timeout=30
            ).json()
            
            if res['status'] == 1:
                result = res['request']
                logger.info(f"[2CAPTCHA] ✓ Resuelto: {result}")
                _registrar_captcha(website_name, captcha_path, result)
                return result
        
        logger.warning("[2CAPTCHA] Timeout")
        return None
        
    except Exception as e:
        logger.error(f"[2CAPTCHA] Error: {e}")
        return None


def resolver_captcha_2captcha(image_bytes, filename_prefix='captcha'):
    """
    Función unificada para resolver captchas.
    ✅ Logging limpio enfocado en eventos importantes
    """
    website_name = _detectar_website_desde_caller()
    ts = int(time.time())
    
    if website_name:
        captcha_folder = get_captcha_folder_for_website(website_name)
    else:
        captcha_folder = CAPTCHA_FOLDER
    
    captcha_path = os.path.join(captcha_folder, f"{filename_prefix}_{ts}.png")
    
    try:
        with open(captcha_path, "wb") as f:
            f.write(image_bytes)
    except Exception as e:
        logger.error(f"[CAPTCHA] Error guardando imagen: {e}")
        return None
    
    grupo_id = detectar_grupo_captcha(website_name)
    
    if grupo_id is None:
        return resolver_captcha_2captcha_api(image_bytes, captcha_path, website_name)
    
    max_retries = CAPTCHA_MAX_RETRIES.get(grupo_id, 3)
    
    for intento in range(1, max_retries + 1):
        result, confidence, timeout_occurred = resolver_captcha_keras_interno(image_bytes, grupo_id, captcha_path)
        
        if timeout_occurred:
            if VERBOSE_LOGGING:
                logger.debug(f"[CAPTCHA] Timeout intento {intento}, reintentando...")
            time.sleep(1)
            continue
        
        if result:
            _registrar_captcha(website_name, captcha_path, result)
            return result
        else:
            if intento < max_retries:
                time.sleep(0.5)
    
    logger.info(f"[CAPTCHA] Modelo falló → Usando 2captcha")
    return resolver_captcha_2captcha_api(image_bytes, captcha_path, website_name)


#### === Evidencias === ####
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


def enviar_resultado_balance(sheet, website, username, fecha=None, balance=None):
    """
    Registra un balance en MongoDB.
    ✅ Log limpio: solo muestra registro exitoso
    """
    if fecha is None:
        fecha = get_current_timestamp()
    
    grupo = obtener_grupo(username, website)
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
                "website": website_normalized,
                "username": username,
                "fecha": fecha,
                "balance": balance,
                "used_as_previous": False,
                "grupo": grupo
            }
            
            collection.insert_one(doc)
            logger.info(f"[✓] {website_normalized} | {username} | {balance}")
            
        except Exception as e:
            logger.error(f"[MongoDB] Error: {e}")
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass
