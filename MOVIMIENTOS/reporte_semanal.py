import requests
from datetime import datetime
from collections import defaultdict
import gspread
from google.oauth2.service_account import Credentials
from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS


# ============================================================
# CONFIGURACIÓN
# ============================================================

# Compañías a evaluar (nombres exactos como están en el diccionario companies)
COMPANIAS_ELEGIDAS = [
    "Token Tiger",
    "Innercore Games",
    "Fast Fortunes",
    # "Wise Gang",
    # "The Fun Room",
    # "Ultra Lounge",
    # "Slots Gone Wild",
    # "JJsreelsadventures",
    # "Lucky Luxe",
    # "Mega Ultra Win",
    # "Snarcade",
    # "Lucky Buddy",
    # "Devine Slots",
    # "Grabbin Cash",
    # "BordersWay",
    # "Pandagod",
    # "The Players Lounge",
    # "Litts Dynasty",
]


# Rango de fechas en UTC-6 (formato YYYY-MM-DD)
FECHA_INICIO = "2025-12-29"
FECHA_FIN = "2026-01-04"

# Google Sheets Config
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "../credentials/bamboo-parsec-477706-i5-f024e2770bbe.json"
SPREADSHEET_ID = "1ZdbKvJ92MzmoxSei3H5qxdSIMCiHejfC2quls-mOoUo"
SHEET_NAME = "29.12 - 4.1"

# Lista de plataformas en orden (según tu template)
PLATAFORMAS_ORDEN = [
    "Ultra Panda",
    "Golden Dragon",
    "Vblink",
    "Panda Master",
    "Orion Stars",
    "Ace Book",
    "Golden Treasure",
    "Egames",
    "River Sweeps",
    "Game Vault",
    "Fire Kirin",
    "Juwa"
]

# ============================================================
# FIN DE CONFIGURACIÓN
# ============================================================


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
    data = cambio.json()
    token = data.get("token") or data.get("data", {}).get("token")
    if not token:
        raise ValueError(f"No se pudo obtener token para {nombre_compania}: {data}")
    return token, company_id


def extraer_movimientos_rango(nombre_compania, token, company_id, fecha_inicio, fecha_fin):
    headers = {"Authorization": f"Bearer {token}"}
    movements_url = "https://api.backend.biz/api/movements/paginated"
    page_size = 500

    date_filter = f"{fecha_inicio},{fecha_fin}"
    params = {
        "filters": f'''[{{"type":"date","value":"{date_filter}"}},{{"type":"companyId","value":"{company_id}"}}]''',
        "page": 1,
        "pageSize": page_size,
        "timeZone": "America/Chicago",
    }

    resp = requests.get(movements_url, params=params, headers=headers)
    json_data = resp.json()
    total_docs = json_data.get("data", {}).get("numberTotalDocuments", 0)
    total_pages = (total_docs // page_size) + (1 if total_docs % page_size else 0)
    print(f"[{nombre_compania}] Total movimientos: {total_docs} en {total_pages} páginas.")

    all_documents = []
    for page in range(1, total_pages + 1):
        params["page"] = page
        resp = requests.get(movements_url, params=params, headers=headers)
        documents = resp.json().get("data", {}).get("documents", [])
        all_documents.extend(documents)
        print(f"[{nombre_compania}] Página {page}/{total_pages} procesada: {len(documents)} docs.")

    return all_documents


def extraer_transacciones_rango(nombre_compania, token, company_id, fecha_inicio, fecha_fin):
    headers = {"Authorization": f"Bearer {token}"}
    transactions_url = "https://api.backend.biz/api/transaction/paginated"
    page_size = 500

    date_filter = f"{fecha_inicio},{fecha_fin}"
    params = {
        "filters": f'''[{{"type":"date","value":"{date_filter}"}},{{"type":"companyId","value":"{company_id}"}}]''',
        "page": 1,
        "pageSize": page_size,
        "timeZone": "America/Chicago",
    }

    resp = requests.get(transactions_url, params=params, headers=headers)
    json_data = resp.json()
    total_docs = json_data.get("data", {}).get("totalTransactions", 0)
    
    total_pages = (total_docs // page_size) + (1 if total_docs % page_size else 0)
    print(f"[{nombre_compania}] Total transacciones: {total_docs} en {total_pages} páginas.")

    all_transactions = []
    for page in range(1, total_pages + 1):
        params["page"] = page
        resp = requests.get(transactions_url, params=params, headers=headers)
        transactions = resp.json().get("data", {}).get("transactions", [])
        all_transactions.extend(transactions)
        print(f"[{nombre_compania}] Página {page}/{total_pages} de transacciones procesada: {len(transactions)} docs.")

    return all_transactions


def calcular_total_purchases(transacciones):
    total_purchases = 0
    count_purchases = 0
    
    for trans in transacciones:
        if trans.get("type") == "Purchase" and trans.get("transactionStatus") == "Approved":
            total_purchases += trans.get("amount", 0)
            count_purchases += 1
    
    return total_purchases, count_purchases


def agrupar_por_plataforma(movimientos):
    desglose = defaultdict(lambda: {"IN": 0, "OUT": 0, "count_in": 0, "count_out": 0})
    
    for mov in movimientos:
        if mov.get("status") != "Approved":
            continue
            
        game_name = mov.get("gameName", "Sin Plataforma")
        amount = mov.get("amount", 0)
        mov_type = mov.get("type", "")
        
        if mov_type == "Add Credits":
            desglose[game_name]["IN"] += amount
            desglose[game_name]["count_in"] += 1
        elif mov_type in ["Withdraw Credits", "Remove Credits"]:
            desglose[game_name]["OUT"] += amount
            desglose[game_name]["count_out"] += 1
    
    return desglose


def buscar_fila_compania(worksheet, nombre_compania):
    """
    Busca la fila donde está el nombre de la compañía en la columna B
    Retorna la fila donde está el nombre (ej: 4 para "Todas las marcas")
    """
    try:
        # Buscar en la columna B
        cell = worksheet.find(nombre_compania, in_column=2)
        if cell:
            return cell.row
    except:
        pass
    return None


def escribir_datos_en_tabla(worksheet, fila_nombre, desglose, total_deposits):
    """
    Escribe los datos en la tabla correspondiente usando batch update
    fila_nombre: fila donde está el nombre de la compañía (ej: 4)
    """
    
    # La primera fila de datos está 2 filas después del nombre
    fila_primera_plataforma = fila_nombre + 2
    
    # Preparar todas las actualizaciones en batch
    updates = []
    
    # Total de DEPOSITS en columna C, primera fila de datos
    updates.append({
        'range': f'C{fila_primera_plataforma}',
        'values': [[total_deposits]]
    })
    
    print(f"  💰 Deposits: ${total_deposits:,.2f} en C{fila_primera_plataforma}")
    
    # Preparar datos de cada plataforma
    fila_actual = fila_primera_plataforma
    
    for plataforma in PLATAFORMAS_ORDEN:
        if plataforma in desglose:
            datos = desglose[plataforma]
            # Columna D: IN (Add Credits)
            updates.append({
                'range': f'D{fila_actual}',
                'values': [[datos["IN"]]]
            })
            # Columna E: OUT (Remove/Withdraw Credits)
            updates.append({
                'range': f'E{fila_actual}',
                'values': [[datos["OUT"]]]
            })
            print(f"    Fila {fila_actual} - {plataforma}: IN=${datos['IN']:,.2f} | OUT=${datos['OUT']:,.2f}")
        
        fila_actual += 1
    
    # Ejecutar todas las actualizaciones en batch
    if updates:
        worksheet.batch_update(updates)
        print(f"  ✅ {len(updates)} celdas actualizadas en batch")


def exportar_a_google_sheets(resultados_companias, consolidado):
    """
    Exporta todos los resultados a Google Sheets
    """
    print("\n--- Conectando a Google Sheets ---")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    
    print(f"✅ Conectado a hoja: {SHEET_NAME}")
    
    # Primero escribir consolidado (primera tabla - "Todas las marcas")
    print("\n--- Escribiendo consolidado (Todas las marcas) ---")
    fila_consolidado = buscar_fila_compania(worksheet, "Todas las marcas")
    if fila_consolidado:
        escribir_datos_en_tabla(
            worksheet, 
            fila_consolidado, 
            consolidado["desglose"], 
            consolidado["total_purchases"]
        )
        print(f"  ✅ Consolidado escrito")
    else:
        print("  ⚠️ No se encontró 'Todas las marcas' en columna B")
    
    # Escribir datos de cada compañía
    print("\n--- Escribiendo datos por compañía ---")
    for nombre_compania, datos in resultados_companias.items():
        print(f"\n📊 Procesando {nombre_compania}...")
        fila_nombre = buscar_fila_compania(worksheet, nombre_compania)
        
        if fila_nombre:
            escribir_datos_en_tabla(
                worksheet,
                fila_nombre,
                datos["desglose"],
                datos["total_purchases"]
            )
        else:
            print(f"  ⚠️ No se encontró '{nombre_compania}' en columna B")
    
    print("\n✅ Exportación a Google Sheets completada")


if __name__ == "__main__":
    # Validar fechas
    try:
        datetime.strptime(FECHA_INICIO, "%Y-%m-%d")
        datetime.strptime(FECHA_FIN, "%Y-%m-%d")
    except ValueError:
        print("❌ Formato de fecha inválido. Usa YYYY-MM-DD.")
        exit()
    
    print("="*60)
    print("DESGLOSE DE MOVIMIENTOS Y TRANSACCIONES".center(60))
    print("="*60)
    print(f"\nRango UTC-6: {FECHA_INICIO} al {FECHA_FIN}")
    print(f"Compañías: {', '.join(COMPANIAS_ELEGIDAS)}\n")
    print("="*60)
    
    # Variables para consolidado global y resultados por compañía
    desglose_global = defaultdict(lambda: {"IN": 0, "OUT": 0, "count_in": 0, "count_out": 0})
    total_purchases_global = 0
    count_purchases_global = 0
    resultados_companias = {}
    
    # Procesar cada compañía
    for nombre_elegido in COMPANIAS_ELEGIDAS:
        if nombre_elegido not in companies:
            print(f"⚠️  [{nombre_elegido}] No existe en el diccionario 'companies', se omite.")
            continue
        
        try:
            print(f"\n--- Descargando datos de {nombre_elegido} ---")
            token, company_id = obtener_token_compania(nombre_elegido)
            
            # Extraer movimientos
            movimientos = extraer_movimientos_rango(
                nombre_elegido, token, company_id, FECHA_INICIO, FECHA_FIN
            )
            
            # Extraer transacciones
            transacciones = extraer_transacciones_rango(
                nombre_elegido, token, company_id, FECHA_INICIO, FECHA_FIN
            )
            
            # Calcular total de purchases
            total_purchases, count_purchases = calcular_total_purchases(transacciones)
            
            # Acumular para consolidado global
            total_purchases_global += total_purchases
            count_purchases_global += count_purchases
            
            # Agrupar movimientos por plataforma (solo Approved)
            desglose = agrupar_por_plataforma(movimientos)
            
            # Guardar resultados de esta compañía
            resultados_companias[nombre_elegido] = {
                "desglose": desglose,
                "total_purchases": total_purchases,
                "count_purchases": count_purchases
            }
            
            # Acumular en desglose global
            for platform, datos in desglose.items():
                desglose_global[platform]["IN"] += datos["IN"]
                desglose_global[platform]["OUT"] += datos["OUT"]
                desglose_global[platform]["count_in"] += datos["count_in"]
                desglose_global[platform]["count_out"] += datos["count_out"]
            
            print(f"✅ {nombre_elegido}: ${total_purchases:,.2f} en purchases, {len(desglose)} plataformas")
            
        except Exception as e:
            print(f"❌ [{nombre_elegido}] Error durante el procesamiento: {e}")
    
    # Preparar consolidado
    consolidado = {
        "desglose": desglose_global,
        "total_purchases": total_purchases_global,
        "count_purchases": count_purchases_global
    }
    
    # Exportar todo a Google Sheets
    exportar_a_google_sheets(resultados_companias, consolidado)
    
    print("\n" + "="*60)
    print("✓ Proceso completado.".center(60))
    print("="*60)
