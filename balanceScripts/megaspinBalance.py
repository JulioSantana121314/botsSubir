# megaspinBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "MEGA SPIN"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def login(driver, usuario, password):
    form = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "form#ctl00"))
    )
    user_input = form.find_element(By.CSS_SELECTOR, "input[name='txtLoginName']")
    pwd_input = form.find_element(By.CSS_SELECTOR, "input[name='txtLoginPass']")
    user_input.clear()
    user_input.send_keys(usuario)
    pwd_input.clear()
    pwd_input.send_keys(password)
    btn = form.find_element(By.CSS_SELECTOR, "input[name='btnLogin']")
    btn.click()
    time.sleep(0.7)
    if driver.find_elements(By.CSS_SELECTOR, "form#ctl00"):
        raise Exception("El form de login sigue tras intentar login; posible sesión previa activa/race. Reintentar.")

def extraer_balance(driver):
    try:
        WebDriverWait(driver, 8).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frm_left_frm"))
        )
        for _ in range(8):
            try:
                balance_elem = driver.find_element(By.ID, "balance")
                balance_str = balance_elem.text
                match = re.search(r"[0-9,\.]+", balance_str)
                if match:
                    balance = float(match.group().replace(',', ''))
                    logger.info(f"Balance extraído: {balance}")
                    print(f"Balance: {balance}")
                    driver.switch_to.default_content()
                    return balance
            except Exception:
                pass
            time.sleep(1)
        config.guardar_evidencia(driver.get_screenshot_as_png(), "megaspin_no_balance")
        logger.warning("No se encontró el balance tras esperar. Ver evidencia en carpeta /screenshots")
        driver.switch_to.default_content()
        return None
    except Exception as e:
        driver.switch_to.default_content()
        raise e

def hacer_logout(driver):
    try:
        WebDriverWait(driver, 8).until(
            EC.frame_to_be_available_and_switch_to_it((By.ID, "frm_left_frm"))
        )
        logout_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@onclick,\"LoginOut.aspx\") and contains(.,'Logout')]"))
        )
        logout_link.click()
        logger.info("Logout realizado correctamente mediante link de logout.")
        driver.switch_to.default_content()
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form#ctl00"))
        )
        logger.info("Form de login visible y listo tras logout.")
        time.sleep(1)
    except Exception as e:
        config.guardar_evidencia(driver.get_screenshot_as_png(), "megaspin_logout_fail")
        driver.switch_to.default_content()
        logger.warning(f"No se pudo hacer logout; evidencia guardada. Error: {e}")

def main():
    sheet = config.google_sheets_connect()
    site = config.WEBSITES[WEBSITE_NAME]
    driver = None
    try:
        driver = config.get_chrome_driver()
        for cuenta in site["accounts"]:
            for intento in range(MAX_LOGIN_RETRIES):
                try:
                    driver.get(site["url"])
                    time.sleep(1)
                    login(driver, cuenta["usuario"], cuenta["password"])
                    WebDriverWait(driver, 8).until(
                        EC.frame_to_be_available_and_switch_to_it((By.ID, "frm_left_frm"))
                    )
                    WebDriverWait(driver, 8).until(
                        EC.visibility_of_element_located((By.ID, "balance"))
                    )
                    driver.switch_to.default_content()
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
            balance = extraer_balance(driver)
            hora_login = config.get_current_timestamp()
            if balance is not None:
                config.enviar_resultado_balance(sheet, WEBSITE_NAME, cuenta["usuario"], hora_login, balance)
            hacer_logout(driver)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
