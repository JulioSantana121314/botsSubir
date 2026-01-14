# yoloBalance.py — versión 1.2 (centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import config


WEBSITE_NAME = "YOLO"
MAX_LOGIN_RETRIES = 4

logger = config.get_logger(f"{WEBSITE_NAME}_bot")


def extraer_balance_yolo(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.pc span.user-name"))
        )
        user_name_spans = driver.find_elements(By.CSS_SELECTOR, "div.pc span.user-name")
        for s in user_name_spans:
            text = s.text
            match = re.search(r"My Score.*?([\d,\.]+)", text)
            if match:
                balance = float(match.group(1).replace(",", ""))
                logger.info(f"Balance extraído: {balance}")
                print(f"Balance: {balance}")
                return balance

        score_spans = driver.find_elements(By.CSS_SELECTOR, "span.score")
        for s in score_spans:
            text = s.text.strip()
            if re.match(r"^[\d,\.]+$", text):
                balance = float(text.replace(",", ""))
                logger.info(f"Balance extraído (score): {balance}")
                print(f"Balance: {balance}")
                return balance
    except Exception as e:
        logger.error(f"Error extrayendo balance: {e}")
    return None


def logout_yolo(driver):
    try:
        logout_btn = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[contains(@href,'/admin/auth/logout') and contains(.,'Logout')]")
            )
        )
        time.sleep(1.2)
        logout_btn.click()
        logger.info("Logout realizado correctamente.")
    except Exception as e:
        logger.warning(f"Error realizando logout: {e}")


def login_and_check(driver, usuario, password):
    for intento in range(MAX_LOGIN_RETRIES):
        try:
            driver.get(config.WEBSITES[WEBSITE_NAME]["url"])
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form#login-form"))
            )
            usuario_input = driver.find_element(By.NAME, "username")
            pass_input = driver.find_element(By.NAME, "password")
            usuario_input.clear()
            usuario_input.send_keys(usuario)
            pass_input.clear()
            pass_input.send_keys(password)
            login_btn = driver.find_element(By.ID, "submit")
            login_btn.click()

            for _ in range(16):
                if driver.find_elements(By.CSS_SELECTOR, "div.navbar-wrapper span.user-name"):
                    time.sleep(0.7)
                    return True
                time.sleep(0.5)

            logger.info(f"Intento {intento + 1} fallido para usuario {usuario}, reintentando...")
        except Exception as e:
            logger.warning(f"Error en ciclo de login: {e}")
            time.sleep(1)

    logger.error(f"No se pudo iniciar sesión después de {MAX_LOGIN_RETRIES} intentos para {usuario}")
    return False


def main():
    sheet = config.google_sheets_connect()
    site = config.WEBSITES[WEBSITE_NAME]
    driver = config.get_chrome_driver()
    try:
        for cuenta in site["accounts"]:
            logged = login_and_check(driver, cuenta["usuario"], cuenta["password"])
            if not logged:
                continue

            balance = extraer_balance_yolo(driver)
            hora_login = config.get_current_timestamp()
            if balance is not None:
                config.enviar_resultado_balance(
                    sheet, WEBSITE_NAME, cuenta["usuario"], hora_login, balance
                )
            logout_yolo(driver)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
