# juwaBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "JUWA"
MAX_LOGIN_RETRIES = 4
MAX_CAPTCHA_RETRIES = 4

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def resolver_captcha_juwa(driver, max_retries=MAX_CAPTCHA_RETRIES):
    for intento in range(max_retries):
        try:
            time.sleep(1.5)
            captcha_img = driver.find_element(By.CLASS_NAME, "imgCode")
            captcha_bytes = captcha_img.screenshot_as_png
            solucion = config.resolver_captcha_2captcha(captcha_bytes, "juwa")
            input_captcha = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Please enter the verification code']")
            input_captcha.clear()
            input_captcha.send_keys(solucion)
            return True
        except Exception as e:
            logger.warning(f"Error resolviendo captcha Juwa: {e}")
            time.sleep(1.5)
    raise Exception("Error resolviendo captcha Juwa después de múltiples intentos")

def extraer_balance_juwa(driver):
    try:
        balance_elem = driver.find_element(By.CSS_SELECTOR, ".balance span")
        texto = balance_elem.text.strip()
        match = re.search(r"[\d,\.]+", texto)
        if match:
            balance = float(match.group().replace(',', ''))
            logger.info(f"Balance extraído: {balance}")
            print(f"Balance: {balance}")
            return balance
    except Exception as e:
        logger.error(f"Error extrayendo balance Juwa: {e}")
    return None

def logout_juwa(driver):
    try:
        time.sleep(1)
        logout_btn = driver.find_element(By.XPATH, "//button[contains(text(),'log out') or contains(text(),'Log out')]")
        logout_btn.click()
        logger.info("Logout realizado correctamente.")
    except Exception:
        logger.warning("No se encontró botón de logout o error al hacer logout.")

def login_and_check(driver, usuario, password):
    time.sleep(1.5)
    for intento in range(MAX_LOGIN_RETRIES):
        try:
            driver.get(config.WEBSITES[WEBSITE_NAME]["url"])
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder='Please enter your account']"))
            )
            usuario_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Please enter your account']")
            pass_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='Please enter your password']")
            usuario_input.clear()
            usuario_input.send_keys(usuario)
            pass_input.clear()
            pass_input.send_keys(password)
            resolver_captcha_juwa(driver)
            signin_btn = driver.find_element(By.XPATH, "//button[.//span[text()='Sign in']]")
            signin_btn.click()
            time.sleep(2.7)
            if driver.current_url == config.WEBSITES[WEBSITE_NAME]["url"] or "login" in driver.current_url.lower():
                logger.info(f"Intento {intento + 1} fallido para usuario {usuario}, reintentando...")
                continue
            else:
                logger.info(f"Login exitoso para usuario {usuario}")
                return True
        except Exception as e:
            logger.warning(f"Error en login/captcha para usuario {usuario}: {e}")
            time.sleep(1)
    logger.error(f"No se pudo iniciar sesión después de {MAX_LOGIN_RETRIES} intentos para {usuario}")
    return False

def main():
    sheet = config.google_sheets_connect()
    site = config.WEBSITES[WEBSITE_NAME]
    driver = None
    try:
        driver = config.get_chrome_driver()
        for cuenta in site["accounts"]:
            logged = login_and_check(driver, cuenta["usuario"], cuenta["password"])
            if not logged:
                continue
            balance = extraer_balance_juwa(driver)
            hora_login = config.get_current_timestamp()
            if balance is not None:
                config.enviar_resultado_balance(sheet, WEBSITE_NAME, cuenta["usuario"], hora_login, balance)
            logout_juwa(driver)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
