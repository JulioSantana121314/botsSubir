# platform_grupo2.py
import time
import re

from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

import config


# ----------------------------
# consola + logger
# ----------------------------
def _ts():
    return time.strftime("%H:%M:%S")


def _p(msg):
    print(f"{_ts()} {msg}", flush=True)


def get_logger(website_name):
    return config.get_logger(f"{website_name}_bot")


def _screenshot(driver, logger, prefix):
    try:
        path = config.guardar_evidencia(driver.get_screenshot_as_png(), prefix)
        _p(f"[SCREENSHOT] {path}")
        logger.info(f"[SCREENSHOT] {path}")
        return path
    except Exception as e:
        _p(f"[SCREENSHOT] no se pudo guardar: {e}")
        logger.warning(f"[SCREENSHOT] no se pudo guardar: {e}")
        return None


# ----------------------------
# JS helpers
# ----------------------------
def _js(driver, script, *args):
    return driver.execute_script(script, *args)


def _js_click(driver, el):
    _js(driver, "arguments[0].scrollIntoView({block:'center'});", el)
    time.sleep(0.1)
    _js(driver, "arguments[0].click();", el)


def _native_event_click(driver, el):
    _js(
        driver,
        """
        const el = arguments[0];
        const r = el.getBoundingClientRect();
        const opts = {bubbles:true, cancelable:true, view:window, clientX:r.left+r.width/2, clientY:r.top+r.height/2};
        el.dispatchEvent(new PointerEvent('pointerdown', opts));
        el.dispatchEvent(new MouseEvent('mousedown', opts));
        el.dispatchEvent(new PointerEvent('pointerup', opts));
        el.dispatchEvent(new MouseEvent('mouseup', opts));
        el.dispatchEvent(new MouseEvent('click', opts));
        """,
        el,
    )


def _visible_count(driver, css_selector):
    els = driver.find_elements(By.CSS_SELECTOR, css_selector)
    return sum(1 for e in els if e.is_displayed())


def _log_modal_state(driver, logger, label):
    try:
        dialogs = driver.find_elements(By.CSS_SELECTOR, "div.el-dialog[role='dialog']")
        visible_dialogs = [d for d in dialogs if d.is_displayed()]
        overlays = driver.find_elements(By.CSS_SELECTOR, "div.v-modal")
        visible_overlays = [o for o in overlays if o.is_displayed()]

        msg = (
            f"[MODAL-STATE] {label} | dialogs={len(dialogs)} visible_dialogs={len(visible_dialogs)} "
            f"overlays={len(overlays)} visible_overlays={len(visible_overlays)}"
        )
        _p(msg)
        logger.info(msg)
    except Exception as e:
        _p(f"[MODAL-STATE] snapshot error: {e}")
        logger.warning(f"[MODAL-STATE] snapshot error: {e}")


# ----------------------------
# Hint visible (robusto)
# ----------------------------
def _get_visible_hint_dialog(driver):
    candidates = []
    candidates += driver.find_elements(By.CSS_SELECTOR, "div.el-dialog[role='dialog'][aria-label='Hint']")
    candidates += driver.find_elements(
        By.XPATH,
        "//div[contains(@class,'el-dialog') and @role='dialog']"
        "[.//span[contains(@class,'el-dialog__title') and normalize-space(.)='Hint']]",
    )
    candidates += driver.find_elements(
        By.XPATH,
        "//div[contains(@class,'el-dialog') and @role='dialog']"
        "[.//div[contains(@class,'m-remote-login-alert-content')]]",
    )

    visibles = []
    for m in candidates:
        try:
            if m.is_displayed():
                visibles.append(m)
        except Exception:
            pass

    return visibles[0] if visibles else None


# ----------------------------
# Cierres de modals
# ----------------------------
def cerrar_message_box_notification(driver, logger):
    """
    Modal:
    <div class="el-message-box"> ... <span>Notification</span> ... <span>OK</span>
    """
    try:
        box = WebDriverWait(driver, 0.6).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div.el-message-box"))
        )

        # validar por título Notification (para no chocar con logout confirm u otros)
        title = ""
        try:
            title_el = box.find_element(By.CSS_SELECTOR, "div.el-message-box__title span")
            title = (title_el.text or "").strip()
        except Exception:
            title = ""

        if title.lower() != "notification":
            return False

        ok_btn = box.find_element(By.XPATH, ".//div[contains(@class,'el-message-box__btns')]//button[.//span[normalize-space(.)='OK']]")
        try:
            ok_btn.click()
        except Exception:
            _js_click(driver, ok_btn)

        _p("[NOTIF] ✅ cerrado (OK)")
        logger.info("[NOTIF] ✅ cerrado (OK)")
        return True
    except TimeoutException:
        return False
    except Exception as e:
        logger.warning(f"[NOTIF] error: {e}")
        return False


def cerrar_modal_anuncio(driver, logger):
    _p("[ANUNCIO] buscando...")
    logger.info("[ANUNCIO] buscando...")

    try:
        WebDriverWait(driver, 0.8).until(
            EC.visibility_of_element_located((By.XPATH, "//div[contains(@class,'el-dialog')]//span[contains(text(),'announcement')]"))
        )
        btn = WebDriverWait(driver, 0.8).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class,'el-dialog__footer')]//span[normalize-space(.)='confirm']/parent::button")
            )
        )
        try:
            btn.click()
        except Exception:
            _js_click(driver, btn)

        _p("[ANUNCIO] ✅ cerrado")
        logger.info("[ANUNCIO] ✅ cerrado")
        return True
    except TimeoutException:
        return False
    except Exception as e:
        logger.warning(f"[ANUNCIO] error: {e}")
        return False


def cerrar_hint_password(driver, logger):
    """
    Hint password: botón "Do not remind again this month"
    """
    try:
        modal = _get_visible_hint_dialog(driver)
        if not modal:
            return False

        text = (modal.text or "").lower()
        if ("not been changed" not in text) and ("change your password" not in text) and ("password" not in text):
            return False

        btn = modal.find_element(By.XPATH, ".//button[.//span[normalize-space()='Do not remind again this month']]")

        try:
            ActionChains(driver).move_to_element(btn).pause(0.05).click(btn).perform()
        except Exception:
            try:
                _js_click(driver, btn)
            except Exception:
                _native_event_click(driver, btn)

        _p("[HINT-PASS] ✅ cerrado (intentado)")
        logger.info("[HINT-PASS] ✅ cerrado (intentado)")
        return True
    except Exception:
        return False


def cerrar_hint_login_diferente(driver, logger):
    """
    Hint different location: botón "confirm"
    """
    try:
        modal = _get_visible_hint_dialog(driver)
        if not modal:
            return False

        text = (modal.text or "").lower()
        if ("different location" not in text) and ("logged in" not in text):
            return False

        btn = modal.find_element(By.XPATH, ".//button[.//span[normalize-space()='confirm']]")
        try:
            btn.click()
        except Exception:
            _js_click(driver, btn)

        _p("[HINT-DIFF] ✅ confirm presionado")
        logger.info("[HINT-DIFF] ✅ confirm presionado")
        return True
    except Exception:
        return False


def cerrar_modales_genericos(driver, logger):
    closed_any = False

    # confirm genérico (footer)
    try:
        btn = WebDriverWait(driver, 0.5).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[contains(@class,'el-dialog__footer')]//span[normalize-space(.)='confirm']/parent::button")
            )
        )
        try:
            btn.click()
        except Exception:
            _js_click(driver, btn)

        _p("[GENERIC] cerró confirm")
        logger.info("[GENERIC] cerró confirm")
        closed_any = True
    except TimeoutException:
        pass
    except Exception:
        pass

    # OK genérico (diálogos tipo message-box que no sean Notification)
    try:
        btn = WebDriverWait(driver, 0.5).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'el-message-box__btns')]//button[.//span[normalize-space(.)='OK']]"))
        )
        try:
            btn.click()
        except Exception:
            _js_click(driver, btn)

        _p("[GENERIC] cerró OK (message-box)")
        logger.info("[GENERIC] cerró OK (message-box)")
        closed_any = True
    except TimeoutException:
        pass
    except Exception:
        pass

    return closed_any


def fast_close_all_modals(driver, logger, cycles=5):
    """
    Barrido rápido: intenta cerrar TODOS los modals conocidos por ciclo.
    """
    _p(f"[FAST-CLOSE] start cycles={cycles}")
    logger.info(f"[FAST-CLOSE] start cycles={cycles}")

    for c in range(1, cycles + 1):
        _p(f"[FAST-CLOSE] cycle {c}/{cycles}")
        logger.info(f"[FAST-CLOSE] cycle {c}/{cycles}")

        # Nuevo: Notification primero (suele bloquear)
        cerrar_message_box_notification(driver, logger)

        # Hint(s)
        cerrar_hint_password(driver, logger)
        cerrar_hint_login_diferente(driver, logger)

        # anuncio + genéricos
        cerrar_modal_anuncio(driver, logger)
        cerrar_modales_genericos(driver, logger)

        visible_dialogs = _visible_count(driver, "div.el-dialog[role='dialog']")
        visible_overlays = _visible_count(driver, "div.v-modal")
        visible_msgbox = _visible_count(driver, "div.el-message-box")

        _p(f"[FAST-CLOSE] visible_dialogs={visible_dialogs} visible_overlays={visible_overlays} visible_msgbox={visible_msgbox}")
        logger.info(f"[FAST-CLOSE] visible_dialogs={visible_dialogs} visible_overlays={visible_overlays} visible_msgbox={visible_msgbox}")

        if visible_dialogs == 0 and visible_overlays == 0 and visible_msgbox == 0:
            _p("[FAST-CLOSE] CLEAN -> stop")
            logger.info("[FAST-CLOSE] CLEAN -> stop")
            return True

        time.sleep(0.25)

    _p("[FAST-CLOSE] end cycles (pueden quedar overlays)")
    logger.warning("[FAST-CLOSE] end cycles (pueden quedar overlays)")
    return False


# ----------------------------
# Login OK detection + extracción
# ----------------------------
def confirmar_login_exitoso(driver, logger, timeout=10):
    _p("[LOGIN-OK] esperando dashboard...")
    logger.info("[LOGIN-OK] esperando dashboard...")

    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.score-container")))
        _p("[LOGIN-OK] ✅ score-container detectado")
        logger.info("[LOGIN-OK] ✅ score-container detectado")
        return True
    except TimeoutException:
        try:
            WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.account-container")))
            _p("[LOGIN-OK] ✅ account-container detectado")
            logger.info("[LOGIN-OK] ✅ account-container detectado")
            return True
        except TimeoutException:
            _p("[LOGIN-OK] ❌ no se confirmó login")
            logger.warning("[LOGIN-OK] ❌ no se confirmó login")
            return False


def login(driver, usuario, password, logger):
    _p(f"[LOGIN] usuario={usuario}")
    logger.info(f"[LOGIN] usuario={usuario}")

    wait = WebDriverWait(driver, 10)

    user_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.el-input__inner[name='userName']")))
    user_input.clear()
    user_input.send_keys(usuario)

    pass_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input.el-input__inner[name='passWd']")))
    pass_input.clear()
    pass_input.send_keys(password)

    # ✅ NUEVO: esperar que el botón de login sea clickeable antes de presionar
    login_btn = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.el-button--primary")))
    try:
        login_btn.click()
    except Exception:
        _js_click(driver, login_btn)

    _p("[LOGIN] click login")
    logger.info("[LOGIN] click login")
    return True


def extraer_balance_y_usuario(driver, logger):
    _p("[EXTRACT] iniciando...")
    logger.info("[EXTRACT] iniciando...")

    balance_elem = driver.find_element(
        By.XPATH,
        "//div[contains(@class,'score-container')]//span[not(ancestor::i[contains(@class,'el-icon-loading')])]",
    )
    texto_balance = balance_elem.text
    match = re.search(r"[0-9,\.]+", texto_balance)
    balance = float(match.group().replace(",", "")) if match else None

    usuario_elem = driver.find_element(By.XPATH, "//div[contains(@class,'account-container')]//p")
    username = usuario_elem.text.strip()

    _p(f"[EXTRACT] balance={balance} username='{username}' raw='{texto_balance}'")
    logger.info(f"[EXTRACT] balance={balance} username='{username}' raw='{texto_balance}'")
    return balance, username


# ----------------------------
# Logout (sin re-check de modals)
# ----------------------------
def abrir_sidebar(driver, logger):
    try:
        driver.find_element(By.CLASS_NAME, "hamburger").click()
        _p("[SIDEBAR] abierto")
        logger.info("[SIDEBAR] abierto")
        time.sleep(0.4)
    except Exception as e:
        logger.warning(f"[SIDEBAR] error: {e}")


def logout(driver, logger):
    _p("[LOGOUT] iniciando")
    logger.info("[LOGOUT] iniciando")

    try:
        time.sleep(0.8)
        logout_btn = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.XPATH, "//span[normalize-space(text())='Logout']/parent::button"))
        )
        logout_btn.click()
        _p("[LOGOUT] click Logout")
        logger.info("[LOGOUT] click Logout")

        ok_btn = WebDriverWait(driver, 6).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'el-message-box__btns')]//button[.//span[normalize-space(.)='OK']]"))
        )
        try:
            ok_btn.click()
        except Exception:
            _js_click(driver, ok_btn)

        _p("[LOGOUT] OK confirmado")
        logger.info("[LOGOUT] OK confirmado")
    except Exception as e:
        _p(f"[LOGOUT] error: {e}")
        logger.error(f"[LOGOUT] error: {e}")
        config.log_exception(logger, "Error en logout")
        _screenshot(driver, logger, "logout_error")


# ----------------------------
# Flujo principal por cuenta
# ----------------------------
def login_and_check(driver, website_name, usuario, password, url_login, max_retries, logger):
    for intento in range(1, max_retries + 1):
        _p(f"[FLOW] intento {intento}/{max_retries}")
        logger.info(f"[FLOW] intento {intento}/{max_retries}")

        try:
            _p(f"[FLOW] GET {url_login}")
            driver.get(url_login)
            time.sleep(1.2)

            login(driver, usuario, password, logger)

            # Confirmar login exitoso lo antes posible
            if not confirmar_login_exitoso(driver, logger, timeout=10):
                _screenshot(driver, logger, f"login_not_confirmed_{intento}")
                continue

            # Hora del login exitoso (lo primero)
            hora_login = config.get_current_timestamp()
            _p(f"[FLOW] ✅ LOGIN OK -> hora_login={hora_login}")
            logger.info(f"[FLOW] ✅ LOGIN OK -> hora_login={hora_login}")

            # Barrido rápido de modals (incluye Notification)
            fast_close_all_modals(driver, logger, cycles=5)

            # Extraer balance/usuario
            time.sleep(0.6)
            balance, username = extraer_balance_y_usuario(driver, logger)
            if balance is not None and username:
                return balance, username, hora_login

            _screenshot(driver, logger, f"extract_failed_{intento}")
            time.sleep(1.2)

        except Exception as e:
            _p(f"[FLOW] error: {e}")
            logger.error(f"[FLOW] error: {e}")
            config.log_exception(logger, f"Error en login_and_check intento {intento}")
            _screenshot(driver, logger, f"fatal_{intento}")
            time.sleep(1.2)

    return None, None, None


def run(website_name, max_login_retries=3):
    logger = get_logger(website_name)
    _p(f"=== RUN {website_name} ===")
    logger.info(f"=== RUN {website_name} ===")

    driver = None
    try:
        driver = config.get_chrome_driver()
        sheet = config.google_sheets_connect()

        url_login = config.WEBSITES[website_name]["url"]
        cuentas = config.WEBSITES[website_name]["accounts"]

        for idx, cuenta in enumerate(cuentas, 1):
            usuario = cuenta["usuario"]
            password = cuenta["password"]

            _p(f"--- CUENTA {idx}/{len(cuentas)} {usuario} ---")
            logger.info(f"[CUENTA] {idx}/{len(cuentas)} usuario={usuario}")

            balance, username, hora_login = login_and_check(
                driver, website_name, usuario, password, url_login, max_login_retries, logger
            )

            if balance is not None and username:
                config.enviar_resultado_balance(sheet, website_name, username, hora_login, balance)
                _p("[RESULT] registrado")
                logger.info("[RESULT] registrado")
            else:
                _p("[RESULT] sin resultado")
                logger.warning("[RESULT] sin resultado")

            abrir_sidebar(driver, logger)
            logout(driver, logger)
            time.sleep(1.5)

    finally:
        if driver:
            driver.quit()
            _p("[CLEANUP] driver cerrado")
            logger.info("[CLEANUP] driver cerrado")


if __name__ == "__main__":
    print("Este archivo contiene lógica centralizada (platform_grupo2).")
    print("Ejecuta los scripts individuales (ej: vblinkBalance.py)")
