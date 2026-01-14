# mafiaBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "MAFIA"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def login_con_captcha(driver, usuario, password):
    form = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "form.layui-form"))
    )
    user_input = form.find_element(By.CSS_SELECTOR, "input[name='username']")
    pwd_input = form.find_element(By.CSS_SELECTOR, "input[name='password']")
    captcha_input = form.find_element(By.CSS_SELECTOR, "input[name='captcha']")
    user_input.clear()
    user_input.send_keys(usuario)
    pwd_input.clear()
    pwd_input.send_keys(password)
    captcha_box = form.find_element(By.ID, "captchaImg")
    driver.execute_script("arguments[0].scrollIntoView();", captcha_box)
    time.sleep(0.5)
    captcha_bytes = captcha_box.screenshot_as_png
    solucion = config.resolver_captcha_2captcha(captcha_bytes, "mafia")
    captcha_input.clear()
    captcha_input.send_keys(solucion)
    btn_form = form.find_element(By.CSS_SELECTOR, "button.layui-btn")
    btn_form.click()

def extraer_balance_header(driver):
    for intento in range(5):
        try:
            balance_elem = driver.find_element(By.ID, "money")
            balance_str = balance_elem.text.strip()
            match = re.search(r"[0-9,\.]+", balance_str)
            if match:
                balance = float(match.group().replace(',', ''))
                logger.info(f"Balance extraído: {balance}")
                print(f"Balance: {balance}")
                return balance
        except Exception:
            pass
        time.sleep(1)
    config.guardar_evidencia(driver.get_screenshot_as_png(), "mafia_no_balance_header")
    logger.warning("No se encontró el balance tras esperar. Ver evidencia en carpeta /screenshots")
    return None

def hacer_logout(driver):
    try:
        avatar_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[img[contains(@class, 'layui-nav-img')]]"))
        )
        avatar_btn.click()
        time.sleep(1)
        logout_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "logout"))
        )
        logout_btn.click()
        time.sleep(1)
        confirm_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a.layui-layer-btn0"))
        )
        confirm_btn.click()
        logger.info("Logout realizado correctamente con confirmación.")
        time.sleep(2)
    except Exception as e:
        config.guardar_evidencia(driver.get_screenshot_as_png(), "mafia_logout_fail")
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
                    login_con_captcha(driver, cuenta["usuario"], cuenta["password"])
                    WebDriverWait(driver, 5).until(EC.visibility_of_element_located((By.ID, "money")))
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
            balance = extraer_balance_header(driver)
            hora_login = config.get_current_timestamp()
            if balance is not None:
                config.enviar_resultado_balance(sheet, WEBSITE_NAME, cuenta["usuario"], hora_login, balance)
            hacer_logout(driver)
            time.sleep(2)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
