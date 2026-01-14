# geminiBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "GEMINI"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def login(driver, usuario, password):
    form = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "form[method='POST']"))
    )
    user_input = form.find_element(By.CSS_SELECTOR, "input[name='login']")
    pwd_input = form.find_element(By.CSS_SELECTOR, "input[name='password']")
    user_input.clear()
    user_input.send_keys(usuario)
    pwd_input.clear()
    pwd_input.send_keys(password)
    driver.execute_script("arguments[0].submit();", form)
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "div.navbar-header"))
    )

def extraer_balance(driver):
    for _ in range(10):
        try:
            li = driver.find_element(By.CSS_SELECTOR, "li.main-balance")
            txt = li.text.strip()
            match = re.search(r"([\d,.]+)", txt)
            if match:
                balance = float(match.group(1).replace(",", ""))
                logger.info(f"Balance extraído: {balance}")
                print(f"Balance: {balance}")
                return balance
        except Exception as e:
            logger.warning(f"Error extrayendo balance: {e}")
        time.sleep(1)
    config.guardar_evidencia(driver.get_screenshot_as_png(), "gemini_no_balance")
    logger.warning("No se encontró el balance tras esperar. Ver evidencia en carpeta /screenshots")
    return None

def hacer_logout(driver):
    try:
        menu_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.menu-button.navbar-toggle"))
        )
        menu_btn.click()
        time.sleep(1)
        logout_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'area=logout') and contains(.,'Logout')]"))
        )
        logout_btn.click()
        logger.info("Logout realizado correctamente.")
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form[method='POST']"))
        )
        logger.info("Formulario de login visible tras logout.")
        time.sleep(1)
    except Exception as e:
        config.guardar_evidencia(driver.get_screenshot_as_png(), "gemini_logout_fail")
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
