"""
Panda Master Balance Bot - Script simplificado usando platform_grupo1
"""
import platform_grupo1

# Configuración específica del website
WEBSITE_NAME = "PANDA MASTER"
MAX_LOGIN_RETRIES = 4

if __name__ == "__main__":
    platform_grupo1.run(WEBSITE_NAME, MAX_LOGIN_RETRIES)
