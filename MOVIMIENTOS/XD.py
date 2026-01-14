import csv
import requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS


def obtener_token_compania(nombre_compania):
    """Obtiene token de autenticación para una compañía específica"""
    login_url = "https://api.backend.biz/api/authentication/login/backend"
    login_data = {"username": SUPERADMIN_USER, "password": SUPERADMIN_PASS}
    resp = requests.post(login_url, json=login_data)
    super_token = resp.json()["data"]["token"]

    company_id = companies[nombre_compania]
    change_url = "https://api.backend.biz/api/authentication/change-company/master"
    headers = {"Authorization": f"Bearer {super_token}"}
    payload = {"companyId": company_id}
    cambio = requests.post(change_url, json=payload, headers=headers)
    data = cambio.json()
    token = data.get("token") or data.get("data", {}).get("token")
    if not token:
        raise ValueError(f"No se pudo obtener token para {nombre_compania}: {data}")
    return token, company_id


def extraer_movimientos_noviembre(nombre_compania, token, company_id):
    """Extrae todos los movimientos de noviembre 2025 para una compañía"""
    headers = {"Authorization": f"Bearer {token}"}
    movements_url = "https://api.backend.biz/api/movements/paginated"
    page_size = 500

    # Rango de fechas para todo noviembre 2025
    date_filter = "2025-11-01,2025-11-30"

    params = {
        "filters": f'''[{{"type":"date","value":"{date_filter}"}},{{"type":"companyId","value":"{company_id}"}}]''',
        "page": 1,
        "pageSize": page_size,
        "timeZone": "America/Lima",
    }

    # Primera petición para obtener el total
    resp = requests.get(movements_url, params=params, headers=headers)
    json_data = resp.json()
    total_docs = json_data.get("data", {}).get("numberTotalDocuments", 0)
    total_pages = (total_docs // page_size) + (1 if total_docs % page_size else 0)
    print(f"  → [{nombre_compania}] Total: {total_docs} movimientos en {total_pages} páginas")

    # Extraer todas las páginas
    all_documents = []
    for page in range(1, total_pages + 1):
        params["page"] = page
        resp = requests.get(movements_url, params=params, headers=headers)
        documents = resp.json().get("data", {}).get("documents", [])
        
        # Agregar nombre de compañía a cada documento
        for doc in documents:
            doc["compania"] = nombre_compania
        
        all_documents.extend(documents)

    return all_documents


def procesar_compania(nombre_compania):
    """Procesa una compañía: obtiene token y extrae movimientos de noviembre"""
    try:
        token, company_id = obtener_token_compania(nombre_compania)
        movimientos = extraer_movimientos_noviembre(nombre_compania, token, company_id)
        print(f"  ✓ [{nombre_compania}] Completado: {len(movimientos)} movimientos")
        return movimientos
    except Exception as e:
        print(f"  ✗ [{nombre_compania}] Error: {e}")
        return []


def guardar_a_csv(todos_movimientos, filepath):
    """Guarda todos los movimientos en un archivo CSV"""
    if not todos_movimientos:
        print("⚠ No hay movimientos para guardar")
        return

    # Obtener todos los campos únicos
    fieldnames = set()
    for mov in todos_movimientos:
        fieldnames.update(mov.keys())
    fieldnames = sorted(list(fieldnames))
    
    # Escribir CSV
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(todos_movimientos)
    
    print(f"\n✅ Archivo guardado: {filepath}")
    print(f"   📊 Total registros: {len(todos_movimientos)}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("EXTRACCIÓN DE MOVIMIENTOS - NOVIEMBRE 2025")
    print("="*80 + "\n")
    
    # Lista de todas las compañías
    todas_companias = sorted(companies.keys())
    print(f"📋 Total compañías a procesar: {len(todas_companias)}\n")
    
    # Extraer movimientos en paralelo
    todos_movimientos = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(procesar_compania, nombre): nombre for nombre in todas_companias}
        
        for future in as_completed(futures):
            movimientos = future.result()
            todos_movimientos.extend(movimientos)
    
    # Guardar en el mismo directorio del script
    script_dir = Path(__file__).parent
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"movimientos_noviembre_2025_{timestamp}.csv"
    filepath = script_dir / filename
    
    guardar_a_csv(todos_movimientos, filepath)
    
    print("\n✅ PROCESO COMPLETADO\n")
