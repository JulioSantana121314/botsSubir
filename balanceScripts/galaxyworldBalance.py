# galaxyworldBalance.py — versión 2.0 (modernizado + logging optimizado)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from datetime import datetime
import config
import os

WEBSITE_NAME = "GALAXY WORLD"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def resolver_captcha_galaxyworld(driver, max_retries=5):
    """
    Resuelve el captcha de Galaxy World usando modelo Keras grupo3.
    ✅ NO usa 2captcha, solo modelo local
    """
    for intento in range(max_retries):
        try:
            captcha_img = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "imgCode"))
            )
            captcha_bytes = captcha_img.screenshot_as_png
            
            # ✅ Guardar imagen temporalmente para procesarla con Keras
            ts = int(time.time())
            captcha_folder = config.get_captcha_folder_for_website(WEBSITE_NAME)
            captcha_path = os.path.join(captcha_folder, f"galaxyworld_{ts}.png")
            
            with open(captcha_path, "wb") as f:
                f.write(captcha_bytes)
            
            # ✅ FORZAR uso de modelo grupo3 (no 2captcha)
            result, confidence, timeout_occurred = config.resolver_captcha_keras_interno(
                captcha_bytes, 
                "grupo3",  # ← FORZAR grupo3
                captcha_path
            )
            
            if timeout_occurred:
                if config.VERBOSE_LOGGING:
                    logger.warning(f"[CAPTCHA] Timeout en intento {intento + 1}, reintentando...")
                time.sleep(1)
                continue
            
            if result:
                # ✅ Registrar captcha para renombrado automático
                config._registrar_captcha(WEBSITE_NAME, captcha_path, result)
                
                # Ingresar solución
                input_captcha = driver.find_elements(By.CSS_SELECTOR, "input.el-input__inner")[2]
                input_captcha.clear()
                input_captcha.send_keys(result)
                return True
            else:
                if config.VERBOSE_LOGGING:
                    logger.warning(f"[CAPTCHA] Intento {intento + 1}/{max_retries} falló (conf: {confidence:.2f})")
                if intento < max_retries - 1:
                    time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"[CAPTCHA] Error intento {intento + 1}: {e}")
            if intento < max_retries - 1:
                time.sleep(1)
    
    # ✅ Si falla tras todos los intentos, lanzar excepción (NO usar 2captcha)
    logger.error(f"[CAPTCHA] Modelo grupo3 falló tras {max_retries} intentos")
    raise Exception(f"Error resolviendo captcha con modelo grupo3 tras {max_retries} intentos")

def login_galaxyworld(driver, usuario, password):
    """Rellena el formulario de login"""
    try:
        usuario_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='username']")
        pass_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='password']")
        
        usuario_input.clear()
        usuario_input.send_keys(usuario)
        pass_input.clear()
        pass_input.send_keys(password)
        
    except Exception as e:
        logger.error(f"[LOGIN] Error rellenando formulario: {e}")
        raise

def click_sign_in(driver):
    """Click en el botón Sign In"""
    try:
        time.sleep(1.0)
        signin_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.login-btn > button.el-button--primary"))
        )
        signin_btn.click()
    except TimeoutException:
        logger.error("[LOGIN] Botón Sign In no encontrado")
        raise

def ir_admin_list(driver):
    """Navega a la sección Admin List"""
    try:
        wait = WebDriverWait(driver, 20)
        admin_icon = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "i.el-icon-user-solid"))
        )
        admin_btn = admin_icon.find_element(By.XPATH, "./..")
        admin_btn.click()
        time.sleep(2)
    except TimeoutException:
        logger.error("[NAVIGATION] Ícono Admin List no encontrado")
        raise

def extraer_balance_header_galaxyworld(driver):
    """
    Extrae el balance del header de Admin List.
    ✅ Optimizado con mejor manejo de errores
    """
    for intento in range(30):
        try:
            # Primer intento: buscar en span interno
            balance_elem = driver.find_element(
                By.XPATH, 
                "//button[contains(@class,'el-button--default') and contains(.,'Balance:')]/span/span"
            )
            balance_str = balance_elem.text.strip()
        except Exception:
            try:
                # Segundo intento: buscar en span con style
                balance_elem = driver.find_element(
                    By.XPATH, 
                    "//button[contains(@class,'el-button--default') and contains(.,'Balance:')]//span[@style]"
                )
                balance_str = balance_elem.text.strip()
            except Exception:
                balance_str = ""
        
        # Validar y extraer número
        if balance_str:
            match = re.search(r"[0-9,\.]+", balance_str)
            if match:
                balance = float(match.group().replace(',', ''))
                return balance
        
        # Esperar 1 segundo antes de reintentar
        if intento < 29:
            time.sleep(1)
    
    # Si no se encuentra tras 30 intentos, guardar evidencia
    config.guardar_evidencia(driver.get_screenshot_as_png(), "galaxyworld_no_balance")
    logger.error("[BALANCE] No se encontró balance en header tras 30 segundos")
    return None

def procesar_cuenta(driver, cuenta, idx, total):
    """
    Procesa una cuenta individual.
    ✅ Retorna True si fue exitoso, False si falló
    """
    usuario = cuenta["usuario"]
    password = cuenta["password"]
    
    logger.info(f"[{idx}/{total}] Procesando: {usuario}")
    
    # Intentos de login
    for intento in range(MAX_LOGIN_RETRIES):
        try:
            # Verificar driver está activo
            if not getattr(driver, "session_id", None):
                raise WebDriverException("Driver sin sesión válida")
            
            # Navegar y hacer login
            driver.get(config.WEBSITES[WEBSITE_NAME]["url"])
            time.sleep(1)
            
            login_galaxyworld(driver, usuario, password)
            resolver_captcha_galaxyworld(driver)
            click_sign_in(driver)
            
            time.sleep(8)
            
            # Verificar si login fue exitoso
            current_url = driver.current_url
            if config.WEBSITES[WEBSITE_NAME]["url"] in current_url or "login" in current_url.lower():
                if config.VERBOSE_LOGGING:
                    logger.debug(f"   Login intento {intento + 1}/{MAX_LOGIN_RETRIES} falló")
                time.sleep(2)
                continue
            else:
                # Login exitoso
                break
        
        except WebDriverException as e:
            if "invalid session id" in str(e).lower():
                raise  # Propagar para reiniciar driver
            
            if config.VERBOSE_LOGGING:
                logger.warning(f"   Error intento {intento + 1}: {e}")
            time.sleep(2)
        
        except Exception as e:
            if config.VERBOSE_LOGGING:
                logger.warning(f"   Error intento {intento + 1}: {e}")
            time.sleep(2)
    else:
        # No se pudo loguear tras todos los intentos
        logger.error(f"[{idx}/{total}] ✗ Login fallido: {usuario}")
        return False
    
    # Extraer balance
    try:
        ir_admin_list(driver)
        balance = extraer_balance_header_galaxyworld(driver)
        
        if balance is not None:
            # ✅ Función correcta con parámetros nombrados
            config.enviar_resultado_balance(
                sheet=None,  # No se usa en modo MONGO
                website=WEBSITE_NAME,
                username=usuario,
                balance=balance
            )
            logger.info(f"[{idx}/{total}] ✓ Completado: {usuario}")
            return True
        else:
            logger.error(f"[{idx}/{total}] ✗ No se pudo extraer balance: {usuario}")
            return False
    
    except Exception as e:
        logger.error(f"[{idx}/{total}] ✗ Error extrayendo balance: {usuario}")
        if config.VERBOSE_LOGGING:
            config.log_exception(logger, f"Error en extracción para {usuario}")
        return False

def main():
    """
    Función principal con logging limpio y manejo robusto de errores.
    ✅ Reinicia driver automáticamente si falla
    """
    sheet = None
    if config.EXPORT_MODE.upper() == "SHEET":
        sheet = config.google_sheets_connect()
    
    site = config.WEBSITES[WEBSITE_NAME]
    driver = None
    
    total_cuentas = len(site["accounts"])
    exitosos = 0
    
    logger.info("="*70)
    logger.info(f"🚀 Iniciando scraping: {WEBSITE_NAME} ({total_cuentas} cuentas)")
    logger.info("="*70)
    
    try:
        for idx, cuenta in enumerate(site["accounts"], 1):
            # Verificar/iniciar driver
            try:
                if driver is None or not getattr(driver, "session_id", None):
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                    driver = config.get_chrome_driver()
                
                # Procesar cuenta
                if procesar_cuenta(driver, cuenta, idx, total_cuentas):
                    exitosos += 1
            
            except WebDriverException as e:
                if "invalid session id" in str(e).lower():
                    logger.warning(f"[{idx}/{total_cuentas}] Driver perdió sesión, reiniciando...")
                    if driver:
                        try:
                            driver.quit()
                        except:
                            pass
                    driver = None
                    # Reintentar esta cuenta
                    continue
                else:
                    logger.error(f"[{idx}/{total_cuentas}] Error WebDriver: {e}")
            
            except Exception as e:
                logger.error(f"[{idx}/{total_cuentas}] Error inesperado: {e}")
                if config.VERBOSE_LOGGING:
                    config.log_exception(logger, f"Error procesando {cuenta['usuario']}")
    
    finally:
        # Cerrar driver
        if driver:
            try:
                driver.quit()
            except:
                pass
        
        # Resumen final
        logger.info("="*70)
        logger.info(f"✓ {WEBSITE_NAME} completado ({exitosos}/{total_cuentas} exitosos)")
        logger.info("="*70)

if __name__ == "__main__":
    main()
