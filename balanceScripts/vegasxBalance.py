# vegasxBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "VEGAS X"
MAX_LOGIN_RETRIES = 5

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def cerrar_modal_si_aparece(driver):
    try:
        btn_modal = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(.,\"Don't show again\")]"))
        )
        btn_modal.click()
        logger.info("Se cerró el modal de bono")
        time.sleep(1)
    except Exception:
        pass

def abrir_sidebar(driver):
    toggler = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, ".content-panel-toggler"))
    )
    toggler.click()
    logger.info("Sidebar abierto")
    time.sleep(1)

def extraer_credits_sidebar(driver):
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.ID, "logs"))
    )
    for _ in range(5):
        try:
            credits_elem = driver.find_element(By.CSS_SELECTOR, ".value.top_credits")
            credits_str = credits_elem.text.strip()
            match = re.search(r"[0-9,\.]+", credits_str)
            if match:
                credits = float(match.group().replace(',', ''))
                logger.info(f"Credits extraídos: {credits}")
                print(f"Credits: {credits}")
                return credits
        except Exception:
            pass
        time.sleep(1)
    config.guardar_evidencia(driver.get_screenshot_as_png(), "vegasx_sidebar_no_credits")
    logger.warning("No se encontró el balance en el sidebar tras esperar. Ver evidencia en carpeta /screenshots")
    return None

def cerrar_sidebar(driver):
    try:
        cerrar_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".content-panel-close"))
        )
        cerrar_btn.click()
        logger.info("Sidebar cerrado correctamente.")
        time.sleep(1)
    except Exception:
        logger.warning("No se pudo cerrar sidebar (probablemente ya estaba cerrado).")

def hacer_logout(driver):
    try:
        logout_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((
                By.XPATH, "//a[contains(@href,'/logout') and span[contains(text(),'Logout')]]"
            ))
        )
        logout_link.click()
        logger.info("Logout realizado correctamente mediante link.")
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "form.form-signin"))
        )
        logger.info("Form de login visible y listo tras logout.")
        time.sleep(2)
    except Exception as e:
        config.guardar_evidencia(driver.get_screenshot_as_png(), "vegasx_logout_fail")
        logger.warning(f"No se pudo hacer logout; evidencia guardada. Error: {e}")

def login(driver, usuario, password):
    form = WebDriverWait(driver, 20).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "form.form-signin"))
    )
    user_input = form.find_element(By.CSS_SELECTOR, ".form-control.username")
    pwd_input = form.find_element(By.CSS_SELECTOR, ".form-control.password")
    user_input.clear()
    user_input.send_keys(usuario)
    pwd_input.clear()
    pwd_input.send_keys(password)
    btn = form.find_element(By.CSS_SELECTOR, "button.loginbutton")
    btn.click()
    time.sleep(0.7)
    if driver.find_elements(By.CSS_SELECTOR, "form.form-signin"):
        raise Exception("El form de login reapareció tras sign in; posible sesión previa activa/race. Reintentar inmediatamente.")

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
                    cerrar_modal_si_aparece(driver)
                    WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, ".content-panel-toggler"))
                    )
                    logger.info(f"Login exitoso para usuario {cuenta['usuario']}")
                    break
                except Exception as e:
                    logger.warning(f"Intento {intento + 1} fallido para usuario {cuenta['usuario']}: {e}")
                    time.sleep(2)
            else:
                logger.warning(f"No se pudo iniciar sesión después de {MAX_LOGIN_RETRIES} intentos para {cuenta['usuario']}")
                continue
            abrir_sidebar(driver)
            credits = extraer_credits_sidebar(driver)
            hora_login = config.get_current_timestamp()
            if credits is not None:
                config.enviar_resultado_balance(sheet, WEBSITE_NAME, cuenta["usuario"], hora_login, credits)
            cerrar_sidebar(driver)
            hacer_logout(driver)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
