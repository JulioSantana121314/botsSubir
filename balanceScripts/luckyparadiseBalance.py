# luckyparadiseBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException, TimeoutException
from datetime import datetime
import config

WEBSITE_NAME = "LUCKY PARADISE"
MAX_LOGIN_RETRIES = 5
logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def cerrar_modal_tips(driver):
    try:
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".layui-layer.layui-layer-page")))
        confirm_btn = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".layui-layer-btn0"))
        )
        confirm_btn.click()
        logger.info("Modal Tips/Confirm detectado y cerrado.")
        time.sleep(0.7)
    except TimeoutException:
        pass
    except Exception as e:
        logger.warning(f"Error al cerrar el modal Tips: {e}")

def resolver_captcha_luckyparadise(driver, max_retries=5):
    for intento in range(max_retries):
        captcha_canvas = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "verifyCanvas")))
        captcha_bytes = captcha_canvas.screenshot_as_png
        solucion = config.resolver_captcha_2captcha(captcha_bytes, "luckyparadise")
        input_captcha = driver.find_element(By.ID, "captcha")
        input_captcha.clear()
        input_captcha.send_keys(solucion)
        return True
    raise Exception("Error resolviendo captcha después de múltiples intentos")

def login(driver, usuario, password):
    form = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "form.layui-form"))
    )
    user_input = form.find_element(By.ID, "username")
    pwd_input = form.find_element(By.ID, "password")
    user_input.clear()
    user_input.send_keys(usuario)
    pwd_input.clear()
    pwd_input.send_keys(password)
    resolver_captcha_luckyparadise(driver)
    btn_login = form.find_element(By.ID, "loginBtn")
    btn_login.click()
    WebDriverWait(driver, 15).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "mainBody"))
    )
    driver.switch_to.default_content()

def extraer_balance(driver):
    WebDriverWait(driver, 10).until(
        EC.frame_to_be_available_and_switch_to_it((By.ID, "mainBody"))
    )
    for _ in range(8):
        try:
            balance_elem = driver.find_element(By.ID, "balance")
            txt = balance_elem.text.strip()
            match = re.search(r"([0-9]+(\.[0-9]{2})?)", txt)
            if match:
                balance = float(match.group(1))
                logger.info(f"Balance extraído: {balance}")
                print(f"Balance: {balance}")
                driver.switch_to.default_content()
                return balance
        except Exception:
            pass
        time.sleep(1)
    config.guardar_evidencia(driver.get_screenshot_as_png(), "luckyparadise_no_balance")
    logger.warning("No se encontró el balance tras esperar. Ver evidencia en carpeta /screenshots")
    driver.switch_to.default_content()
    return None

def hacer_logout(driver):
    try:
        driver.switch_to.default_content()
        logout_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "logout"))
        )
        time.sleep(1.2)
        logout_btn.click()
        logger.info("Logout realizado correctamente.")
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form.layui-form"))
        )
        logger.info("Formulario de login visible tras logout.")
    except Exception as e:
        config.guardar_evidencia(driver.get_screenshot_as_png(), "luckyparadise_logout_fail")
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
                    cerrar_modal_tips(driver)
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
