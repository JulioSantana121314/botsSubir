# highstakesBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "HIGHSTAKES"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def login_con_captcha(driver, usuario, password):
    form = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "form.login-container"))
    )
    inputs = form.find_elements(By.CSS_SELECTOR, "input.el-input__inner")
    user_input = [i for i in inputs if "account" in (i.get_attribute('placeholder') or "")][0]
    pwd_input = [i for i in inputs if "password" in (i.get_attribute('placeholder') or "")][0]
    captcha_input = [i for i in inputs if "verification code" in (i.get_attribute('placeholder') or "")][0]

    user_input.clear()
    user_input.send_keys(usuario)
    pwd_input.clear()
    pwd_input.send_keys(password)
    captcha_img = form.find_element(By.CSS_SELECTOR, "img.imgCode")
    captcha_bytes = captcha_img.screenshot_as_png
    solucion = config.resolver_captcha_2captcha(captcha_bytes, "highstakes")
    captcha_input.clear()
    captcha_input.send_keys(solucion)
    btn_form = form.find_element(By.CSS_SELECTOR, "button.el-button--primary")
    btn_form.click()

def extraer_balance_header(driver):
    for intento in range(20):
        try:
            balance_elem = driver.find_element(
                By.XPATH, "//span[contains(@class, 'balance') and contains(.,'Balance:')]/span")
            balance_str = balance_elem.text.strip()
            match = re.search(r"[0-9,\.]+", balance_str)
            if match:
                balance = float(match.group().replace(',', ''))
                logger.info(f"Balance encabezado extraído: {balance}")
                print(f"Balance encabezado: {balance}")
                return balance
        except Exception:
            pass
        time.sleep(1)
    config.guardar_evidencia(driver.get_screenshot_as_png(), "highstakes_no_balance_header")
    logger.warning("No se encontró el balance en el header tras esperar. Ver evidencia en carpeta /screenshots")
    return None

def main():
    sheet = config.google_sheets_connect()
    site = config.WEBSITES[WEBSITE_NAME]
    driver = None
    try:
        for cuenta in site["accounts"]:
            for intento in range(MAX_LOGIN_RETRIES):
                try:
                    if driver is None or not getattr(driver, "session_id", None):
                        if driver:
                            driver.quit()
                        driver = config.get_chrome_driver()
                    driver.get(site["url"])
                    time.sleep(1)
                    login_con_captcha(driver, cuenta["usuario"], cuenta["password"])
                    logger.info(f"Login exitoso para usuario {cuenta['usuario']}")
                    break
                except WebDriverException as e:
                    if "invalid session id" in str(e).lower():
                        if driver:
                            driver.quit()
                        driver = config.get_chrome_driver()
                    logger.warning(f"Intento {intento + 1} fallido para usuario {cuenta['usuario']}: {e}")
                    time.sleep(2)
                except Exception as e:
                    logger.warning(f"Intento {intento + 1} fallido para usuario {cuenta['usuario']}: {e}")
                    time.sleep(2)
            else:
                logger.warning(f"No se pudo iniciar sesión después de {MAX_LOGIN_RETRIES} intentos para {cuenta['usuario']}")
                continue
            time.sleep(3)
            balance = extraer_balance_header(driver)
            hora_login = config.get_current_timestamp()
            if balance is not None:
                config.enviar_resultado_balance(sheet, WEBSITE_NAME, cuenta["usuario"], hora_login, balance)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
