# 100plusBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "100 PLUS"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def login(driver, usuario, password, second_password):
    form = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "form.login-form"))
    )
    user_input = form.find_element(By.CSS_SELECTOR, "input[name='username']")
    pwd_input = form.find_element(By.CSS_SELECTOR, "input[name='password']")
    user_input.clear()
    user_input.send_keys(usuario)
    pwd_input.clear()
    pwd_input.send_keys(password)
    btn_login = form.find_element(By.CSS_SELECTOR, "button.el-button--success")
    btn_login.click()
    try:
        second_form = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.XPATH, "//label[contains(text(),'2nd security')]"))
        )
        pwd2_input = driver.find_element(By.XPATH, "//label[contains(text(),'2nd security')]/..//input[@type='password']")
        pwd2_input.clear()
        pwd2_input.send_keys(second_password)
        btn_ok = driver.find_element(By.XPATH, "//button[span[contains(.,'OK')]]")
        btn_ok.click()
        logger.info("Segundo password enviado correctamente.")
    except Exception as e:
        logger.info("No se solicitó segundo password (puede ser cuenta especial o error): %s" % e)
    WebDriverWait(driver, 15).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".navbar .left-menu"))
    )

def extraer_balance(driver):
    for _ in range(10):
        try:
            tag = driver.find_element(By.XPATH, "//span[contains(text(),'My Score:')]")
            txt = tag.text.strip()
            match = re.search(r"([0-9]+\.[0-9]{2})", txt)
            if match:
                balance = float(match.group(1))
                logger.info(f"Balance extraído: {balance}")
                print(f"Balance: {balance}")
                return balance
        except Exception:
            pass
        time.sleep(1)
    config.guardar_evidencia(driver.get_screenshot_as_png(), "100plus_no_balance")
    logger.warning("No se encontró el balance tras esperar. Ver evidencia en carpeta /screenshots")
    return None

def hacer_logout(driver):
    try:
        hamburger = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "hamburger-container"))
        )
        hamburger.click()
        logout_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(@class,'signout-text') and contains(text(),'Sign out')]")
            )
        )
        logout_btn.click()
        ok_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.swal2-confirm"))
        )
        ok_btn.click()
        logger.info("Logout realizado correctamente (modal OK confirmado).")
        WebDriverWait(driver, 12).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form.login-form"))
        )
        logger.info("Form de login visible y listo tras logout.")
        time.sleep(1)
    except Exception as e:
        config.guardar_evidencia(driver.get_screenshot_as_png(), "100plus_logout_fail")
        logger.warning(f"No se pudo hacer logout; evidencia guardada. Error: {e}")

def main():
    sheet = config.google_sheets_connect()
    site = config.WEBSITES[WEBSITE_NAME]
    driver = None
    try:
        for cuenta in site["accounts"]:
            # SOLO usa el second_password si está en la cuenta
            second_password = cuenta["password2"] if "password2" in cuenta else None
            for intento in range(MAX_LOGIN_RETRIES):
                try:
                    if driver is None or not getattr(driver, "session_id", None):
                        if driver:
                            driver.quit()
                        driver = config.get_chrome_driver()
                    driver.get(site["url"])
                    time.sleep(1)
                    login(driver, cuenta["usuario"], cuenta["password"], second_password)
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
