# superdragonBalance.py — versión 1.1 (lógica centralizada via config.py)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from datetime import datetime
import config

WEBSITE_NAME = "SUPER DRAGON"
MAX_LOGIN_RETRIES = 4
MAX_CAPTCHA_RETRIES = 4

logger = config.get_logger(f"{WEBSITE_NAME}_bot")

def resolver_captcha_superdragon(driver, max_retries=MAX_CAPTCHA_RETRIES):
    for intento in range(max_retries):
        try:
            captcha_img = driver.find_element(By.CSS_SELECTOR, "form.login-form img")
            try:
                captcha_img.click()
                time.sleep(0.4)
            except Exception:
                pass
            captcha_bytes = captcha_img.screenshot_as_png
            solucion = config.resolver_captcha_2captcha(captcha_bytes, "superdragon")
            input_captcha = driver.find_elements(By.XPATH, "//input[@class='el-input__inner' and @autocomplete='off']")
            if input_captcha:
                input_captcha = input_captcha[-1]
                WebDriverWait(driver, 4).until(lambda dr: input_captcha.is_enabled() and not input_captcha.get_attribute('readonly'))
                input_captcha.clear()
                input_captcha.send_keys(solucion)
                return True
        except Exception as e:
            logger.warning(f"Error resolviendo captcha: {e}")
        time.sleep(1.2)
    raise Exception("Error resolviendo captcha Super Dragon después de múltiples intentos")

def extraer_balance_modern(driver):
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//section[contains(@class, 'app-main')]"))
        )
        header_cells = driver.find_elements(By.XPATH, "//table[contains(@class,'el-table__header')]//div[@class='cell']")
        balance_index = None
        for idx, h in enumerate(header_cells):
            if h.text.strip().lower() == "balance":
                balance_index = idx + 1
                break
        if balance_index is not None:
            value_cell = driver.find_element(
                By.XPATH, f"(//table[contains(@class,'el-table__body')]/tbody/tr/td[{balance_index}]/div[@class='cell'])[1]"
            )
            texto = value_cell.text.strip()
            match = re.search(r"[\d,\.]+", texto)
            if match:
                balance = float(match.group().replace(",", ""))
                logger.info(f"Balance extraído: {balance}")
                print(f"Balance: {balance}")
                return balance
    except Exception as e:
        logger.error(f"Error extrayendo balance: {e}")
    return None

def logout_modern(driver):
    try:
        avatar_btn = driver.find_element(By.CSS_SELECTOR, ".avatar-wrapper.el-dropdown-selfdefine")
        avatar_btn.click()
        time.sleep(1.2)
        logout_btn = WebDriverWait(driver, 7).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//li[contains(@class,'el-dropdown-menu__item--divided')]//span[contains(translate(., 'LO', 'lo'), 'log out')]")
            )
        )
        logout_btn.click()
        logger.info("Logout realizado correctamente.")
    except Exception as e:
        logger.warning(f"Error realizando logout: {e}")

def login_and_check(driver, usuario, password):
    for intento in range(MAX_LOGIN_RETRIES):
        try:
            driver.get(config.WEBSITES[WEBSITE_NAME]["url"])
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "form.login-form")))
            usuario_input = driver.find_element(By.CSS_SELECTOR, "input[name='username']")
            pass_input = driver.find_element(By.CSS_SELECTOR, "input[name='password']")
            usuario_input.clear()
            usuario_input.send_keys(usuario)
            pass_input.clear()
            pass_input.send_keys(password)
            resolver_captcha_superdragon(driver)
            login_btn = driver.find_element(By.XPATH, "//button/span[contains(.,'Log in')]/parent::button")
            login_btn.click()
            for _ in range(16):
                if "login" not in driver.current_url.lower():
                    time.sleep(0.7)
                    return True
                time.sleep(0.5)
            logger.info(f"Intento {intento + 1} fallido para usuario {usuario}, reintentando...")
        except Exception as e:
            logger.warning(f"Error en ciclo de login/captcha: {e}")
            time.sleep(1)
    logger.error(f"No se pudo iniciar sesión después de {MAX_LOGIN_RETRIES} intentos para {usuario}")
    return False

def main():
    sheet = config.google_sheets_connect()
    site = config.WEBSITES[WEBSITE_NAME]
    driver = None
    try:
        driver = config.get_chrome_driver()
        for cuenta in site["accounts"]:
            logged = login_and_check(driver, cuenta["usuario"], cuenta["password"])
            if not logged:
                continue
            balance = extraer_balance_modern(driver)
            hora_login = config.get_current_timestamp()
            if balance is not None:
                config.enviar_resultado_balance(sheet, WEBSITE_NAME, cuenta["usuario"], hora_login, balance)
            logout_modern(driver)
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
