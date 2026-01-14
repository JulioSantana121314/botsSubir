# firephoenixBalance.py — versión 1.1 (centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from datetime import datetime
import config


WEBSITE_NAME = "Fire Phoenix"
logger = config.get_logger(f"{WEBSITE_NAME}_bot")


def login_firephoenix(driver, usuario, password):
    """Realiza login en Fire Phoenix"""
    try:
        wait = WebDriverWait(driver, 20)
        
        # Esperar a que el formulario esté visible
        usuario_input = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input#userName[name='username']"))
        )
        password_input = driver.find_element(By.CSS_SELECTOR, "input#passWd[name='password']")
        login_button = driver.find_element(By.CSS_SELECTOR, "button#loginButton")
        
        # Llenar formulario
        usuario_input.clear()
        usuario_input.send_keys(usuario)
        password_input.clear()
        password_input.send_keys(password)
        
        # Click en login
        login_button.click()
        logger.info(f"Login ejecutado para usuario {usuario}")
        
        # Esperar a que desaparezca el formulario de login y aparezca el header con el balance
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.badge.bg-aqua#n3"))
        )
        logger.info(f"Login exitoso para usuario {usuario}")
        time.sleep(1)
        
    except TimeoutException:
        logger.error(f"Timeout esperando elementos de login para {usuario}")
        config.guardar_evidencia(driver.get_screenshot_as_png(), f"firephoenix_login_timeout_{usuario}")
        raise
    except Exception as e:
        logger.error(f"Error en login para {usuario}: {e}")
        config.guardar_evidencia(driver.get_screenshot_as_png(), f"firephoenix_login_error_{usuario}")
        raise


def extraer_balance_y_usuario(driver):
    """Extrae el balance y username del header"""
    try:
        wait = WebDriverWait(driver, 10)
        
        # Extraer username
        username_elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.m_uid"))
        )
        username = username_elem.text.strip()
        
        # Extraer balance
        balance_elem = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "span.badge.bg-aqua#n3"))
        )
        texto_balance = balance_elem.text.strip()
        
        # Parsear balance - formato: "score: 7,059.00"
        match = re.search(r'score:\s*([0-9,\.]+)', texto_balance)
        if match:
            balance_str = match.group(1).replace(',', '')
            balance = float(balance_str)
        else:
            logger.warning(f"No se pudo parsear el balance del texto: '{texto_balance}'")
            return None, None
        
        if balance is not None and username:
            logger.info(f"Balance extraído: {balance}, Usuario: {username}")
            print(f"Balance: {balance}, Usuario: {username}")
            return balance, username
        else:
            logger.warning("No se encontró balance o usuario correctamente")
            return None, None
            
    except TimeoutException:
        logger.error("Timeout esperando balance o usuario en el header")
        config.guardar_evidencia(driver.get_screenshot_as_png(), "firephoenix_balance_timeout")
        return None, None
    except Exception as e:
        logger.error(f"Error extrayendo balance o usuario: {e}")
        config.guardar_evidencia(driver.get_screenshot_as_png(), "firephoenix_balance_error")
        return None, None


def confirmar_logout_modal(driver):
    """Confirma el modal de logout presionando 'Yes!'"""
    try:
        wait = WebDriverWait(driver, 5)
        
        # Esperar a que aparezca el modal de confirmación
        modal = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.sweet-alert.showSweetAlert.visible"))
        )
        logger.info("Modal de confirmación de logout detectado")
        
        # Buscar y hacer click en el botón "Yes!"
        yes_button = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.sa-confirm-button-container button.confirm"))
        )
        
        try:
            yes_button.click()
        except Exception:
            # Si el click normal falla, intentar con JavaScript
            driver.execute_script("arguments[0].click();", yes_button)
        
        logger.info("Confirmación de logout aceptada (botón 'Yes!' presionado)")
        time.sleep(1)
        
    except TimeoutException:
        logger.warning("No apareció modal de confirmación de logout o ya fue cerrado")
    except Exception as e:
        logger.error(f"Error al confirmar modal de logout: {e}")
        config.guardar_evidencia(driver.get_screenshot_as_png(), "firephoenix_confirm_logout_error")


def logout(driver):
    """Realiza logout de Fire Phoenix"""
    try:
        wait = WebDriverWait(driver, 10)
        
        # Buscar el botón Sign out
        signout_link = wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a#li_signOut"))
        )
        signout_link.click()
        logger.info("Botón 'Sign out' presionado")
        
        # Confirmar el modal de logout
        confirmar_logout_modal(driver)
        
        # Esperar a que aparezca nuevamente el formulario de login
        wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "button#loginButton"))
        )
        logger.info("Logout completado, formulario de login visible")
        time.sleep(2)
        
    except TimeoutException:
        logger.warning("Timeout esperando logout o retorno al login")
        config.guardar_evidencia(driver.get_screenshot_as_png(), "firephoenix_logout_timeout")
    except Exception as e:
        logger.error(f"Error realizando logout: {e}")
        config.guardar_evidencia(driver.get_screenshot_as_png(), "firephoenix_logout_error")


def main():
    logger.info(f"Iniciando navegador Chrome para {WEBSITE_NAME}")
    driver = config.get_chrome_driver()
    sheet = config.google_sheets_connect()
    url_login = config.WEBSITES[WEBSITE_NAME]["url"]
    cuentas = config.WEBSITES[WEBSITE_NAME]["accounts"]
    
    try:
        for cuenta in cuentas:
            usuario = cuenta['usuario']
            password = cuenta['password']
            logger.info(f"Procesando cuenta {usuario}...")
            
            try:
                # Cargar página de login
                driver.get(url_login)
                time.sleep(2)
                
                # Login
                login_firephoenix(driver, usuario, password)
                
                # Capturar timestamp inmediatamente después del login exitoso
                hora_login = config.get_current_timestamp()
                
                # Extraer balance y usuario
                balance, username = extraer_balance_y_usuario(driver)
                
                # Enviar a MongoDB si se obtuvo el balance
                if balance is not None and username is not None:
                    config.enviar_resultado_balance(
                        sheet, WEBSITE_NAME, username, hora_login, balance
                    )
                else:
                    logger.warning(f"No se pudo registrar balance para {usuario}")
                
                # Logout
                logout(driver)
                
            except Exception as e:
                logger.error(f"Error procesando cuenta {usuario}: {e}")
                config.log_exception(logger, f"Excepción en cuenta {usuario}")
                # Intentar logout de emergencia
                try:
                    logout(driver)
                except:
                    pass
                continue
        
        logger.info("Proceso completo para todas las cuentas.")
        
    finally:
        if driver:
            driver.quit()
            logger.info("Navegador cerrado.")


if __name__ == "__main__":
    main()
