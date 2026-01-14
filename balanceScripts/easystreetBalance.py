# easystreetBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "EASY STREET"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def resolver_captcha_easystreet(driver, max_retries=5):
    for _ in range(max_retries):
        imgs = driver.find_elements(By.XPATH, "//form[@class='am-form']//img[contains(@src, '/admin/captcha/')]")
        captcha_img = next((img for img in imgs if img.is_displayed()), None)
        if not captcha_img:
            raise Exception("No se encontró un captcha visible en EasyStreet.")
        WebDriverWait(driver, 10).until(
            lambda drv: driver.execute_script(
                "return arguments[0].complete && arguments[0].naturalWidth > 0;", captcha_img))
        captcha_bytes = captcha_img.screenshot_as_png
        try:
            captcha_val = config.resolver_captcha_2captcha(captcha_bytes, "easystreet")
            return captcha_val
        except Exception:
            time.sleep(2)
    raise Exception("No se pudo resolver el captcha de Easy Street")

def login(driver, usuario, password, max_captcha_attempts=4):
    for captcha_intento in range(max_captcha_attempts):
        form = WebDriverWait(driver, 20).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form.am-form"))
        )
        user_input = form.find_element(By.ID, "doc-ipt-email-1")
        pwd_input = form.find_element(By.ID, "doc-ipt-pwd-1")
        code_input = form.find_element(By.ID, "doc-ipt-code-1")
        user_input.clear()
        user_input.send_keys(usuario)
        pwd_input.clear()
        pwd_input.send_keys(password)
        captcha_val = resolver_captcha_easystreet(driver)
        code_input.clear()
        code_input.send_keys(captcha_val)
        driver.execute_script("arguments[0].submit();", form)
        try:
            WebDriverWait(driver, 10).until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, "header.am-topbar"))
            )
            return
        except Exception:
            logger.warning(f"Captcha fallado/relogin - intento {captcha_intento + 1} de {max_captcha_attempts}")
    raise Exception("No se pudo completar el login tras múltiples intentos de captcha")

def extraer_balance(driver):
    for _ in range(10):
        try:
            sess = driver.find_element(By.CSS_SELECTOR, "header.am-topbar .am-topbar-brand.am-hide-sm-only")
            spans = sess.find_elements(By.TAG_NAME, "span")
            for span in spans:
                txt = span.text
                match = re.search(r"Balance: ?\$([\d,]+\.\d{2})", txt)
                if match:
                    balance = float(match.group(1).replace(",", ""))
                    logger.info(f"Balance extraído: {balance}")
                    print(f"Balance: {balance}")
                    return balance
        except Exception as e:
            logger.warning(f"Error extrayendo balance: {e}")
        time.sleep(1)
    config.guardar_evidencia(driver.get_screenshot_as_png(), "easystreet_no_balance")
    logger.warning("No se encontró el balance tras esperar. Ver evidencia en carpeta /screenshots")
    return None

def hacer_logout(driver):
    try:
        logout_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href,'/admin/logout') and contains(.,'Logout')]"))
        )
        logout_btn.click()
        logger.info("Logout realizado correctamente.")
        WebDriverWait(driver, 15).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form.am-form"))
        )
        logger.info("Form de login visible y listo tras logout.")
        time.sleep(1)
    except Exception as e:
        config.guardar_evidencia(driver.get_screenshot_as_png(), "easystreet_logout_fail")
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
