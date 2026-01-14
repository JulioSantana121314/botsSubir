import requests
from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS

def obtener_token_compania(nombre_compania):
    login_url = "https://api.backend.biz/api/authentication/login/backend"
    login_data = {"username": SUPERADMIN_USER, "password": SUPERADMIN_PASS}
    resp = requests.post(login_url, json=login_data)
    super_token = resp.json()["data"]["token"]

    company_id = companies[nombre_compania]
    change_url = "https://api.backend.biz/api/authentication/change-company/master"
    headers = {"Authorization": f"Bearer {super_token}"}
    payload = {"companyId": company_id}
    cambio = requests.post(change_url, json=payload, headers=headers)
    # Fíjate si el token está directo o en data/token
    data = cambio.json()
    token = data.get("token") or data.get("data", {}).get("token")
    return token

# Ejemplo: seleccionar la compañía deseada
nombre_elegido = "Wise Gang"
token = obtener_token_compania(nombre_elegido)
print(f"Token para {nombre_elegido}: {token}")

# Ahora puedes consultar movimientos usando ese token y company_id
headers = {"Authorization": f"Bearer {token}"}
movements_url = "https://api.backend.biz/api/movements/paginated"
params = {
    "filters": f'[{{"type":"companyId","value":"{companies[nombre_elegido]}"}}]',
    "page": 1,
    "pageSize": 50,
    "timeZone": "America/Lima",
}
resp = requests.get(movements_url, params=params, headers=headers)
print("Movimientos:", resp.json())
