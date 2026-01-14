# galaxyworldBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import config

WEBSITE_NAME = "GALAXY WORLD"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def resolver_captcha_gamevault(driver, max_retries=5):
    for intento in range(max_retries):
        captcha_img = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "imgCode")))
        captcha_bytes = captcha_img.screenshot_as_png
        solucion = config.resolver_captcha_2captcha(captcha_bytes, "galaxyworld")
        input_captcha = driver.find_elements(By.CSS_SELECTOR, "input.el-input__inner")[2]
        input_captcha.clear()
        input_captcha.send_keys(solucion)
        return True
    raise Exception("Error resolviendo captcha Galaxy World después de múltiples intentos")

def login_gamevault(driver, usuario, password):
    usuario_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='username']")
    pass_input = driver.find_element(By.CSS_SELECTOR, "input[placeholder='password']")
    usuario_input.clear()
    usuario_input.send_keys(usuario)
    pass_input.clear()
    pass_input.send_keys(password)

def click_sign_in(driver):
    time.sleep(1.0)
    signin_btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, "div.login-btn > button.el-button--primary"))
    )
    signin_btn.click()

def ir_admin_list(driver):
    wait = WebDriverWait(driver, 20)
    admin_icon = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "i.el-icon-user-solid")))
    admin_btn = admin_icon.find_element(By.XPATH, "./..")
    admin_btn.click()
    logger.info("Click a Admin List con el ícono de usuario.")
    time.sleep(2)

def extraer_balance_header_gamevault(driver):
    for intento in range(30):
        try:
            balance_elem = driver.find_element(
                By.XPATH, "//button[contains(@class,'el-button--default') and contains(.,'Balance:')]/span/span")
            balance_str = balance_elem.text.strip()
        except Exception:
            try:
                balance_elem = driver.find_element(
                    By.XPATH, "//button[contains(@class,'el-button--default') and contains(.,'Balance:')]//span[@style]")
                balance_str = balance_elem.text.strip()
            except Exception:
                balance_str = ""
        match = re.search(r"[0-9,\.]+", balance_str)
        if match and balance_str != "":
            balance = float(match.group().replace(',', ''))
            logger.info(f"Balance encabezado extraído: {balance}")
            print(f"Balance encabezado: {balance}")
            return balance
        time.sleep(1)
    config.guardar_evidencia(driver.get_screenshot_as_png(), "galaxyworld_no_balance_header")
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
                    login_gamevault(driver, cuenta["usuario"], cuenta["password"])
                    resolver_captcha_gamevault(driver)
                    click_sign_in(driver)
                    time.sleep(8)
                    if driver.current_url == site["url"] or "login" in driver.current_url.lower():
                        logger.info(f"Intento {intento + 1} fallido para usuario {cuenta['usuario']}, reintentando...")
                        time.sleep(2)
                        continue
                    else:
                        logger.info(f"Login exitoso para usuario {cuenta['usuario']}")
                        break
                except Exception as e:
                    logger.warning(f"Intento {intento + 1} fallido para usuario {cuenta['usuario']}: {e}")
                    time.sleep(2)
            else:
                logger.warning(f"No se pudo iniciar sesión después de {MAX_LOGIN_RETRIES} intentos para {cuenta['usuario']}")
                continue
            ir_admin_list(driver)
            balance = extraer_balance_header_gamevault(driver)
            hora_login = config.get_current_timestamp()
            if balance is not None:
                config.enviar_resultado_balance(sheet, WEBSITE_NAME, cuenta["usuario"], hora_login, balance)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
