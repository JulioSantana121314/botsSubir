"""
Platform Grupo 1 - Lógica centralizada para websites con estructura similar.
Sitios compatibles: MILKY WAY, ORION STARS, FIRE KIRIN, etc.

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
    Cierra popups de sesión expirada.
    ✅ Usa explicit wait con timeout de 1 segundo
    """
    try:
        # ✅ Esperar máximo 1 segundo a que aparezca el popup
        wait = WebDriverWait(driver, 1)
        ok_btn = wait.until(EC.presence_of_element_located((By.ID, "mb_btn_ok")))
        
        if ok_btn.is_displayed():
            ok_btn.click()
            time.sleep(0.3)
            if config.VERBOSE_LOGGING:
                logger.debug("[POPUP] Popup cerrado")
    except:
        # No hay popup o timeout, continuar normalmente
        pass
def resolver_captcha(driver, website_name_prefix, logger):
    """
    Resuelve captcha usando imagen con ID 'ImageCheck' e input 'txtVerifyCode'.
    ✅ Usa detección automática de grupo desde config.py
    """
    try:
        captcha_img = driver.find_element(By.ID, "ImageCheck")
        captcha_bytes = captcha_img.screenshot_as_png
        
        # ✅ config.resolver_captcha_2captcha detecta automáticamente el grupo
        solucion = config.resolver_captcha_2captcha(captcha_bytes, website_name_prefix.lower())
        
        if not solucion:
            logger.warning(f"[CAPTCHA] No se obtuvo solución")
            return False
        
        input_code = driver.find_element(By.ID, "txtVerifyCode")
        input_code.clear()
        input_code.send_keys(solucion)
        return True
        
    except Exception as e:
        logger.error(f"[CAPTCHA] Error: {e}")
        if config.VERBOSE_LOGGING:
            config.log_exception(logger, "Error en resolver_captcha")
        return False

def close_popup_optimizado(driver, logger):
    """
    Cierra popup post-login con botón ID 'cancelBtn'.
    ✅ Optimizado: Verifica si existe antes de intentar múltiples veces
    """
    try:
        # ✅ Intentar encontrar el botón UNA SOLA VEZ
        cancel_btn = driver.find_element(By.ID, "cancelBtn")
        if cancel_btn.is_displayed():
            cancel_btn.click()
            if config.VERBOSE_LOGGING:
                logger.debug("[POPUP] Popup post-login cerrado")
    except NoSuchElementException:
        # No hay popup, esto es normal
        pass
    except Exception as e:
        if config.VERBOSE_LOGGING:
            logger.debug(f"[POPUP] No se pudo cerrar: {e}")

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
            return balance, username
        else:
            logger.warning("[EXTRACT] Balance o usuario es None")
            return None, None
            
    except Exception as e:
        logger.error(f"[EXTRACT] Error: {e}")
        if config.VERBOSE_LOGGING:
            config.log_exception(logger, "Error en extraer_balance_y_usuario")
        return None, None

def logout(driver, logger):
    """
    Realiza logout navegando directamente a LoginOut.aspx.
    ✅ Más simple, rápido y confiable que buscar el botón
    """
    try:
        # Obtener URL base (http://domain.com)
        current_url = driver.current_url
        base_url = '/'.join(current_url.split('/')[:3])
        logout_url = f"{base_url}/LoginOut.aspx"
        
        # Navegar directamente al logout
        driver.get(logout_url)
        
        if config.VERBOSE_LOGGING:
            logger.debug(f"[LOGOUT] Navegando a: {logout_url}")
        
        # Esperar a que aparezca la página de login (confirma logout exitoso)
        time.sleep(2)
        
        try:
            driver.find_element(By.ID, "txtLoginName")
            logger.info("[LOGOUT] ✓ Logout completado")
            return True
        except NoSuchElementException:
            logger.warning("[LOGOUT] ⚠️ No se detectó página de login, pero logout ejecutado")
            return True  # Asumir éxito
        
    except Exception as e:
        logger.error(f"[LOGOUT] ✗ Error: {e}")
        return False

def login_and_check(driver, website_name, usuario, password, max_retries, logger):
    """
    Intenta login con reintentos automáticos.
    ✅ Optimizado: Espera inteligente en lugar de time.sleep fijos
    """
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
                if config.VERBOSE_LOGGING:
                    logger.warning(f"[LOGIN] Intento {intento + 1}/{max_retries} - Captcha falló")
                time.sleep(2)
                continue
            
            # Click en login
            driver.find_element(By.ID, "btnLogin").click()
            
            # ✅ OPTIMIZACIÓN: Esperar a que DESAPAREZCA el botón de login
            # (indica que la página cambió después del login)
            wait = WebDriverWait(driver, 10)
            try:
                wait.until(EC.staleness_of(driver.find_element(By.ID, "btnLogin")))
            except:
                pass  # Si ya no existe, continuar
            
            # ✅ OPTIMIZACIÓN: Esperar a que aparezca UserBalance (confirma login exitoso)
            try:
                wait.until(EC.presence_of_element_located((By.ID, "UserBalance")))
            except:
                # Si no aparece UserBalance en 10s, el login probablemente falló
                if config.VERBOSE_LOGGING:
                    logger.warning(f"[LOGIN] UserBalance no apareció, posible login fallido")
                time.sleep(1)
                continue
            
            # ✅ Cerrar popup post-login (optimizado)
            close_popup_optimizado(driver, logger)
            
            # Extraer balance y usuario (ahora sabemos que existen)
            balance, username = extraer_balance_y_usuario(driver, logger)
            
            if balance is not None and username:
                logger.info(f"[LOGIN] ✓ Login exitoso: {usuario}")
                return balance, username
            else:
                if config.VERBOSE_LOGGING:
                    logger.warning(f"[LOGIN] Intento {intento + 1}/{max_retries} - No se pudo extraer datos")
                
        except Exception as e:
            logger.warning(f"[LOGIN] Intento {intento + 1}/{max_retries} - Error: {e}")
            if config.VERBOSE_LOGGING:
                config.log_exception(logger, f"Error en login intento {intento + 1}")
            time.sleep(2)
    
    logger.error(f"[LOGIN] ✗ Login falló tras {max_retries} intentos: {usuario}")
    return None, None
def run(website_name, max_login_retries=4):
    """
    Función principal para ejecutar el bot.
    ✅ Logging limpio + manejo robusto de driver
    """
    logger = get_logger(website_name)
    
    logger.info("="*70)
    logger.info(f"🚀 Iniciando scraping: {website_name}")
    logger.info("="*70)
    
    driver = None
    exitosos = 0
    
    try:
        # Verificar que el website existe
        if website_name not in config.WEBSITES:
            logger.error(f"✗ Website '{website_name}' no encontrado en diccionario")
            return
        
        cuentas = config.WEBSITES[website_name]["accounts"]
        total_cuentas = len(cuentas)
        
        logger.info(f"Total de cuentas: {total_cuentas}")
        
        # Inicializar driver
        driver = config.get_chrome_driver()
        sheet = None
        if config.EXPORT_MODE.upper() == "SHEET":
            sheet = config.google_sheets_connect()
        
        # Procesar cada cuenta
        for idx, cuenta in enumerate(cuentas, 1):
            usuario = cuenta['usuario']
            password = cuenta['password']
            
            logger.info(f"[{idx}/{total_cuentas}] Procesando: {usuario}")
            
            # Intentar login y extraer balance
            balance, username = login_and_check(
                driver, website_name, usuario, password, max_login_retries, logger
            )
            
            # Si login exitoso, registrar balance
            if balance is not None and username is not None:
                config.enviar_resultado_balance(
                    sheet=sheet,
                    website=website_name,
                    username=username,
                    balance=balance
                )
                exitosos += 1
                logger.info(f"[{idx}/{total_cuentas}] ✓ Completado: {usuario}")
            else:
                logger.error(f"[{idx}/{total_cuentas}] ✗ No se pudo obtener balance: {usuario}")
            
            # Logout (no crítico si falla)
            logout(driver, logger)
            
            # Delay entre cuentas
            if idx < total_cuentas:
                time.sleep(2)
        
    except Exception as e:
        logger.error(f"✗ Error fatal: {e}")
        if config.VERBOSE_LOGGING:
            config.log_exception(logger, "Error fatal en run()")
        
    finally:
        # ✅ CERRAR DRIVER DE FORMA SEGURA
        if driver:
            try:
                driver.quit()
                if config.VERBOSE_LOGGING:
                    logger.debug("[DRIVER] Driver cerrado correctamente")
            except Exception as e:
                # ✅ Ignorar errores al cerrar driver (no son críticos)
                if config.VERBOSE_LOGGING:
                    logger.debug(f"[DRIVER] Error cerrando driver (no crítico): {e}")
        
        # Resumen final
        logger.info("="*70)
        logger.info(f"✓ {website_name} completado ({exitosos}/{total_cuentas} exitosos)")
        logger.info("="*70)

if __name__ == "__main__":
    print("Este archivo contiene lógica centralizada.")
    print("Ejecuta los scripts individuales (ej: milkywayBalance.py)")
