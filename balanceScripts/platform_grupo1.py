"""
Platform Grupo 1 - Lógica centralizada para websites con estructura similar.
Sitios compatibles: MILKY WAY, ORION STARS, FIRE KIRIN, JUWA, ULTRA PANDA, VEGAS X, etc.

Estructura común:
- Login con usuario/password/captcha
- Popup de sesión expirada con ID "mb_btn_ok"
- Captcha imagen con ID "ImageCheck"
- Balance en ID "UserBalance"
- Usuario en ID "UserName"
- Logout con onclick="top.location.href = 'LoginOut.aspx'"
"""
import time
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import config


def get_logger(website_name):
    """Obtiene logger específico para el website"""
    return config.get_logger(f"{website_name}_bot")


def popup_session_timeout_handler(driver, logger):
    """
    Cierra popups de sesión expirada (modal con ID 'mb_btn_ok').
    Loop hasta que no haya más modales visibles.
    """
    while True:
        time.sleep(2)
        modal_detected = False
        try:
            ok_btn = driver.find_element(By.ID, "mb_btn_ok")
            ok_btn.click()
            logger.info("Popup de sesión expirada cerrado automáticamente.")
            modal_detected = True
        except NoSuchElementException:
            pass
        except Exception as e:
            logger.warning(f"Error al cerrar popup de sesión expirada: {e}")
            break
        
        if modal_detected:
            time.sleep(2)
            continue
        
        try:
            overlay = driver.find_element(By.ID, "mb_box")
            if overlay.is_displayed():
                logger.info("Overlay de sesión aún presente, repitiendo ciclo de cierre.")
                continue
        except NoSuchElementException:
            pass
        break


def resolver_captcha(driver, website_name_prefix, logger):
    """
    Resuelve captcha usando imagen con ID 'ImageCheck' e input 'txtVerifyCode'.
    
    Args:
        website_name_prefix: Prefijo para el archivo del captcha (ej: "milkyway", "orion")
    """
    try:
        captcha_img = driver.find_element(By.ID, "ImageCheck")
        captcha_bytes = captcha_img.screenshot_as_png
        solucion = config.resolver_captcha_2captcha(captcha_bytes, website_name_prefix.lower())
        
        if not solucion:
            logger.warning(f"[CAPTCHA] No se obtuvo solución del captcha")
            return False
        
        input_code = driver.find_element(By.ID, "txtVerifyCode")
        input_code.clear()
        input_code.send_keys(solucion)
        logger.info(f"[CAPTCHA] Captcha resuelto e ingresado")
        return True
        
    except Exception as e:
        logger.error(f"[CAPTCHA] Error al resolver captcha: {e}")
        config.log_exception(logger, "Error en resolver_captcha")
        return False


def close_popup(driver, logger):
    """
    Cierra popup post-login con botón ID 'cancelBtn'.
    Intenta hasta 5 veces con pequeños delays.
    """
    try:
        for intento in range(5):
            try:
                cancel_btn = driver.find_element(By.ID, "cancelBtn")
                cancel_btn.click()
                logger.info("[POPUP] Popup post-login cerrado")
                break
            except NoSuchElementException:
                time.sleep(0.3)
    except Exception as e:
        logger.debug(f"[POPUP] No se encontró popup para cerrar (puede ser normal): {e}")


def extraer_balance_y_usuario(driver, logger):
    """
    Extrae balance (ID 'UserBalance') y username (ID 'UserName').
    
    Returns:
        tuple: (balance: int, username: str) o (None, None) si falla
    """
    try:
        # Extraer balance
        elem_balance = driver.find_element(By.ID, "UserBalance")
        texto_balance = elem_balance.text
        match = re.search(r'\d+', texto_balance)
        balance = int(match.group()) if match else None
        
        # Extraer username
        elem_usuario = driver.find_element(By.ID, "UserName")
        username = elem_usuario.text.strip()
        
        if balance is not None and username:
            logger.info(f"[EXTRACT] Balance: {balance}, Usuario: {username}")
            print(f"Balance: {balance}, Usuario: {username}")
            return balance, username
        else:
            logger.warning("[EXTRACT] Balance o usuario es None")
            return None, None
            
    except Exception as e:
        logger.error(f"[EXTRACT] Error al extraer balance/usuario: {e}")
        config.log_exception(logger, "Error en extraer_balance_y_usuario")
        return None, None


def logout(driver, logger):
    """
    Realiza logout usando link con onclick="top.location.href = 'LoginOut.aspx'".
    """
    try:
        logout_link = driver.find_element(By.XPATH, "//a[@onclick=\"top.location.href = 'LoginOut.aspx'\"]")
        logout_link.click()
        logger.info("[LOGOUT] Logout realizado correctamente")
        time.sleep(1)
    except Exception as e:
        logger.warning(f"[LOGOUT] No se pudo hacer logout: {e}")


def login_and_check(driver, website_name, usuario, password, max_retries, logger):
    """
    Intenta login con reintentos automáticos.
    
    Returns:
        tuple: (balance, username, hora_login) o (None, None, None) si falla
    """
    # Prefijo para captcha basado en website name
    website_prefix = website_name.replace(" ", "").lower()
    
    for intento in range(max_retries):
        try:
            # Cargar página
            driver.get(config.WEBSITES[website_name]["url"])
            
            # Cerrar popups de sesión expirada
            popup_session_timeout_handler(driver, logger)
            
            # Llenar formulario
            driver.find_element(By.ID, "txtLoginName").clear()
            driver.find_element(By.ID, "txtLoginName").send_keys(usuario)
            driver.find_element(By.ID, "txtLoginPass").clear()
            driver.find_element(By.ID, "txtLoginPass").send_keys(password)
            
            # Resolver captcha
            if not resolver_captcha(driver, website_prefix, logger):
                logger.warning(f"[LOGIN] Intento {intento + 1}/{max_retries} - Captcha falló")
                time.sleep(2)
                continue
            
            # Click en login
            driver.find_element(By.ID, "btnLogin").click()
            time.sleep(2.5)
            
            # Cerrar popup post-login
            close_popup(driver, logger)
            
            # ✅ PRIMERO: Extraer balance y usuario (valida que login fue exitoso)
            balance, username = extraer_balance_y_usuario(driver, logger)
            
            if balance is not None and username:
                # ✅ DESPUÉS: Capturar timestamp SOLO si login fue exitoso
                hora_login = config.get_current_timestamp()
                logger.info(f"[LOGIN] ✅ Login exitoso para {usuario}")
                return balance, username, hora_login
            else:
                logger.warning(f"[LOGIN] Intento {intento + 1}/{max_retries} - No se pudo extraer balance/usuario")
                
        except Exception as e:
            logger.warning(f"[LOGIN] Intento {intento + 1}/{max_retries} - Error: {e}")
            config.log_exception(logger, f"Error en login_and_check intento {intento + 1}")
            time.sleep(2)
    
    logger.error(f"[LOGIN] ❌ Login falló después de {max_retries} intentos para {usuario}")
    return None, None, None


def run(website_name, max_login_retries=4):
    """
    Función principal para ejecutar el bot.
    
    Args:
        website_name: Nombre exacto del website en diccionario (ej: "MILKY WAY", "ORION STARS")
        max_login_retries: Número máximo de reintentos de login por cuenta
    """
    logger = get_logger(website_name)
    logger.info(f"{'='*60}")
    logger.info(f"Iniciando bot para {website_name}")
    logger.info(f"{'='*60}")
    
    driver = None
    try:
        # Inicializar driver y sheet
        driver = config.get_chrome_driver()
        sheet = config.google_sheets_connect()
        
        # Obtener cuentas del diccionario
        if website_name not in config.WEBSITES:
            logger.error(f"❌ Website '{website_name}' no encontrado en diccionario")
            return
        
        cuentas = config.WEBSITES[website_name]["accounts"]
        logger.info(f"Total de cuentas a procesar: {len(cuentas)}")
        
        # Procesar cada cuenta
        for idx, cuenta in enumerate(cuentas, 1):
            usuario = cuenta['usuario']
            password = cuenta['password']
            
            logger.info(f"\n[{idx}/{len(cuentas)}] Procesando cuenta: {usuario}")
            
            # Intentar login y extraer balance
            balance, username, hora_login = login_and_check(
                driver, website_name, usuario, password, max_login_retries, logger
            )
            
            # Si login exitoso, registrar balance
            if balance is not None and username is not None:
                config.enviar_resultado_balance(
                    sheet, website_name, username, hora_login, balance
                )
            else:
                logger.warning(f"[{idx}/{len(cuentas)}] ⚠️ No se pudo obtener balance para {usuario}")
            
            # Logout
            logout(driver, logger)
            
            # Delay entre cuentas
            if idx < len(cuentas):
                time.sleep(2)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ Proceso completado para {website_name}")
        logger.info(f"{'='*60}")
        
    except Exception as e:
        logger.error(f"❌ Error fatal en ejecución del bot: {e}")
        config.log_exception(logger, "Error fatal en run()")
        
    finally:
        if driver:
            driver.quit()
            logger.info("Driver cerrado correctamente")


if __name__ == "__main__":
    print("Este archivo contiene lógica centralizada.")
    print("Ejecuta los scripts individuales (ej: milkywayBalance.py)")
