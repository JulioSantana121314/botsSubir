# siriusBalance.py — versión 1.2 (logging optimizado + función correcta)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "SIRIUS"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def resolver_captcha_sirius(driver, max_retries=5):
    """Resuelve el captcha de Sirius"""
    for intento in range(max_retries):
        try:
            captcha_img = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "imgCode"))
            )
            captcha_bytes = captcha_img.screenshot_as_png
            solucion = config.resolver_captcha_2captcha(captcha_bytes, "sirius")
            
            if not solucion:
                logger.warning(f"[CAPTCHA] Intento {intento + 1}/{max_retries} falló")
                continue
            
            input_captcha = driver.find_elements(By.CSS_SELECTOR, "input.el-input__inner")[2]
            input_captcha.clear()
            input_captcha.send_keys(solucion)
            return True
        except Exception as e:
            logger.warning(f"[CAPTCHA] Error en intento {intento + 1}: {e}")
            if intento < max_retries - 1:
                time.sleep(1)
    
    raise Exception("Error resolviendo captcha Sirius tras múltiples intentos")

def login_sirius(driver, usuario, password):
    """Rellena el formulario de login"""
    usuario_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='username']")
    pass_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='password']")
    usuario_input.clear()
    usuario_input.send_keys(usuario)
    pass_input.clear()
    pass_input.send_keys(password)

def click_sign_in(driver):
    """Click en el botón Sign In"""
    time.sleep(1.0)
    signin_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.login-btn > button.el-button--primary"))
    )
    signin_btn.click()

def ir_admin_list(driver):
    """Navega a la sección Admin List"""
    wait = WebDriverWait(driver, 20)
    admin_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "i.el-icon-user-solid")))
    admin_btn = admin_icon.find_element(By.XPATH, "./..")
    admin_btn.click()
    time.sleep(2)

def extraer_balance_header_sirius(driver):
    """Extrae el balance del header de Admin List"""
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
        match = re.search(r"[0-9,\.]+", balance_str)
        if match and balance_str != "":
            balance = float(match.group().replace(',', ''))
            return balance
        
        time.sleep(1)
    
    # Si no se encuentra tras 30 intentos, guardar evidencia
    config.guardar_evidencia(driver.get_screenshot_as_png(), "sirius_adminlist_no_balance")
    logger.error("[BALANCE] No se encontró balance en header tras 30 intentos")
    return None

def main():
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
            usuario = cuenta["usuario"]
            password = cuenta["password"]
            
            logger.info(f"[{idx}/{total_cuentas}] Procesando: {usuario}")
            
            # Intentos de login
            login_exitoso = False
            for intento in range(MAX_LOGIN_RETRIES):
                try:
                    # Verificar/reiniciar driver si es necesario
                    if driver is None or not getattr(driver, "session_id", None):
                        if driver:
                            try:
                                driver.quit()
                            except:
                                pass
                        driver = config.get_chrome_driver()
                    
                    # Proceso de login
                    driver.get(site["url"])
                    time.sleep(1)
                    
                    login_sirius(driver, usuario, password)
                    resolver_captcha_sirius(driver)
                    click_sign_in(driver)
                    
                    time.sleep(8)
                    
                    # Verificar si login fue exitoso
                    if driver.current_url == site["url"] or "login" in driver.current_url.lower():
                        if config.VERBOSE_LOGGING:
                            logger.debug(f"   Intento {intento + 1}/{MAX_LOGIN_RETRIES} falló")
                        time.sleep(2)
                        continue
                    else:
                        login_exitoso = True
                        break
                
                except WebDriverException as e:
                    if "invalid session id" in str(e).lower():
                        if driver:
                            try:
                                driver.quit()
                            except:
                                pass
                        driver = config.get_chrome_driver()
                    
                    if config.VERBOSE_LOGGING:
                        logger.warning(f"   WebDriverException intento {intento + 1}: {e}")
                    time.sleep(2)
                
                except Exception as e:
                    if config.VERBOSE_LOGGING:
                        logger.warning(f"   Error intento {intento + 1}: {e}")
                    time.sleep(2)
            
            # Si no se pudo loguear tras todos los intentos
            if not login_exitoso:
                logger.error(f"[{idx}/{total_cuentas}] ✗ Login fallido tras {MAX_LOGIN_RETRIES} intentos: {usuario}")
                continue
            
            # Extraer balance
            try:
                ir_admin_list(driver)
                balance = extraer_balance_header_sirius(driver)
                
                if balance is not None:
                    # ✅ FUNCIÓN CORRECTA: enviar_resultado_balance()
                    config.enviar_resultado_balance(
                        sheet=sheet,
                        website=WEBSITE_NAME,
                        username=usuario,
                        balance=balance
                    )
                    exitosos += 1
                    logger.info(f"[{idx}/{total_cuentas}] ✓ Completado: {usuario}")
                else:
                    logger.error(f"[{idx}/{total_cuentas}] ✗ No se pudo extraer balance: {usuario}")
            
            except Exception as e:
                logger.error(f"[{idx}/{total_cuentas}] ✗ Error extrayendo balance: {usuario}")
                if config.VERBOSE_LOGGING:
                    config.log_exception(logger, f"Error en extracción de balance para {usuario}")
    
    finally:
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
