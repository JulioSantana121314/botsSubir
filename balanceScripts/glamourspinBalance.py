# glamourspinBalance.py — versión 1.2 (centralizada via config.py, con popup handler)
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import config


WEBSITE_NAME = "GLAMOUR SPIN"
logger = config.get_logger(f"{WEBSITE_NAME}_bot")


def cerrar_popup_announcement(driver):
    """Cierra el popup de 'announcement' si aparece; si no, continúa sin error."""
    try:
        # Espera breve a que aparezca el diálogo de announcement
        WebDriverWait(driver, 3).until(
            EC.visibility_of_element_located(
                (By.XPATH, "//div[contains(@class,'el-dialog') and @aria-label='announcement']")
            )
        )
        # Botón X (ícono de cerrar en el header)
        close_icon = WebDriverWait(driver, 2).until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.el-dialog__headerbtn i.el-dialog__close")
            )
        )
        try:
            close_icon.click()
        except Exception:
            driver.execute_script("arguments[0].click();", close_icon)
        logger.info("Popup de 'announcement' cerrado con la X.")
        time.sleep(0.5)
    except TimeoutException:
        # No apareció el popup; continuar flujo normal
        pass
    except Exception as e:
        logger.warning(f"No se pudo cerrar el popup de 'announcement': {e}")


def login_vblink(driver, usuario, password):
    wait = WebDriverWait(driver, 30)
    usuario_input = wait.until(EC.presence_of_element_located(
        (By.CSS_SELECTOR, "input.el-input__inner[name='userName']")))
    usuario_input.clear()
    usuario_input.send_keys(usuario)
    password_input = driver.find_element(By.CSS_SELECTOR, "input.el-input__inner[name='passWd']")
    password_input.clear()
    password_input.send_keys(password)
    driver.find_element(By.CSS_SELECTOR, "button.el-button--primary").click()


def cerrar_todos_modales(driver):
    for _ in range(3):
        cerro_algo = False
        try:
            wait = WebDriverWait(driver, 2)
            confirm_btn = wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class,'el-dialog__footer')]//span[.='confirm']/parent::button")))
            try:
                confirm_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", confirm_btn)
            logger.info("Modal de confirmación detectado y cerrado.")
            time.sleep(1)
            cerro_algo = True
        except TimeoutException:
            pass
        try:
            wait = WebDriverWait(driver, 2)
            confirm_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//button[contains(@class,'el-button--primary') and span[normalize-space(text())='confirm']]")))
            try:
                confirm_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", confirm_btn)
            logger.info("Modal de conflicto de login detectado y cerrado.")
            time.sleep(1)
            cerro_algo = True
        except TimeoutException:
            pass
        try:
            wait = WebDriverWait(driver, 2)
            ok_btn = wait.until(EC.presence_of_element_located(
                (By.XPATH, "//button[contains(@class,'el-button--primary') and span[normalize-space(text())='OK']]")))
            try:
                ok_btn.click()
            except Exception:
                driver.execute_script("arguments[0].click();", ok_btn)
            logger.info("Modal Hint OK detectado y cerrado.")
            time.sleep(1)
            cerro_algo = True
        except TimeoutException:
            pass
        if not cerro_algo:
            break


def extraer_balance_y_usuario(driver):
    try:
        balance_elem = driver.find_element(
            By.XPATH, "//div[contains(@class,'score-container')]//span[not(ancestor::i[contains(@class,'el-icon-loading')])]"
        )
        texto_balance = balance_elem.text
        match = re.search(r"[0-9,\.]+", texto_balance)
        balance = float(match.group().replace(',', '')) if match else None
        usuario_elem = driver.find_element(
            By.XPATH, "//div[contains(@class,'account-container')]//p"
        )
        username = usuario_elem.text.strip()
        if balance is not None and username:
            logger.info(f"Balance extraído: {balance}, Usuario: {username}")
            print(f"Balance: {balance}, Usuario: {username}")
            return balance, username
        else:
            logger.warning("No se encontró balance o usuario correctamente")
            return None, None
    except Exception as e:
        logger.error(f"Error extrayendo balance o usuario: {e}")
        return None, None


def abrir_sidebar(driver):
    try:
        hamburger_btn = driver.find_element(By.CLASS_NAME, "hamburger")
        hamburger_btn.click()
        logger.info("Menú lateral (sidebar) abierto.")
        time.sleep(1)
    except Exception as e:
        logger.warning(f"No se pudo abrir sidebar o ya estaba abierto: {e}")


def confirmar_logout(driver):
    try:
        wait = WebDriverWait(driver, 7)
        ok_btn = wait.until(EC.presence_of_element_located(
            (By.XPATH, "//div[contains(@class, 'el-message-box__btns')]/button[span[normalize-space(text())='OK']]")
        ))
        try:
            ok_btn.click()
        except Exception:
            driver.execute_script("arguments[0].click();", ok_btn)
        logger.info("Confirmación de logout aceptada.")
        time.sleep(1)
    except TimeoutException:
        logger.info("No apareció modal de confirmación de logout.")


def logout(driver):
    try:
        logout_btn = driver.find_element(By.XPATH, "//span[text()='Logout']/parent::button")
        logout_btn.click()
        logger.info("Botón Logout presionado, esperando confirmación...")
        cerrar_todos_modales(driver)
        confirmar_logout(driver)
        cerrar_todos_modales(driver)
        time.sleep(3)
    except Exception as e:
        logger.error(f"Error realizando logout: {e}")


def main():
    logger.info(f"Iniciando navegador Chrome para {WEBSITE_NAME}")
    driver = config.get_chrome_driver()
    sheet = config.google_sheets_connect()
    url_login = config.WEBSITES[WEBSITE_NAME]["url"]
    cuentas = config.WEBSITES[WEBSITE_NAME]["accounts"]
    try:
        for cuenta in cuentas:
            logger.info(f"Procesando cuenta {cuenta['usuario']}...")
            driver.get(url_login)
            time.sleep(2)
            cerrar_popup_announcement(driver)  # <-- NUEVO: Cerrar popup de announcement
            login_vblink(driver, cuenta['usuario'], cuenta['password'])
            cerrar_todos_modales(driver)
            logger.info("Formulario enviado correctamente y todos los modales gestionados.")
            time.sleep(2)
            cerrar_popup_announcement(driver)  # <-- NUEVO: Por si reaparece tras login
            cerrar_todos_modales(driver)
            hora_login = config.get_current_timestamp()
            balance, username = extraer_balance_y_usuario(driver)
            if balance is not None and username is not None:
                config.enviar_resultado_balance(sheet, WEBSITE_NAME, username, hora_login, balance)
            abrir_sidebar(driver)
            logout(driver)
        logger.info("Proceso completo.")
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
