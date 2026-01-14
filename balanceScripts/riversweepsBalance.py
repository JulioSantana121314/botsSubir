# riversweepsBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "River Sweeps"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def login(driver, usuario, password):
    form = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "form#yw0"))
    )
    user_input = form.find_element(By.ID, "LoginForm_login")
    pwd_input = form.find_element(By.ID, "LoginForm_password")
    user_input.clear()
    user_input.send_keys(usuario)
    pwd_input.clear()
    pwd_input.send_keys(password)
    btn = form.find_element(By.CSS_SELECTOR, "input[type='submit']")
    btn.click()
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.alert.alert-block"))
        )
    except Exception:
        raise Exception("No apareció el panel de balance tras login, reintentar.")

def extraer_balance(driver):
    for _ in range(10):
        try:
            alert = driver.find_element(By.CSS_SELECTOR, "div.alert.alert-block")
            b_tags = alert.find_elements(By.TAG_NAME, "b")
            for b in b_tags:
                raw = b.text.strip()
                if raw.lower().endswith("usd"):
                    num_str = re.sub(r"[^\d.]", "", raw)
                    if num_str:
                        balance = float(num_str)
                        logger.info(f"Balance extraído: {balance}")
                        print(f"Balance: {balance}")
                        return balance
        except Exception:
            pass
        time.sleep(1)
    config.guardar_evidencia(driver.get_screenshot_as_png(), "riversweeps_no_balance")
    logger.warning("No se encontró el balance tras esperar. Ver evidencia en carpeta /screenshots")
    return None

def hacer_logout(driver):
    try:
        logout_sidebar = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "div.well.well-small ul.nav-list a[href='/office/logout']")
            )
        )
        logout_sidebar.click()
        logger.info("Logout realizado correctamente mediante link de logout (sidebar).")
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form#yw0"))
        )
        logger.info("Form de login visible y listo tras logout.")
        time.sleep(1)
    except Exception as e:
        config.guardar_evidencia(driver.get_screenshot_as_png(), "riversweeps_logout_fail")
        logger.warning(f"No se pudo hacer logout; evidencia guardada. Error: {e}")

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
                    login(driver, cuenta["usuario"], cuenta["password"])
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
