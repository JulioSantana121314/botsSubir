import requests
from datetime import datetime, timedelta
from collections import defaultdict
import gspread
from google.oauth2.service_account import Credentials
from config import companies, SUPERADMIN_USER, SUPERADMIN_PASS


# ============================================================
# CONFIGURACIÓN - EDITA ESTOS VALORES
# ============================================================

# Compañía: Solo Wise Gang
WISE_GANG = "Wise Gang"

# Rango de fechas en UTC-5 (formato YYYY-MM-DD)
FECHA_INICIO = "2025-12-22"
FECHA_FIN = "2025-12-28"

# Google Sheets Config
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
SERVICE_ACCOUNT_FILE = "../credentials/bamboo-parsec-477706-i5-f024e2770bbe.json"
SPREADSHEET_ID = "1VSQxeldFoJOjoaDt1IAI2j59UNSNlFN_fqYaQc-Xf6Q"
SHEET_NAME = "Daily"

# Lista de plataformas en orden
PLATAFORMAS_ORDEN = [
    "Golden Dragon",
    "Egames",
    "Ace Book",
    "Ultra Panda",
    "Vblink",
    "Golden Treasure",
    "Orion Stars",
    "Game Vault",
    "Galaxy World",
    "Juwa",
    "Joker",
    "Winner´s club",
    "Cash Frenzy",
    "King of Pop",
    "Gemini",
    "Loot",
    "Easy Street",
    "Mafia",
    "Lucky Stars",
    "Game Room",
    "Noble",
    "Win Star",
    "Highstakes",
    "Great Balls of Fire",
    "Fish Glory",
    "Plus System",
    "Magic City",
    "Milky Way",
    "Vegas X",
    "River Sweeps",
    "Yolo",
    "Blue Dragon",
    "GoldStar",
    "Legend Fire",
    "River Monster",
    "Mega Spin",
    "Sirius",
    "Moolah",
    "TheKraKen",
    "High Roller",
    "Glamour Spin",
    "Jackpot Frenzy",
    "Fortune2Go",
    "Juwa 2.0",
    "Black Mamba",
    "Apollo",
    "Vegas Roll",
    "Mr. All In One",
    "Cash Machine",
    "Billion Balls",
    "Orion Power",
    "Vegas Luck",
    "Lucky Ox",
    "Orion Strike",
    "Fun Station",
    "Diamond Dragon",
    "Gold Mine",
    "Orca",
    "Fire Kirin",
    "Lucky Paradise",
    "Fortune Nexus",
    "Vegas Sweeps",
    "Big Daddy",
    "Classics 777",
    "Valhalla",
    "GD City 2.0",
    "Majik Bonus",
    "Fire Phoenix",
    "Easy Money",
    "Panda Master",
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


def extraer_movimientos_dia(nombre_compania, token, company_id, fecha_dia):
    """
    Extrae movimientos de un día específico
    fecha_dia: formato YYYY-MM-DD
    """
    headers = {"Authorization": f"Bearer {token}"}
    movements_url = "https://api.backend.biz/api/movements/paginated"
    page_size = 500

    date_filter = f"{fecha_dia},{fecha_dia}"
    params = {
        "filters": f'''[{{"type":"date","value":"{date_filter}"}},{{"type":"companyId","value":"{company_id}"}}]''',
        "page": 1,
        "pageSize": page_size,
        "timeZone": "America/Lima",
    }

    resp = requests.get(movements_url, params=params, headers=headers)
    json_data = resp.json()
    total_docs = json_data.get("data", {}).get("numberTotalDocuments", 0)
    total_pages = (total_docs // page_size) + (1 if total_docs % page_size else 0)

    all_documents = []
    for page in range(1, total_pages + 1):
        params["page"] = page
        resp = requests.get(movements_url, params=params, headers=headers)
        documents = resp.json().get("data", {}).get("documents", [])
        all_documents.extend(documents)

    return all_documents


def agrupar_por_plataforma(movimientos):
    """
    Agrupa movimientos por gameName y calcula IN y OUT
    SOLO considera movimientos con status "Approved"
    """
    desglose = defaultdict(lambda: {"IN": 0, "OUT": 0})
    
    for mov in movimientos:
        # FILTRO: Solo procesar si el status es "Approved"
        if mov.get("status") != "Approved":
            continue
            
        game_name = mov.get("gameName", "Sin Plataforma")
        amount = mov.get("amount", 0)
        mov_type = mov.get("type", "")
        
        if mov_type == "Add Credits":
            desglose[game_name]["IN"] += amount
        elif mov_type in ["Withdraw Credits", "Remove Credits"]:
            desglose[game_name]["OUT"] += amount
    
    return desglose


def buscar_fila_fecha(worksheet, fecha_str):
    """
    Busca la fila donde está la fecha en columna A
    fecha_str: formato "D/M" (ej: "1/12")
    Retorna la fila donde está esa fecha
    """
    try:
        cell = worksheet.find(fecha_str, in_column=1)
        if cell:
            return cell.row
    except:
        pass
    return None


def escribir_tabla_wise_gang(worksheet, fila_fecha, desglose_wise):
    """
    Escribe en la tabla WISE GANG (columnas J:O)
    
    Estructura:
    - J: Platform names (no tocar)
    - K: Add Credits (IN)
    - L: Remove Credits (OUT)
    """
    
    # Buscar la fila donde está "Platform" en columna J después de la fecha
    fila_header = None
    for offset in range(1, 15):  # Buscar hasta 15 filas después de la fecha
        try:
            test_cell = worksheet.cell(fila_fecha + offset, 10).value  # Columna J = 10
            if test_cell == "Platform":
                fila_header = fila_fecha + offset
                break
        except:
            pass
    
    if not fila_header:
        print(f"  ⚠️ No se encontró header 'Platform' en columna J")
        return None
    
    # Preparar actualizaciones en batch
    updates = []
    
    # Los datos empiezan en la fila siguiente al header
    fila_datos_inicio = fila_header + 1
    
    for idx, plataforma in enumerate(PLATAFORMAS_ORDEN):
        fila_actual = fila_datos_inicio + idx
        
        if plataforma in desglose_wise:
            datos = desglose_wise[plataforma]
            # Columna K: IN (Add Credits)
            updates.append({
                'range': f'K{fila_actual}',
                'values': [[datos["IN"]]]
            })
            # Columna L: OUT (Remove Credits)
            updates.append({
                'range': f'L{fila_actual}',
                'values': [[datos["OUT"]]]
            })
        else:
            # Si no hay datos, poner 0
            updates.append({
                'range': f'K{fila_actual}',
                'values': [[0]]
            })
            updates.append({
                'range': f'L{fila_actual}',
                'values': [[0]]
            })
    
    # Ejecutar batch update
    if updates:
        worksheet.batch_update(updates)
        print(f"  ✅ Tabla WISE GANG actualizada en K{fila_datos_inicio}:L{fila_datos_inicio + len(PLATAFORMAS_ORDEN) - 1}")
    
    return fila_header


def generar_rango_fechas(fecha_inicio, fecha_fin):
    """
    Genera lista de fechas entre inicio y fin
    """
    inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d")
    fin = datetime.strptime(fecha_fin, "%Y-%m-%d")
    
    fechas = []
    fecha_actual = inicio
    while fecha_actual <= fin:
        fechas.append(fecha_actual.strftime("%Y-%m-%d"))
        fecha_actual += timedelta(days=1)
    
    return fechas


def formato_fecha_hoja(fecha_str):
    """
    Convierte YYYY-MM-DD a formato D/M
    Ejemplo: "2025-12-01" -> "1/12"
    """
    fecha = datetime.strptime(fecha_str, "%Y-%m-%d")
    return f"{fecha.day}/{fecha.month}"


if __name__ == "__main__":
    print("="*60)
    print("REPORTE DIARIO DE MOVIMIENTOS - WISE GANG".center(60))
    print("="*60)
    print(f"\nRango UTC-5: {FECHA_INICIO} al {FECHA_FIN}\n")
    print("="*60)
    
    # Verificar que Wise Gang existe en companies
    if WISE_GANG not in companies:
        print(f"❌ Error: '{WISE_GANG}' no existe en el diccionario companies")
        exit()
    
    # Conectar a Google Sheets
    print("\n--- Conectando a Google Sheets ---")
    creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    gc = gspread.authorize(creds)
    sh = gc.open_by_key(SPREADSHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    print(f"✅ Conectado a hoja: {SHEET_NAME}")
    
    # Generar lista de fechas
    fechas = generar_rango_fechas(FECHA_INICIO, FECHA_FIN)
    
    # Procesar cada día
    for fecha_dia in fechas:
        fecha_formato_hoja = formato_fecha_hoja(fecha_dia)
        print(f"\n{'='*60}")
        print(f"Procesando: {fecha_formato_hoja} ({fecha_dia})".center(60))
        print(f"{'='*60}")
        
        # Buscar la fila de esta fecha en la hoja
        fila_fecha = buscar_fila_fecha(worksheet, fecha_formato_hoja)
        
        if not fila_fecha:
            print(f"⚠️  No se encontró la fecha {fecha_formato_hoja} en columna A")
            continue
        
        print(f"📍 Fecha encontrada en fila {fila_fecha}")
        
        # Procesar Wise Gang
        print(f"\n📊 Procesando Wise Gang...")
        try:
            token, company_id = obtener_token_compania(WISE_GANG)
            movimientos = extraer_movimientos_dia(WISE_GANG, token, company_id, fecha_dia)
            
            if movimientos:
                desglose_wise = agrupar_por_plataforma(movimientos)
                print(f"  ✓ Wise Gang: {len(movimientos)} movimientos")
                
                # Escribir en la tabla WISE GANG
                print(f"\n📝 Escribiendo en Google Sheets...")
                escribir_tabla_wise_gang(worksheet, fila_fecha, desglose_wise)
            else:
                print(f"  - Wise Gang: sin movimientos")
                # Escribir ceros si no hay movimientos
                desglose_wise = defaultdict(lambda: {"IN": 0, "OUT": 0})
                escribir_tabla_wise_gang(worksheet, fila_fecha, desglose_wise)
                
        except Exception as e:
            print(f"  ❌ Wise Gang: {e}")
        
        print(f"✅ Día {fecha_formato_hoja} completado")
    
    print("\n" + "="*60)
    print("✓ Proceso completado para todos los días".center(60))
    print("="*60)
