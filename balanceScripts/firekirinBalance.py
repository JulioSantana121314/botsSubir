"""
Fire Kirin Balance Bot - Script simplificado usando platform_grupo1
"""
import platform_grupo1

# Configuración específica del website
WEBSITE_NAME = "FIRE KIRIN"
MAX_LOGIN_RETRIES = 4

if __name__ == "__main__":
    platform_grupo1.run(WEBSITE_NAME, MAX_LOGIN_RETRIES)
